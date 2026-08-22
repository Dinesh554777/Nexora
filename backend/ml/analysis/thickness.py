"""Phase 10: Medial meniscus thickness measurement.

Methodology
-----------
Input
    mask        : binary numpy array, shape (R, C, Z), dtype uint8 or bool.
                  Value 1 (or True) = meniscus foreground.
    spacing_mm  : optional (row_mm, col_mm, slice_mm) from the NIfTI header
                  (``result["spacing"]`` from Phase 9).  Pass None when the
                  header is absent; results are then reported in voxels.
    slice_axis  : axis along which the volume was sliced (default 2, i.e. Z).

Anatomical position definition
    Anterior / middle / posterior are defined relative to the mask's own
    occupied extent along ``slice_axis``; no external atlas or landmark is
    used.  The occupied Z range [z_min, z_max] is divided into three equal
    thirds by the indices of the **active slices** (slices that contain at
    least one foreground voxel):

        anterior  = first  ⌊N/3⌋  active slices
        middle    = next   ⌊N/3⌋  active slices
        posterior = remaining       active slices

    This guarantees reproducibility: the same mask always produces the same
    partition regardless of the absolute voxel coordinates.

Thickness measurement per region
    For each active slice in a region, the mask is projected along the row
    axis (axis perpendicular to ``slice_axis`` in the R-C plane that spans
    the radial extent of the meniscus cross-section).  For each column the
    maximum contiguous run of foreground pixels is measured; the largest
    such run across all columns gives the local thickness for that slice.
    The region's reported thickness is the **median** of per-slice values,
    which is robust to irregular or partially-visible slices.

    Formally, for a single slice S (shape R×C):
        t(col) = max contiguous-run-length of foreground pixels in S[:, col]
        t_slice = median( t(col) for col where t(col) > 0 )
        t_region = median( t_slice  for slices in region )

    Physical conversion:
        t_mm = t_voxel × row_spacing_mm

    If ``spacing_mm`` is None the value is reported in **voxels** and the
    unit string is set to ``"voxels"``; otherwise it is ``"mm"``.

Edge-case handling
    empty mask              → all three values None, status "empty_mask"
    fewer than 3 active slices → affected regions return None with
                                  status "insufficient_slices"
    a region has only blank columns in all its slices → None with
                                  status "no_foreground_in_region"
    invalid geometry (ndim, shape) → ValueError raised immediately
    non-finite spacing      → treated as missing; unit falls back to voxels

No claim of clinical validity is made.  Results are for research /
algorithmic-development purposes only.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------

# Each region value is a dict matching the requested schema:
#   {"value": float | None, "unit": str, "method": str, "status": str}
ThicknessResult = dict[str, dict[str, Any]]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_REGION_NAMES = ("anterior", "middle", "posterior")

_METHOD_TEMPLATE = (
    "Mask extent along slice_axis partitioned into thirds by active-slice "
    "index; per-slice thickness = median of maximum contiguous foreground "
    "run-lengths projected along the row axis; region thickness = median of "
    "per-slice values"
)


def _validate_mask(mask: np.ndarray, slice_axis: int) -> None:
    """Raise ValueError for obviously invalid inputs."""
    if not isinstance(mask, np.ndarray):
        raise ValueError(
            f"mask must be a numpy ndarray, got {type(mask).__name__}"
        )
    if mask.ndim != 3:
        raise ValueError(
            f"mask must be 3-dimensional, got ndim={mask.ndim}"
        )
    if slice_axis not in (0, 1, 2):
        raise ValueError(
            f"slice_axis must be 0, 1 or 2, got {slice_axis}"
        )
    if mask.shape[slice_axis] == 0:
        raise ValueError(
            f"mask has zero size along slice_axis={slice_axis}"
        )


def _parse_spacing(
    spacing_mm: tuple[float, float, float] | None, slice_axis: int
) -> tuple[float | None, str]:
    """Return (row_spacing_for_axis0, unit_string) from the raw spacing tuple.

    The mask's axis-0 is always the row axis in the original (R, C, Z)
    convention.  After np.moveaxis(mask, slice_axis, 2) the row axis of the
    re-arranged array corresponds to spacing_mm[0] (row_mm).

    Returns (None, "voxels") whenever spacing is missing or invalid.
    """
    if spacing_mm is None:
        return None, "voxels"
    try:
        sp = tuple(float(v) for v in spacing_mm[:3])
    except (TypeError, ValueError):
        return None, "voxels"
    if not all(math.isfinite(v) and v > 0.0 for v in sp):
        return None, "voxels"
    # The projection is along axis-0 of the (R, C, *active_slice*) cube
    # produced after moving slice_axis to position 2.  Axis-0 of that cube
    # maps to axis-0 of the original mask, whose spacing is spacing_mm[0].
    row_mm = sp[0]
    return row_mm, "mm"


def _max_run_length_1d(col: np.ndarray) -> int:
    """Return the length of the longest contiguous run of True/1 values."""
    # Fast path – entirely empty or full
    if not col.any():
        return 0
    if col.all():
        return len(col)
    # General: find transitions
    padded = np.concatenate(([False], col.astype(bool), [False]))
    diffs = np.diff(padded.astype(np.int8))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]
    return int((ends - starts).max())


def _slice_thickness_voxels(sl: np.ndarray) -> float | None:
    """Median of per-column max-run-lengths for a single 2-D slice (R×C).

    Returns None if no foreground column exists.
    """
    # sl has shape (R, C)
    runs = []
    for c in range(sl.shape[1]):
        r = _max_run_length_1d(sl[:, c])
        if r > 0:
            runs.append(r)
    if not runs:
        return None
    return float(np.median(runs))


def _region_thickness_voxels(slices: list[np.ndarray]) -> tuple[float | None, str]:
    """Median of per-slice thickness values across a region.

    Returns (value, status).
      value  : float (voxels) or None
      status : "ok" | "no_foreground_in_region"
    """
    per_slice = []
    for sl in slices:
        t = _slice_thickness_voxels(sl)
        if t is not None:
            per_slice.append(t)
    if not per_slice:
        return None, "no_foreground_in_region"
    return float(np.median(per_slice)), "ok"


def _partition_active_slices(
    active_indices: list[int],
) -> tuple[list[int], list[int], list[int]]:
    """Split active slice indices into (anterior, middle, posterior) thirds.

    Each third receives at least one slice when len >= 3.
    With fewer than 3 active slices the shorter groups may be empty ([]). 
    """
    n = len(active_indices)
    third = n // 3
    anterior = active_indices[:third]
    middle = active_indices[third : 2 * third]
    posterior = active_indices[2 * third :]
    return anterior, middle, posterior


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _empty_result(status: str, unit: str) -> ThicknessResult:
    """Build a result dict where all three regions have None value."""
    return {
        name: {"value": None, "unit": unit, "method": _METHOD_TEMPLATE,
               "status": status}
        for name in _REGION_NAMES
    }


def measure_thickness(
    mask: np.ndarray,
    spacing_mm: tuple[float, float, float] | None = None,
    slice_axis: int = 2,
) -> ThicknessResult:
    """Measure medial meniscus thickness at anterior, middle, and posterior.

    Parameters
    ----------
    mask : np.ndarray
        3-D binary volume, shape (R, C, Z) when ``slice_axis=2``.
        Non-zero voxels are treated as foreground (meniscus).
    spacing_mm : tuple[float, float, float] | None
        Physical voxel size ``(row_mm, col_mm, slice_mm)`` from the NIfTI
        header (``result["spacing"]`` from Phase 9).  Pass ``None`` when
        the header is absent; results are then in voxels.
    slice_axis : int
        Axis that corresponds to individual MRI slices (default 2).

    Returns
    -------
    dict with keys "anterior", "middle", "posterior", each mapping to::

        {
            "value"  : float | None,
            "unit"   : "mm" | "voxels",
            "method" : str,
            "status" : "ok"
                     | "empty_mask"
                     | "insufficient_slices"
                     | "no_foreground_in_region"
        }

    Raises
    ------
    ValueError
        On obviously invalid inputs (wrong ndim, bad slice_axis, zero-size).
    """
    _validate_mask(mask, slice_axis)
    row_mm, unit = _parse_spacing(spacing_mm, slice_axis)

    # Move slice axis to the last position so we always index as [r, c, z]
    arr = np.moveaxis(mask, slice_axis, 2).astype(bool)   # (R, C, Z')

    # --- find slices that contain any foreground ---
    any_fg = arr.any(axis=(0, 1))   # shape (Z',)
    active = [int(z) for z in np.where(any_fg)[0]]

    if len(active) == 0:
        return _empty_result("empty_mask", unit)

    if len(active) < 3:
        # Cannot form three distinct regions; report all as insufficient
        result: ThicknessResult = {}
        for name in _REGION_NAMES:
            result[name] = {
                "value": None,
                "unit": unit,
                "method": _METHOD_TEMPLATE,
                "status": "insufficient_slices",
            }
        return result

    ant_idx, mid_idx, post_idx = _partition_active_slices(active)

    result = {}
    for name, indices in zip(
        _REGION_NAMES, (ant_idx, mid_idx, post_idx)
    ):
        if not indices:
            result[name] = {
                "value": None,
                "unit": unit,
                "method": _METHOD_TEMPLATE,
                "status": "insufficient_slices",
            }
            continue

        slices_2d = [arr[:, :, z] for z in indices]
        t_vox, status = _region_thickness_voxels(slices_2d)

        if t_vox is None or status != "ok":
            result[name] = {
                "value": None,
                "unit": unit,
                "method": _METHOD_TEMPLATE,
                "status": status,
            }
        else:
            value = t_vox * row_mm if row_mm is not None else t_vox
            result[name] = {
                "value": round(value, 4),
                "unit": unit,
                "method": _METHOD_TEMPLATE,
                "status": "ok",
            }

    return result


def measure_from_inference_result(
    inference_result: dict,
    foreground_labels: tuple[int, ...] | None = None,
    slice_axis: int = 2,
) -> ThicknessResult:
    """Convenience wrapper around :func:`measure_thickness` for Phase 9 output.

    Parameters
    ----------
    inference_result : dict
        Dict returned by ``MeniscusPredictor.predict_volume()``.  Expected
        keys: ``"mask"`` (uint8 ndarray), ``"spacing"`` (tuple or None).
    foreground_labels : tuple[int, ...] | None
        If the mask is a **label map** (not binary), pass the integer label
        values that correspond to the medial meniscus, e.g. ``(7,)``.
        When ``None`` (default) the mask is treated as already binary.
    slice_axis : int
        Axis corresponding to MRI slices (default 2, matching Phase 9).

    Returns
    -------
    ThicknessResult  (same schema as :func:`measure_thickness`)
    """
    if "mask" not in inference_result:
        raise ValueError(
            "'mask' key not found in inference_result; "
            "pass a dict from MeniscusPredictor.predict_volume()"
        )

    raw_mask: np.ndarray = np.asarray(inference_result["mask"])
    spacing = inference_result.get("spacing")  # may be None

    if foreground_labels is not None:
        binary_mask = np.isin(raw_mask, foreground_labels).astype(np.uint8)
    else:
        binary_mask = (raw_mask > 0).astype(np.uint8)

    return measure_thickness(binary_mask, spacing_mm=spacing,
                             slice_axis=slice_axis)
