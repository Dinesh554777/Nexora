"""Phase 12: ML-to-backend integration interface.

Single entry point for the backend team.  No FastAPI, no UI, no database.

Usage
-----
    from ml.pipeline import analyze_meniscus

    result = analyze_meniscus("path/to/knee.nii.gz")

Result schema
-------------
{
    "model_version": str,
    "segmentation": {
        "mask_path":  str | None,        # absolute path to saved NIfTI mask
        "voxel_count": int,              # total foreground voxels
        "slices_with_mask": int,
        "quality": {
            "threshold":   float,
            "image_shape": [int, int, int],
            "mask_shape":  [int, int, int],
        }
    },
    "measurements": {
        "anterior":  {"value": float|None, "unit": str, "method": str, "status": str},
        "middle":    {...},
        "posterior": {...}
    },
    "visualization": {
        "overlay_path": str              # absolute path to saved PNG
    },
    "metadata": {
        "subject_id":  str,
        "source_image": str,             # absolute input path
        "spacing": {                     # None when header is absent/invalid
            "row_mm":   float,
            "col_mm":   float,
            "slice_mm": float
        } | None
    }
}

Error contract
--------------
* FileNotFoundError   – image_path does not exist, or checkpoint missing
* ValueError          – image is not a valid NIfTI / wrong dimensionality
* RuntimeError        – unexpected failure in segmentation, measurement, or
                        visualization; original exception is chained

All other exceptions propagate unchanged so callers can inspect the cause.

Model loading
-------------
MeniscusPredictor is stateful (holds the loaded model).  To avoid
reloading the model on every call, use the module-level helper::

    from ml.pipeline import get_predictor
    predictor = get_predictor()              # loaded once, cached
    result = analyze_meniscus(..., predictor=predictor)

Thread safety: a single predictor instance must not be called from
multiple threads simultaneously (PyTorch model is not thread-safe by
default).  Instantiate one predictor per thread if concurrency is needed.
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Path bootstrap — makes the package importable regardless of cwd
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402

from ml.analysis.thickness import measure_thickness  # noqa: E402
from ml.inference.predict import (  # noqa: E402
    DEFAULT_CHECKPOINT,
    DEFAULT_THRESHOLD,
    MeniscusPredictor,
    save_mask,
)
from ml.visualization.overlay import (  # noqa: E402
    build_json_result,
    draw_measurement_overlay,
)

# ---------------------------------------------------------------------------
# Default output locations
# ---------------------------------------------------------------------------
_DEFAULT_OUT_DIR = os.path.join(_ROOT, "outputs", "pipeline")


# ---------------------------------------------------------------------------
# Module-level predictor cache
# ---------------------------------------------------------------------------
_predictor_cache: dict[str, MeniscusPredictor] = {}


def get_predictor(
    checkpoint_path: str = DEFAULT_CHECKPOINT,
    device: str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> MeniscusPredictor:
    """Return a cached MeniscusPredictor for the given checkpoint.

    The first call for a given checkpoint path loads the model from disk
    and caches it.  Subsequent calls with the same path return the cached
    instance immediately, avoiding repeated file-I/O and GPU memory
    allocation.

    Parameters
    ----------
    checkpoint_path : str
        Path to ``best_model.pth`` (or any compatible checkpoint).
    device : str | None
        ``"cpu"``, ``"cuda"``, or ``None`` (auto-detect).
    threshold : float
        Binarisation threshold applied to sigmoid outputs (default 0.5).
    """
    key = os.path.abspath(checkpoint_path)
    if key not in _predictor_cache:
        _predictor_cache[key] = MeniscusPredictor(
            checkpoint_path=checkpoint_path,
            device=device,
            threshold=threshold,
        )
    return _predictor_cache[key]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_mri_volume(image_path: str) -> np.ndarray:
    """Load a NIfTI file and return a float32 (R, C, Z) ndarray."""
    nii = nib.load(image_path)
    data = np.squeeze(nii.get_fdata(dtype=np.float32))
    if data.ndim == 2:
        data = data[:, :, np.newaxis]
    if data.ndim != 3:
        raise ValueError(
            f"Expected a 2-D or 3-D NIfTI volume, got ndim={data.ndim}: {image_path}"
        )
    return data


def _spacing_to_dict(
    spacing: tuple[float, float, float] | None,
) -> dict[str, float] | None:
    """Convert a spacing tuple to the JSON-serialisable dict, or None."""
    if spacing is None:
        return None
    try:
        sp = tuple(float(v) for v in spacing[:3])
        if all(math.isfinite(v) and v > 0 for v in sp):
            return {"row_mm": sp[0], "col_mm": sp[1], "slice_mm": sp[2]}
    except (TypeError, ValueError):
        pass
    return None


def _slices_with_mask(mask: np.ndarray) -> int:
    """Count Z-slices (axis 2) that contain at least one foreground voxel."""
    return int((mask.sum(axis=(0, 1)) > 0).sum())


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyze_meniscus(
    image_path: str,
    *,
    checkpoint_path: str = DEFAULT_CHECKPOINT,
    out_dir: str = _DEFAULT_OUT_DIR,
    save_mask_nifti: bool = True,
    device: str | None = None,
    threshold: float = DEFAULT_THRESHOLD,
    batch_size: int = 8,
    min_area: int = 25,
    slice_axis: int = 2,
    predictor: MeniscusPredictor | None = None,
) -> dict[str, Any]:
    """Run the full medial-meniscus analysis pipeline on one MRI volume.

    Steps performed (in order):
      1. Validate inputs.
      2. Run Phase 9 segmentation (MeniscusPredictor).
      3. Optionally save the binary mask as a NIfTI file.
      4. Run Phase 10 thickness measurement (anterior / middle / posterior).
      5. Run Phase 11 visualization (annotated overlay PNG).
      6. Return a structured result dict.

    Parameters
    ----------
    image_path : str
        Absolute or relative path to a ``.nii`` / ``.nii.gz`` MRI file.
    checkpoint_path : str
        Path to the trained model checkpoint (``best_model.pth``).
    out_dir : str
        Directory where outputs (mask NIfTI, overlay PNG) are written.
        Created automatically if it does not exist.
    save_mask_nifti : bool
        If True (default), write the binary predicted mask to
        ``<out_dir>/<subject_id>_pred_mask.nii.gz``.
    device : str | None
        ``"cpu"``, ``"cuda"``, or ``None`` (auto-detect, default).
    threshold : float
        Sigmoid binarisation threshold (default 0.5).
    batch_size : int
        Slice batch size fed to the U-Net (default 8).
    min_area : int
        Post-processing: discard connected components below this area in
        model-resolution pixels (default 25).
    slice_axis : int
        Axis along which the volume was sliced (default 2).
    predictor : MeniscusPredictor | None
        Pre-loaded predictor instance.  When None (default), the module-
        level cache is used so the model is only loaded once per process.

    Returns
    -------
    dict  matching the schema described in the module docstring.

    Raises
    ------
    FileNotFoundError
        ``image_path`` does not exist, or ``checkpoint_path`` not found.
    ValueError
        Image is not a valid NIfTI, wrong dimensionality, or the
        checkpoint is missing required keys.
    RuntimeError
        Any unexpected failure in segmentation, measurement, or
        visualization; the original exception is always chained.
    """
    # ------------------------------------------------------------------
    # 1. Input validation
    # ------------------------------------------------------------------
    image_path = os.path.abspath(image_path)
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"image not found: {image_path}")
    low = image_path.lower()
    if not (low.endswith(".nii") or low.endswith(".nii.gz")):
        raise ValueError(
            f"image_path must point to a .nii or .nii.gz file, got: {image_path}"
        )

    os.makedirs(out_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 2. Segmentation (Phase 9)
    # ------------------------------------------------------------------
    if predictor is None:
        predictor = get_predictor(
            checkpoint_path=checkpoint_path,
            device=device,
            threshold=threshold,
        )

    try:
        seg = predictor.predict_volume(
            image_path, batch_size=batch_size, min_area=min_area
        )
    except (FileNotFoundError, ValueError):
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Segmentation failed for {image_path!r}: {exc}"
        ) from exc

    mask: np.ndarray                              = seg["mask"]        # (R,C,Z) uint8
    spacing: tuple[float, float, float] | None   = seg["spacing"]
    subject_id: str                               = seg["subject_id"]
    model_version: str                            = seg["model_version"]

    # ------------------------------------------------------------------
    # 3. Save mask NIfTI (optional)
    # ------------------------------------------------------------------
    mask_path: str | None = None
    if save_mask_nifti:
        mask_path = os.path.join(out_dir, f"{subject_id}_pred_mask.nii.gz")
        try:
            save_mask(seg, mask_path, source_nifti=image_path)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to save mask NIfTI to {mask_path!r}: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # 4. Thickness measurement (Phase 10)
    # ------------------------------------------------------------------
    try:
        thickness = measure_thickness(mask, spacing_mm=spacing,
                                      slice_axis=slice_axis)
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Thickness measurement failed for {image_path!r}: {exc}"
        ) from exc

    # ------------------------------------------------------------------
    # 5. Visualization (Phase 11)
    # ------------------------------------------------------------------
    overlay_png = os.path.join(out_dir, f"{subject_id}_overlay.png")
    try:
        volume = _load_mri_volume(image_path)
        draw_measurement_overlay(
            volume        = volume,
            mask          = mask,
            thickness     = thickness,
            spacing_mm    = spacing,
            out_png       = overlay_png,
            slice_axis    = slice_axis,
            model_version = model_version,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Visualization failed for {image_path!r}: {exc}"
        ) from exc

    # ------------------------------------------------------------------
    # 6. Build and return the result dict
    # ------------------------------------------------------------------
    return {
        "model_version": model_version,
        "segmentation": {
            "mask_path":        mask_path,
            "voxel_count":      int(mask.sum()),
            "slices_with_mask": _slices_with_mask(mask),
            "quality": {
                "threshold":   float(seg["threshold"]),
                "image_shape": list(seg["image_shape"]),
                "mask_shape":  list(seg["mask_shape"]),
            },
        },
        "measurements": dict(thickness),
        "visualization": {
            "overlay_path": os.path.abspath(overlay_png),
        },
        "metadata": {
            "subject_id":   subject_id,
            "source_image": image_path,
            "spacing":      _spacing_to_dict(spacing),
        },
    }


# ---------------------------------------------------------------------------
# Backend-facing public adapter
# ---------------------------------------------------------------------------

def analyze_meniscus_for_backend(
    image_path: str,
    *,
    out_dir: str = _DEFAULT_OUT_DIR,
    checkpoint_path: str = DEFAULT_CHECKPOINT,
    device: str | None = None,
    predictor: MeniscusPredictor | None = None,
) -> dict[str, Any]:
    """Backend integration entry point — wraps :func:`analyze_meniscus`.

    Returns a JSON-serialisable dict whose shape exactly matches the
    contract agreed with the FastAPI team:

    .. code-block:: json

        {
            "status": "success",
            "model_version": "unet2d-base16-depth4-epoch10",
            "measurements": {
                "anterior":  {"value": 1.44, "unit": "mm"},
                "middle":    {"value": 2.70, "unit": "mm"},
                "posterior": {"value": 2.16, "unit": "mm"}
            },
            "segmentation": {
                "mask_path": "/abs/path/to/subject_pred_mask.nii.gz"
            },
            "visualization": {
                "overlay_path": "/abs/path/to/subject_overlay.png"
            }
        }

    On any error the dict has ``"status": "error"`` and an ``"error"``
    key with a human-readable message; no exception is raised so the
    FastAPI layer can return a structured HTTP error without a try/except.

    Unit policy
    -----------
    ``"unit"`` is ``"mm"`` when physical spacing is available from the
    NIfTI header, and ``"voxels"`` otherwise.  The value is ``null``
    when the measurement could not be computed (empty mask, too few
    slices, etc.) and ``status`` is set to ``"partial"`` in that case.

    Parameters
    ----------
    image_path : str
        Path to a ``.nii`` / ``.nii.gz`` MRI file.
    out_dir : str
        Directory for output files (mask NIfTI, overlay PNG).
    checkpoint_path : str
        Path to ``best_model.pth``.
    device : str | None
        ``"cpu"``, ``"cuda"``, or ``None`` (auto-detect).
    predictor : MeniscusPredictor | None
        Pre-loaded predictor instance for model-caching across requests.
    """
    try:
        raw = analyze_meniscus(
            image_path,
            out_dir=out_dir,
            checkpoint_path=checkpoint_path,
            device=device,
            predictor=predictor,
        )
    except FileNotFoundError as exc:
        return {"status": "error", "error": f"file not found: {exc}"}
    except ValueError as exc:
        return {"status": "error", "error": f"invalid input: {exc}"}
    except RuntimeError as exc:
        return {"status": "error", "error": f"pipeline error: {exc}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"unexpected error: {exc}"}

    # --- shape measurements into the exact schema the backend expects ---
    measurements: dict[str, Any] = {}
    any_null = False
    for region in ("anterior", "middle", "posterior"):
        entry = raw["measurements"].get(region, {})
        value = entry.get("value")      # float | None
        unit  = entry.get("unit", "voxels")
        measurements[region] = {"value": value, "unit": unit}
        if value is None:
            any_null = True

    status = "partial" if any_null else "success"

    return {
        "status":        status,
        "model_version": raw["model_version"],
        "measurements":  measurements,
        "segmentation": {
            "mask_path": raw["segmentation"]["mask_path"],
        },
        "visualization": {
            "overlay_path": raw["visualization"]["overlay_path"],
        },
    }
