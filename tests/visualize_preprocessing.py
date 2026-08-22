"""Phase 3 visualization: Original MRI | Ground-truth meniscus mask | Overlay.

Run:  python tests/visualize_preprocessing.py [--samples N]
Generates docs/preprocessing_samples.png from the synthetic fixtures until
the real dataset is placed under data/raw/.
"""

from __future__ import annotations

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _HERE)

from nexora.data import PairSlicesDataset, discover_pairs  # noqa: E402
from nexora.preprocessing import PreprocessConfig, preprocess_slice  # noqa: E402

from fixtures import MENISCUS_LABEL, write_fixtures  # noqa: E402
from test_preprocessing import load_from_arrays  # noqa: E402


def save_visualization(samples, out_path: str | None = None) -> str:
    n = len(samples)
    fig, axes = plt.subplots(n, 3, figsize=(9, 3.1 * n))
    axes = np.atleast_2d(axes)

    for row, s in enumerate(samples):
        img = s.image[0].numpy()
        msk = s.mask[0].numpy()

        axes[row, 0].imshow(img, cmap="gray", vmin=0, vmax=1)
        axes[row, 0].set_title("Original MRI (preprocessed)", fontsize=9)

        axes[row, 1].imshow(msk, cmap="gray", vmin=0, vmax=1)
        axes[row, 1].set_title(
            f"GT meniscus mask  uniq={sorted(set(np.unique(msk).tolist()))}",
            fontsize=9,
        )

        rgb = np.repeat(img[..., None], 3, axis=-1)
        rgb[msk > 0] = [1.0, 0.35, 0.1]
        axes[row, 2].imshow(np.clip(rgb, 0, 1))
        axes[row, 2].set_title("MRI + mask overlay", fontsize=9)

        for col in range(3):
            axes[row, col].axis("off")
        axes[row, 1].set_xlabel(
            f"vol {s.volume_index} slice {s.slice_index}  "
            f"spacing_orig={tuple(round(v, 2) for v in s.spacing_mm_original)} mm",
            fontsize=7,
        )

    fig.suptitle(
        "Phase 3 preprocessing verification "
        "(synthetic fixtures; real dataset pending placement under data/raw)",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    if out_path is None:
        out_path = os.path.join(_ROOT, "docs", "preprocessing_samples.png")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def main() -> int:
    n = 3
    if "--samples" in sys.argv:
        n = int(sys.argv[sys.argv.index("--samples") + 1])

    real_root = os.path.join(_ROOT, "data", "raw")
    pairs = discover_pairs(real_root) if os.path.isdir(real_root) else []
    source = "real data/raw"

    if not pairs:
        tmp_dir = os.path.join(_ROOT, "data", "fixtures_tmp")
        write_fixtures(tmp_dir, n_volumes=3, seed=42)
        pairs = discover_pairs(tmp_dir)
        source = "SYNTHETIC fixtures (test plumbing only)"

    ds = PairSlicesDataset(pairs=pairs[: max(n, 3)], slice_axis=2, top_k_per_volume=1,
                           foreground_labels=(MENISCUS_LABEL,))
    cfg = PreprocessConfig(target_size=(256, 256))

    picked, seen_vols = [], set()
    for item in ds:
        if item.volume_index in seen_vols:
            continue
        seen_vols.add(item.volume_index)
        picked.append(preprocess_slice(item, cfg))
        if len(picked) == n:
            break

    for p in picked:
        assert isinstance(p.image, torch.Tensor) and isinstance(p.mask, torch.Tensor)
        assert set(torch.unique(p.mask).tolist()).issubset({0.0, 1.0})

    out_png = save_visualization(picked)
    print(f"source : {source}")
    print(f"samples: {len(picked)}")
    print(f"saved  : {out_png}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
