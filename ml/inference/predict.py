"""Phase 9: inference pipeline for medial meniscus segmentation.

Image (NIfTI) -> preprocessing -> trained U-Net -> probability map
-> binary mask -> post-processing -> structured result.

The model is loaded ONCE per MeniscusPredictor instance, kept in eval()
mode and always queried under torch.no_grad(). Device is chosen
automatically (CUDA if available, else CPU).

Spacing policy: in-plane spacing is read from the NIfTI header zooms; if
the header is missing, zero or non-finite the result carries
`spacing: None`. Physical units are NEVER invented.

CLI (from the repo root):
    python -m ml.inference.predict <sample.nii.gz> [--save-mask out.nii.gz]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nibabel as nib  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from scipy import ndimage as ndi  # noqa: E402

from ml.models import UNet2D  # noqa: E402
from nexora.data.splitting import extract_subject_id  # noqa: E402
from nexora.preprocessing.pipeline import (  # noqa: E402
    PreprocessConfig,
    normalize_intensity,
    resize_image,
)

DEFAULT_CHECKPOINT = os.path.join(_ROOT, "checkpoints", "best_model.pth")
DEFAULT_THRESHOLD = 0.5


def _valid_spacing(zooms) -> tuple[float, float, float] | None:
    try:
        sp = tuple(float(z) for z in zooms[:3])
    except (TypeError, ValueError, IndexError):
        return None
    if not all(np.isfinite(sp) and sp > 0 for sp in sp):
        return None
    return sp


class MeniscusPredictor:
    """Loads the trained U-Net once; predicts meniscus masks for volumes."""

    def __init__(self, checkpoint_path: str = DEFAULT_CHECKPOINT,
                 device: str | None = None, threshold: float = DEFAULT_THRESHOLD):
        self.device = torch.device(
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        if not os.path.isfile(checkpoint_path):
            raise FileNotFoundError(f"checkpoint not found: {checkpoint_path}")
        ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        required = {"model_state_dict", "input_size", "base", "depth"}
        missing = required - set(ckpt)
        if missing:
            raise ValueError(f"checkpoint missing keys: {sorted(missing)}")

        self.input_size = tuple(int(v) for v in ckpt["input_size"])
        self.cfg = PreprocessConfig(target_size=self.input_size)
        self.threshold = float(threshold)
        self.model = UNet2D(in_channels=1, out_channels=1,
                            base=int(ckpt["base"]), depth=int(ckpt["depth"]),
                            input_size=self.input_size).to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

        self.model_version = ckpt.get("model_version") or (
            f"unet2d-base{ckpt['base']}-depth{ckpt['depth']}-epoch{ckpt.get('epoch', '?')}"
        )

    def validate_input(self, image_path: str) -> None:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"image not found: {image_path}")
        low = image_path.lower()
        if not low.endswith((".nii", ".nii.gz")):
            raise ValueError(f"expected a .nii/.nii.gz file, got: {image_path}")

    def _preprocess_slices(self, volume: np.ndarray) -> torch.Tensor:
        """Normalize + resize each slice exactly like training (image only)."""
        planes = [np.ascontiguousarray(s, dtype=np.float32)
                  for s in np.moveaxis(volume, 2, 0)]     # (Z, H, W)
        tensors = []
        for sl in planes:
            norm = normalize_intensity(sl, self.cfg.clip_percentiles)
            resized = resize_image(norm, self.cfg.target_size)
            tensors.append(torch.from_numpy(resized).float())
        return torch.stack(tensors).unsqueeze(1)          # (Z, 1, H', W')

    @torch.no_grad()
    def _forward(self, batch: torch.Tensor) -> torch.Tensor:
        return torch.sigmoid(self.model(batch.to(self.device)))

    def _postprocess_slice(self, binary_small: np.ndarray,
                           min_area: int, out_hw: tuple[int, int]) -> np.ndarray:
        """Drop small components at model resolution, then NN-resize back."""
        lab, n = ndi.label(binary_small)
        if n:
            sizes = np.bincount(lab.ravel())
            keep = sizes >= max(min_area, 1)
            keep[0] = False
            binary_small = keep[lab]
        up = resize_image(binary_small.astype(np.float32), out_hw) >= 0.5
        return up.astype(np.uint8)

    def predict_volume(self, image_path: str, batch_size: int = 8,
                       min_area: int = 25) -> dict:
        self.validate_input(image_path)
        nii = nib.load(image_path)
        data = np.squeeze(nii.get_fdata(dtype=np.float32))
        if data.ndim not in (2, 3):
            raise ValueError(f"expected a 2D or 3D image, got ndim={data.ndim}")
        if data.size == 0 or not np.isfinite(data).all():
            raise ValueError("image is empty or contains non-finite values")

        vol3d = data[:, :, None] if data.ndim == 2 else data
        orig_shape = vol3d.shape                      # (H, W, Z)

        x = self._preprocess_slices(vol3d)
        probs = torch.cat([self._forward(x[i:i + batch_size])
                           for i in range(0, x.shape[0], batch_size)])
        probs_np = probs.squeeze(1).cpu().numpy()     # (Z, h, w) model space

        mask = np.zeros(orig_shape, dtype=np.uint8)   # original resolution
        for z in range(probs_np.shape[0]):
            bin_small = (probs_np[z] >= self.threshold).astype(np.uint8)
            mask[:, :, z] = np.moveaxis(
                self._postprocess_slice(bin_small, min_area,
                                        (orig_shape[0], orig_shape[1])),
                0, 1)

        return {
            "mask": mask,                                        # uint8 {0,1}, input resolution
            "probability": probs_np.astype(np.float32),          # model resolution
            "subject_id": extract_subject_id(os.path.basename(image_path)),
            "spacing": _valid_spacing(nii.header.get_zooms()),   # None if unusable
            "image_shape": orig_shape,
            "model_version": self.model_version,
            "threshold": self.threshold,
            "mask_shape": mask.shape,
            "probability_shape": probs_np.shape,
            "source_image": os.path.abspath(image_path),
        }


def save_mask(result: dict, out_path: str, source_nifti: str | None = None) -> None:
    """Save predicted mask as uint8 NIfTI on the source image grid."""
    parent = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(parent, exist_ok=True)
    affine = np.eye(4)
    if source_nifti:
        affine = nib.load(source_nifti).affine
    img = nib.Nifti1Image(np.asarray(result["mask"], dtype=np.uint8), affine)
    nib.save(img, out_path)


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="ml.inference.predict",
        description="Predict a meniscus mask for a knee MRI volume.",
    )
    ap.add_argument("sample", help="path to a .nii/.nii.gz knee MRI volume")
    ap.add_argument("--checkpoint", default=DEFAULT_CHECKPOINT)
    ap.add_argument("--device", default=None, choices=[None, "cpu", "cuda"])
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--min-area", type=int, default=25,
                    help="drop connected components smaller than this "
                         "(model-resolution pixels)")
    ap.add_argument("--save-mask", metavar="PATH", default=None,
                    help="write the predicted mask as a uint8 NIfTI")
    args = ap.parse_args()

    predictor = MeniscusPredictor(args.checkpoint, device=args.device,
                                  threshold=args.threshold)
    result = predictor.predict_volume(args.sample, batch_size=args.batch_size,
                                      min_area=args.min_area)

    if args.save_mask:
        save_mask(result, args.save_mask, source_nifti=args.sample)

    summary = {
        "subject_id": result["subject_id"],
        "spacing_mm": result["spacing"],
        "image_shape": list(result["image_shape"]),
        "mask_shape": list(result["mask_shape"]),
        "probability_shape": list(result["probability_shape"]),
        "mask_dtype": str(result["mask"].dtype),
        "predicted_voxels": int(result["mask"].sum()),
        "slices_with_mask": int((result["mask"].reshape(-1, result["mask"].shape[-1]).sum(axis=0) > 0).sum()),
        "prob_range": [float(result["probability"].min()),
                       float(result["probability"].max())],
        "threshold": result["threshold"],
        "model_version": result["model_version"],
        "device": str(predictor.device),
        "saved_mask": args.save_mask,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
