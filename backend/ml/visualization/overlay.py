"""Phase 11: Explainable meniscus measurement visualization.

Produces a multi-panel PNG overlay showing:
  1. Original MRI slice (greyscale)
  2. Segmentation mask overlaid on MRI (semi-transparent green)
  3. Anterior measurement line + value
  4. Middle  measurement line + value
  5. Posterior measurement line + value
  6. Three-region summary panel (anterior / middle / posterior side-by-side)

Measurement lines are geometrically derived from the actual binary mask —
not hardcoded.  The representative slice for each region is the active slice
whose per-slice thickness is closest to the region's reported median value.
The measurement line is drawn at the column whose max-contiguous-run-length
is closest to that slice's per-slice median.

Physical spacing is applied when available; otherwise voxel units are used.

No claim of clinical validity is made.

Public API
----------
    draw_measurement_overlay(
        volume        : np.ndarray,          # (R, C, Z) float32, MRI
        mask          : np.ndarray,          # (R, C, Z) uint8 {0,1}
        thickness     : ThicknessResult,     # from measure_thickness()
        spacing_mm    : tuple | None,
        out_png       : str,                 # path to write PNG
        slice_axis    : int = 2,
        model_version : str = "",
    ) -> OverlayMeta                         # geometry record

    build_json_result(
        thickness     : ThicknessResult,
        overlay_path  : str,
        model_version : str,
        spacing_mm    : tuple | None,
    ) -> dict                                # machine-readable JSON dict
"""

from __future__ import annotations

import math
import os
import sys
from typing import Any

import matplotlib  # noqa: E402  (backend must be set before pyplot import)

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# ---------------------------------------------------------------------------
# Re-use the internal helpers from the measurement module directly so the
# line geometry is guaranteed to be consistent with what was measured.
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ml.analysis.thickness import (  # noqa: E402
    ThicknessResult,
    _max_run_length_1d,
    _partition_active_slices,
    _parse_spacing,
    _slice_thickness_voxels,
)

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

# Per-region colours  (R, G, B)  in [0, 1]
_REGION_COLOUR = {
    "anterior":  (0.20, 0.60, 1.00),   # sky-blue
    "middle":    (1.00, 0.75, 0.10),   # amber
    "posterior": (0.90, 0.30, 0.30),   # coral-red
}
_MASK_COLOUR   = (0.10, 0.90, 0.30)   # bright green  (segmentation overlay)
_LINE_LW       = 2.0                  # measurement line linewidth (points)
_TICK_LW       = 1.5
_TICK_HALF     = 3                    # half-width of cap ticks in pixels
_TEXT_FONTSIZE  = 8
_TITLE_FONTSIZE = 9
_DPI            = 150

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def _run_extents_1d(col: np.ndarray) -> tuple[int, int]:
    """Return (row_start, row_end_exclusive) of the longest contiguous run."""
    col = col.astype(bool)
    if not col.any():
        return 0, 0
    padded = np.concatenate(([False], col, [False]))
    diffs  = padded[1:].astype(np.int8) - padded[:-1].astype(np.int8)
    starts = np.where(diffs ==  1)[0]
    ends   = np.where(diffs == -1)[0]
    lengths = ends - starts
    best   = int(np.argmax(lengths))
    return int(starts[best]), int(ends[best])


def _slice_geometry(sl: np.ndarray) -> dict | None:
    """Derive measurement line geometry from a single 2-D mask slice (R×C).

    Returns
    -------
    dict with keys:
        col        : representative column index (int)
        row_start  : first foreground row (inclusive, int)
        row_end    : last foreground row  (inclusive, int)
        thickness  : voxel run-length at the representative column (int)
    or None if the slice is empty.
    """
    R, C = sl.shape
    run_lengths: list[int]    = []
    extents: list[tuple[int,int]] = []

    for c in range(C):
        rs, re = _run_extents_1d(sl[:, c])
        rl = re - rs
        run_lengths.append(rl)
        extents.append((rs, re))

    active = [c for c, r in enumerate(run_lengths) if r > 0]
    if not active:
        return None

    median_t = float(np.median([run_lengths[c] for c in active]))

    # representative column: run-length closest to the per-slice median
    rep_col = min(active, key=lambda c: abs(run_lengths[c] - median_t))
    rs, re = extents[rep_col]

    return {
        "col":       rep_col,
        "row_start": rs,
        "row_end":   re - 1,   # inclusive
        "thickness": run_lengths[rep_col],
    }


