"""Smoke test: run the U-Net forward pass through the real preprocessing.

NOT training. Weights are freshly initialized (untrained); this only proves
the Phase 3 output feeds the network end-to-end with correct shapes/dtypes
and that a sigmoid probability map comes out aligned with the input grid.
"""

from __future__ import annotations

import os
import sys
import tempfile

import numpy as np
import torch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexora.data import PairSlicesDataset  # noqa: E402
from ml.models import UNet2D, count_parameters  # noqa: E402
from nexora.preprocessing import PreprocessConfig, preprocess_slice  # noqa: E402

from fixtures import MENISCUS_LABEL, write_fixtures  # noqa: E402


def main() -> int:
    torch.manual_seed(0)

    model = UNet2D()
    model.eval()
    n_params = count_parameters(model)
    print(f"model     : UNet2D ({n_params:,} trainable params)")
    print(f"torch     : {torch.__version__}")

    with tempfile.TemporaryDirectory(prefix="nexora_unet_smoke_") as tmp:
        write_fixtures(tmp, n_volumes=1, seed=7)
        ds = PairSlicesDataset(pairs_root=tmp, slice_axis=2, top_k_per_volume=1,
                               foreground_labels=(MENISCUS_LABEL,))
        cfg = PreprocessConfig(target_size=(256, 256))
        sample = preprocess_slice(ds[0], cfg)

        x = sample.image.unsqueeze(0)
        print(f"input     : shape={tuple(x.shape)} dtype={x.dtype} "
              f"range=[{x.min():.3f}, {x.max():.3f}]")

        with torch.no_grad():
            logits = model(x)
            probs = torch.sigmoid(logits)
            binary = (probs > 0.5).uint8 if hasattr((probs > 0.5), "uint8") else (probs > 0.5).to(torch.uint8)

        assert logits.shape == (1, 1, 256, 256), f"bad output shape {tuple(logits.shape)}"
        assert torch.isfinite(logits).all(), "non-finite logits"
        pmin, pmax = float(probs.min()), float(probs.max())
        bsum = int(binary.sum())
        gt_px = int(sample.mask.sum())
        iou = float((binary & sample.mask.to(torch.uint8)).sum()) / max(
            float((binary | sample.mask.to(torch.uint8)).sum()), 1.0)

        print(f"logits    : shape={tuple(logits.shape)} "
              f"range=[{float(logits.min()):.3f}, {float(logits.max()):.3f}]")
        print(f"probs     : range=[{pmin:.4f}, {pmax:.4f}]")
        print(f"pred px   : {bsum}   gt px: {gt_px}   IoU: {iou:.4f}")
        print("NOTE      : untrained weights -> prediction is meaningless noise;")
        print("            this run only validates plumbing (shapes/flow/alignment).")

    print("\nSMOKE TEST PASSED (no training performed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
