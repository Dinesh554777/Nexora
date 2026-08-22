"""Phase 11 demo: inference → measurement → annotated overlay → JSON.

Runs the full pipeline on a real fixture test image:
  1. Load the NIfTI volume via nibabel (no trained model needed for
     the measurement/visualization path; the fixture masks are used
     as the predicted masks so the demo is fully self-contained and
     does not require checkpoints/best_model.pth).

     If the checkpoint IS present, the script uses the trained
     MeniscusPredictor instead (pass --use-model to force this).

  2. Binarise the ground-truth label mask (label 7 = meniscus).
  3. Run Phase 10 thickness measurement.
  4. Render the Phase 11 overlay PNG.
  5. Write the machine-readable JSON result.

Output:
    outputs/phase11/<subject_id>_overlay.png
    outputs/phase11/<subject_id>_result.json

Usage:
    python scripts/phase11_demo.py
    python scripts/phase11_demo.py --subject phantom_001
    python scripts/phase11_demo.py --use-model
    python scripts/phase11_demo.py --subject phantom_001 --use-model
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402

from ml.analysis.thickness import measure_thickness  # noqa: E402
from ml.visualization.overlay import (  # noqa: E402
    build_json_result,
    draw_measurement_overlay,
)
from tests.fixtures import MENISCUS_LABEL, SPACING_MM  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR   = os.path.join(_ROOT, "data", "fixtures_tmp")
IMG_DIR    = os.path.join(DATA_DIR, "images")
MASK_DIR   = os.path.join(DATA_DIR, "masks")
CKPT_PATH  = os.path.join(_ROOT, "checkpoints", "best_model.pth")
OUT_DIR    = os.path.join(_ROOT, "outputs", "phase11")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_volume(path: str) -> tuple[np.ndarray, tuple[float, float, float] | None]:
    """Return (float32 ndarray, spacing_mm | None)."""
    nii = nib.load(path)
    data = np.squeeze(nii.get_fdata(dtype=np.float32))
    if data.ndim not in (2, 3):
        raise ValueError(f"expected 2-D or 3-D volume, got ndim={data.ndim}")
    if data.ndim == 2:
        data = data[:, :, None]
    zooms = nii.header.get_zooms()
    try:
        sp = tuple(float(z) for z in zooms[:3])
        if all(np.isfinite(sp) and sp > 0 for sp in sp):
            spacing: tuple | None = sp
        else:
            spacing = None
    except Exception:
        spacing = None
    return data, spacing


def _gt_mask(mask_path: str) -> np.ndarray:
    """Load label NIfTI and binarise to meniscus foreground (label 7)."""
    nii = nib.load(mask_path)
    raw = np.squeeze(nii.get_fdata(dtype=np.float32)).astype(np.uint8)
    if raw.ndim == 2:
        raw = raw[:, :, None]
    return np.isin(raw, [MENISCUS_LABEL]).astype(np.uint8)


def _run_model(image_path: str) -> tuple[np.ndarray,
                                          tuple[float, float, float] | None,
                                          str]:
    """Return (binary_mask, spacing, model_version) from MeniscusPredictor."""
    from ml.inference.predict import MeniscusPredictor  # noqa: PLC0415
    predictor = MeniscusPredictor(checkpoint_path=CKPT_PATH)
    result    = predictor.predict_volume(image_path)
    return result["mask"], result["spacing"], result["model_version"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 11 demo: overlay + JSON")
    ap.add_argument(
        "--subject", default="phantom_000",
        help="subject id (default: phantom_000)"
    )
    ap.add_argument(
        "--use-model", action="store_true",
        help="run MeniscusPredictor instead of using GT mask"
    )
    args = ap.parse_args()

    subject_id = args.subject
    img_path   = os.path.join(IMG_DIR,  f"{subject_id}.nii.gz")
    msk_path   = os.path.join(MASK_DIR, f"{subject_id}.nii.gz")

    # --- verify inputs exist ------------------------------------------------
    if not os.path.isfile(img_path):
        print(f"ERROR: image not found: {img_path}", file=sys.stderr)
        return 1

    # --- load MRI volume ----------------------------------------------------
    print(f"Loading image  : {img_path}")
    volume, spacing = _load_volume(img_path)
    print(f"  shape        : {volume.shape}")
    print(f"  spacing      : {spacing}")

    # --- obtain binary mask -------------------------------------------------
    model_version = "gt_mask_phase11_demo"

    if args.use_model:
        if not os.path.isfile(CKPT_PATH):
            print(f"ERROR: checkpoint not found: {CKPT_PATH}\n"
                  "       Run without --use-model to use ground-truth masks.",
                  file=sys.stderr)
            return 1
        print("Running MeniscusPredictor ...")
        mask, spacing, model_version = _run_model(img_path)
        print(f"  model version: {model_version}")
        print(f"  predicted voxels: {int(mask.sum())}")
    else:
        if not os.path.isfile(msk_path):
            print(f"ERROR: mask not found: {msk_path}", file=sys.stderr)
            return 1
        print(f"Loading GT mask: {msk_path}")
        mask = _gt_mask(msk_path)
        # Use spacing from image header (already read); fall back to fixture constant
        if spacing is None:
            spacing = SPACING_MM
        print(f"  foreground voxels: {int(mask.sum())}")

    # --- Phase 10: measure thickness ----------------------------------------
    print("\nMeasuring thickness ...")
    thickness = measure_thickness(mask, spacing_mm=spacing, slice_axis=2)
    for region, r in thickness.items():
        v = r["value"]
        u = r["unit"]
        s = r["status"]
        val_str = f"{v:.4f} {u}" if v is not None else f"None ({s})"
        print(f"  {region:<10}: {val_str}")

    # --- Phase 11: render overlay -------------------------------------------
    os.makedirs(OUT_DIR, exist_ok=True)
    out_png  = os.path.join(OUT_DIR, f"{subject_id}_overlay.png")
    out_json = os.path.join(OUT_DIR, f"{subject_id}_result.json")

    print(f"\nRendering overlay → {out_png}")
    meta = draw_measurement_overlay(
        volume        = volume,
        mask          = mask,
        thickness     = thickness,
        spacing_mm    = spacing,
        out_png       = out_png,
        slice_axis    = 2,
        model_version = model_version,
    )

    # --- build + write JSON -------------------------------------------------
    result_dict = build_json_result(
        thickness     = thickness,
        overlay_path  = out_png,
        model_version = model_version,
        spacing_mm    = spacing,
        subject_id    = subject_id,
        extra         = {
            "source_image": os.path.abspath(img_path),
            "mask_source":  "trained_model" if args.use_model else "ground_truth",
            "mask_foreground_voxels": int(mask.sum()),
            "measurement_lines": meta.as_dict()["measurement_lines"],
        },
    )

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)

    print(f"JSON result    → {out_json}")

    # --- verify outputs exist -----------------------------------------------
    png_ok  = os.path.isfile(out_png)  and os.path.getsize(out_png)  > 1_000
    json_ok = os.path.isfile(out_json) and os.path.getsize(out_json) > 10

    print(f"\nVerification:")
    print(f"  PNG  ({os.path.getsize(out_png):,} bytes)  : {'OK' if png_ok  else 'FAIL'}")
    print(f"  JSON ({os.path.getsize(out_json):,} bytes) : {'OK' if json_ok else 'FAIL'}")

    if not (png_ok and json_ok):
        print("ERROR: one or more output files are missing or empty.", file=sys.stderr)
        return 1

    # --- echo final JSON for quick inspection --------------------------------
    print("\n--- result JSON (excerpt) ---")
    preview = {
        "subject_id":    result_dict["subject_id"],
        "model_version": result_dict["model_version"],
        "spacing":       result_dict["spacing"],
        "measurements":  result_dict["measurements"],
        "overlay_path":  result_dict["overlay_path"],
    }
    print(json.dumps(preview, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