def _representative_slice(
    arr: np.ndarray,
    region_indices: list[int],
    region_thickness_vox: float,
) -> tuple[int, dict]:
    """Return (slice_index, geometry) for the slice closest to the median.

    Parameters
    ----------
    arr             : (R, C, Z') bool array (slice axis already at 2)
    region_indices  : list of Z' indices that belong to this region
    region_thickness_vox : the reported region thickness in voxels
    """
    best_idx  = region_indices[len(region_indices) // 2]   # fallback: centre
    best_geom: dict | None = None
    best_delta = math.inf

    for z in region_indices:
        sl    = arr[:, :, z]
        t_vox = _slice_thickness_voxels(sl)
        if t_vox is None:
            continue
        delta = abs(t_vox - region_thickness_vox)
        if delta < best_delta:
            best_delta = delta
            best_idx   = z
            best_geom  = _slice_geometry(sl)

    if best_geom is None:
        # fall back to centre slice geometry
        best_geom = _slice_geometry(arr[:, :, best_idx])

    return best_idx, best_geom or {}


# ---------------------------------------------------------------------------
# Public geometry record
# ---------------------------------------------------------------------------

class OverlayMeta:
    """Geometry of the measurement lines that were drawn.

    Attributes
    ----------
    regions : dict[str, dict]
        Per-region record with keys:
          slice_index, col, row_start, row_end,
          thickness_vox, thickness_value, unit
    """

    def __init__(self, regions: dict[str, dict]) -> None:
        self.regions = regions

    def as_dict(self) -> dict:
        return {"measurement_lines": self.regions}


# ---------------------------------------------------------------------------
# Core overlay rendering
# ---------------------------------------------------------------------------

def _normalise_volume(volume: np.ndarray) -> np.ndarray:
    """Return float32 array in [0, 1]."""
    v = volume.astype(np.float32)
    lo, hi = np.percentile(v[np.isfinite(v)], [1, 99])
    if hi > lo:
        v = np.clip((v - lo) / (hi - lo), 0.0, 1.0)
    else:
        v = np.zeros_like(v)
    return v


def _build_rgb_slice(mri_2d: np.ndarray) -> np.ndarray:
    """Convert a normalised greyscale slice to an (R, C, 3) uint8 RGB array."""
    g = np.clip(mri_2d, 0.0, 1.0)
    rgb = (np.stack([g, g, g], axis=-1) * 255).astype(np.uint8)
    return rgb


def _overlay_mask(rgb: np.ndarray, mask_2d: np.ndarray,
                  colour: tuple, alpha: float = 0.40) -> np.ndarray:
    """Blend mask onto an RGB uint8 image."""
    out = rgb.copy().astype(np.float32)
    fg  = mask_2d.astype(bool)
    c   = np.array(colour, dtype=np.float32) * 255.0
    out[fg] = (1.0 - alpha) * out[fg] + alpha * c
    return np.clip(out, 0, 255).astype(np.uint8)


def _draw_measurement_line(
    ax: plt.Axes,
    col: int,
    row_start: int,
    row_end: int,
    colour: tuple,
    label: str,
) -> None:
    """Draw a vertical measurement bar with end-caps and a text label.

    Matplotlib image convention: x=col, y=row (origin top-left).
    """
    x = col
    y0, y1 = row_start, row_end

    # Main line
    ax.plot([x, x], [y0, y1],
            color=colour, linewidth=_LINE_LW, solid_capstyle="butt", zorder=4)

    # End-caps (horizontal ticks)
    for y in (y0, y1):
        ax.plot([x - _TICK_HALF, x + _TICK_HALF], [y, y],
                color=colour, linewidth=_TICK_LW, zorder=4)

    # Text annotation: placed to the right of the line, mid-height
    y_mid = (y0 + y1) / 2.0
    ax.text(x + _TICK_HALF + 2, y_mid, label,
            color=colour, fontsize=_TEXT_FONTSIZE,
            va="center", ha="left", zorder=5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="black",
                      alpha=0.55, edgecolor="none"))


def _format_value(value: float | None, unit: str) -> str:
    if value is None:
        return "N/A"
    if unit == "mm":
        return f"{value:.2f} mm"
    return f"{value:.1f} vox"


# ---------------------------------------------------------------------------
# Single-region panel
# ---------------------------------------------------------------------------

def _render_region_panel(
    ax: plt.Axes,
    mri_2d: np.ndarray,
    mask_2d: np.ndarray,
    geom: dict,
    region_name: str,
    value: float | None,
    unit: str,
    status: str,
) -> None:
    """Render one region panel into ax."""
    colour = _REGION_COLOUR[region_name]

    # Background: MRI + mask overlay
    rgb = _build_rgb_slice(mri_2d)
    rgb = _overlay_mask(rgb, mask_2d, _MASK_COLOUR, alpha=0.35)
    ax.imshow(rgb, origin="upper", interpolation="nearest", aspect="equal")

    # Measurement line (only when geometry is available and status is ok)
    if status == "ok" and geom:
        _draw_measurement_line(
            ax,
            col=geom["col"],
            row_start=geom["row_start"],
            row_end=geom["row_end"],
            colour=colour,
            label=_format_value(value, unit),
        )

    title = f"{region_name.capitalize()}  {_format_value(value, unit)}"
    if status != "ok":
        title += f"\n({status})"
    ax.set_title(title, fontsize=_TITLE_FONTSIZE, color="white",
                 pad=3,
                 bbox=dict(facecolor=colour, alpha=0.75, edgecolor="none",
                           boxstyle="round,pad=0.25"))
    ax.axis("off")


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def draw_measurement_overlay(
    volume: np.ndarray,
    mask: np.ndarray,
    thickness: ThicknessResult,
    spacing_mm: tuple[float, float, float] | None,
    out_png: str,
    slice_axis: int = 2,
    model_version: str = "",
) -> OverlayMeta:
    """Generate and save the annotated measurement overlay PNG.

    Parameters
    ----------
    volume        : (R, C, Z) float32 MRI intensity volume.
    mask          : (R, C, Z) uint8 {0,1} predicted segmentation mask.
    thickness     : ThicknessResult from ``measure_thickness()``.
    spacing_mm    : Physical voxel size (row_mm, col_mm, slice_mm) or None.
    out_png       : Destination path for the PNG file.
    slice_axis    : Axis along which slices were acquired (default 2).
    model_version : String shown in the figure title.

    Returns
    -------
    OverlayMeta containing the drawn measurement line coordinates.
    """
    # ---- Validate inputs ------------------------------------------------
    if volume.ndim != 3 or mask.ndim != 3:
        raise ValueError(
            f"volume and mask must be 3-D, got {volume.ndim}-D and {mask.ndim}-D"
        )
    if volume.shape != mask.shape:
        raise ValueError(
            f"volume and mask shape mismatch: {volume.shape} vs {mask.shape}"
        )
    if slice_axis not in (0, 1, 2):
        raise ValueError(f"slice_axis must be 0, 1 or 2, got {slice_axis}")

    row_mm, unit = _parse_spacing(spacing_mm, slice_axis)

    # ---- Move slice axis to position 2 (matching thickness.py) ----------
    vol_arr  = np.moveaxis(volume.astype(np.float32), slice_axis, 2)  # (R,C,Z')
    mask_arr = np.moveaxis(mask.astype(bool), slice_axis, 2)           # (R,C,Z')
    norm_vol = _normalise_volume(vol_arr)

    # ---- Identify active slices and partition (same logic as thickness.py)
    any_fg  = mask_arr.any(axis=(0, 1))
    active  = [int(z) for z in np.where(any_fg)[0]]

    # ---- Compute per-region representative slices -----------------------
    _REGION_NAMES = ("anterior", "middle", "posterior")
    region_indices: dict[str, list[int]] = {}
    meta_regions: dict[str, dict] = {}

    if len(active) >= 3:
        ant_idx, mid_idx, post_idx = _partition_active_slices(active)
        region_indices = {
            "anterior":  ant_idx,
            "middle":    mid_idx,
            "posterior": post_idx,
        }
    else:
        # Not enough slices — use what we have for display, geometry will be empty
        for name in _REGION_NAMES:
            region_indices[name] = active

    # For each region: pick the representative slice & derive line geometry
    rep_slices: dict[str, int] = {}
    rep_geoms:  dict[str, dict] = {}

    for name in _REGION_NAMES:
        r_entry = thickness.get(name, {})
        status  = r_entry.get("status", "empty_mask")
        value   = r_entry.get("value")

        if status == "ok" and value is not None and region_indices.get(name):
            # Convert value back to voxels for finding the representative slice
            t_vox = value / row_mm if (row_mm is not None and row_mm > 0) else value
            z_rep, geom = _representative_slice(
                mask_arr, region_indices[name], t_vox
            )
        elif active:
            # Fallback: use the midpoint active slice, still derive geometry
            z_rep = active[len(active) // 2]
            geom  = _slice_geometry(mask_arr[:, :, z_rep]) or {}
        else:
            z_rep = 0
            geom  = {}

        rep_slices[name] = z_rep
        rep_geoms[name]  = geom

        # Record meta
        r = thickness.get(name, {})
        meta_regions[name] = {
            "slice_index":      z_rep,
            "col":              geom.get("col"),
            "row_start":        geom.get("row_start"),
            "row_end":          geom.get("row_end"),
            "thickness_vox":    geom.get("thickness"),
            "thickness_value":  r.get("value"),
            "unit":             r.get("unit", unit),
        }

    # ---- Layout: 2 rows × 3 cols
    #   Top row:    Original MRI (full vol midpoint) | Mask overlay (full vol midpoint) | empty/logo
    #   Bottom row: Anterior panel | Middle panel | Posterior panel
    #
    # We use a 1-row × 5-col layout instead:
    #   [MRI mid] [Mask overlay mid] [Anterior] [Middle] [Posterior]
    # --- all panels share the same aspect so the figure is compact -------

    fig, axes = plt.subplots(1, 5, figsize=(18, 4))
    fig.patch.set_facecolor("#1a1a2e")

    # Global mid-slice (for context panels)
    mid_z    = active[len(active) // 2] if active else norm_vol.shape[2] // 2
    mri_mid  = norm_vol[:, :, mid_z]
    mask_mid = mask_arr[:, :, mid_z].astype(np.uint8)

    # -- Panel 0: Original MRI (context)
    ax0 = axes[0]
    ax0.imshow(mri_mid, cmap="gray", origin="upper",
               interpolation="nearest", vmin=0, vmax=1)
    ax0.set_title("Original MRI", fontsize=_TITLE_FONTSIZE, color="white")
    ax0.axis("off")

    # -- Panel 1: Segmentation overlay (context)
    ax1 = axes[1]
    rgb_mid = _build_rgb_slice(mri_mid)
    rgb_mid = _overlay_mask(rgb_mid, mask_mid, _MASK_COLOUR, alpha=0.45)
    ax1.imshow(rgb_mid, origin="upper", interpolation="nearest")
    legend_patch = mpatches.Patch(color=_MASK_COLOUR, label="Predicted mask")
    ax1.legend(handles=[legend_patch], loc="lower right",
               fontsize=6, framealpha=0.6, facecolor="#1a1a2e",
               labelcolor="white", edgecolor="none")
    ax1.set_title("Segmentation", fontsize=_TITLE_FONTSIZE, color="white")
    ax1.axis("off")

    # -- Panels 2-4: Anterior / Middle / Posterior measurement panels
    for i, name in enumerate(_REGION_NAMES):
        ax = axes[2 + i]
        z   = rep_slices[name]
        geom = rep_geoms[name]
        r_entry = thickness.get(name, {})

        _render_region_panel(
            ax,
            mri_2d  = norm_vol[:, :, z],
            mask_2d = mask_arr[:, :, z].astype(np.uint8),
            geom    = geom,
            region_name  = name,
            value   = r_entry.get("value"),
            unit    = r_entry.get("unit", unit),
            status  = r_entry.get("status", "empty_mask"),
        )

    # -- Overall title
    title_parts = [f"Medial Meniscus Thickness  —  {name.capitalize()}: {_format_value(thickness[name].get('value'), thickness[name].get('unit', unit))}"
                   for name in _REGION_NAMES]
    fig.suptitle("  |  ".join(title_parts),
                 fontsize=9, color="white", y=1.01)

    if model_version:
        fig.text(0.99, 0.01, f"model: {model_version}",
                 ha="right", va="bottom", fontsize=6, color="#888888")

    fig.tight_layout(pad=0.8)

    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    fig.savefig(out_png, dpi=_DPI, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)

    return OverlayMeta(meta_regions)


# ---------------------------------------------------------------------------
# JSON result builder
# ---------------------------------------------------------------------------

def build_json_result(
    thickness: ThicknessResult,
    overlay_path: str,
    model_version: str,
    spacing_mm: tuple[float, float, float] | None,
    subject_id: str = "",
    extra: dict[str, Any] | None = None,
) -> dict:
    """Build a machine-readable result dict.

    Schema
    ------
    {
        "subject_id":    str,
        "model_version": str,
        "spacing":       {"row_mm": ..., "col_mm": ..., "slice_mm": ...} | null,
        "measurements":  {
            "anterior":  {"value": ..., "unit": ..., "method": ..., "status": ...},
            "middle":    {...},
            "posterior": {...}
        },
        "overlay_path":  str   (absolute)
    }
    """
    spacing_dict: dict | None = None
    if spacing_mm is not None:
        try:
            sp = tuple(float(v) for v in spacing_mm[:3])
            if all(math.isfinite(v) and v > 0 for v in sp):
                spacing_dict = {
                    "row_mm":   sp[0],
                    "col_mm":   sp[1],
                    "slice_mm": sp[2],
                }
        except (TypeError, ValueError):
            pass

    result: dict[str, Any] = {
        "subject_id":    subject_id,
        "model_version": model_version,
        "spacing":       spacing_dict,
        "measurements":  dict(thickness),
        "overlay_path":  os.path.abspath(overlay_path),
    }
    if extra:
        result.update(extra)
    return result
