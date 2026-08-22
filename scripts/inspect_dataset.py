"""OAI Tissue Segmentations - read-only dataset inspector.

Usage:
    python scripts/inspect_dataset.py --data-root <path-to-dataset>

Outputs:
    reports/dataset_inspection.json   machine-readable summary
    reports/sample_slice.png          image+mask overlay of one slice

Reads only. Never writes inside the dataset folder.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

VOLUME_EXTS = (".nii.gz", ".nii", ".mha", ".mhd", ".nrrd")
MASK_HINTS = ("seg", "mask", "label", "tissue")


def find_volumes(root: Path):
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.name.lower().endswith(VOLUME_EXTS)
    )


def is_mask(path: Path) -> bool:
    stem = path.name.lower()
    return any(h in stem for h in MASK_HINTS)


def load_volume(path: Path):
    try:
        import nibabel as nib
    except ImportError:
        nib = None
    try:
        import SimpleITK as sitk
    except ImportError:
        sitk = None

    if path.name.lower().endswith(VOLUME_EXTS[:2]) and nib is not None:
        img = nib.load(str(path))
        data = np.asanyarray(img.dataobj)
        meta = {
            "loader": "nibabel",
            "affine": np.asarray(img.affine).tolist(),
            "orientation": "".join(nib.aff2axcodes(img.affine)),
            "voxel_spacing": [float(v) for v in img.header.get_zooms()[:3]],
        }
        return data, meta
    if sitk is not None:
        img = sitk.ReadImage(str(path))
        data = sitk.GetArrayFromImage(img)
        meta = {
            "loader": "SimpleITK",
            "affine": None,
            "orientation": None,
            "voxel_spacing": [float(v) for v in img.GetSpacing()],
        }
        return data, meta
    sys.exit("Neither nibabel nor SimpleITK could load this format. pip install nibabel")


def describe_file(path: Path) -> dict:
    data, meta = load_volume(path)
    info = {
        "file": str(path),
        "size_bytes": path.stat().st_size,
        "shape": list(data.shape),
        "dtype": str(data.dtype),
        **meta,
    }
    if is_mask(path):
        labels, counts = np.unique(data.astype(np.int32), return_counts=True)
        info["unique_labels"] = [int(l) for l in labels]
        info["label_counts"] = {str(int(l)): int(c) for l, c in zip(labels, counts)}
    else:
        info["intensity_min"] = float(np.min(data))
        info["intensity_max"] = float(np.max(data))
    return info


def subject_token(path: Path) -> str:
    m = re.match(r"\s*(\d+)", Path(path.name).stem.replace(".nii", ""))
    return m.group(1) if m else "UNKNOWN"


def pick_slice(image: np.ndarray, mask: np.ndarray | None) -> tuple[int, int]:
    axes = range(image.ndim)
    if mask is not None and np.any(mask > 0):
        best_ax, best_idx, best_hit = 0, 0, -1
        for ax in axes:
            proj = (mask > 0).sum(axis=tuple(i for i in axes if i != ax))
            idx = int(np.argmax(proj))
            if int(proj[idx]) > best_hit:
                best_ax, best_idx, best_hit = ax, idx, int(proj[idx])
        return best_ax, best_idx
    ax = int(np.argmin(image.shape))
    return ax, image.shape[ax] // 2


def save_visualization(image_path: Path, mask_path: Path | None, out_png: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    image, _ = load_volume(image_path)
    mask, _ = (load_volume(mask_path) if mask_path else (None, None))
    ax, idx = pick_slice(image, mask)

    img_slice = np.take(image, idx, axis=ax)
    msk_slice = np.take(mask, idx, axis=ax) if mask is not None else None

    fig, axes = plt.subplots(1, 3 if msk_slice is not None else 2, figsize=(12, 5))
    axes[0].imshow(img_slice.T, cmap="gray", origin="lower")
    axes[0].set_title(f"{image_path.name}\naxis={ax} slice={idx}")
    if msk_slice is not None:
        axes[1].imshow(msk_slice.T, cmap="nipy_spectral", origin="lower")
        axes[1].set_title("mask labels")
        axes[2].imshow(img_slice.T, cmap="gray", origin="lower")
        axes[2].imshow(np.ma.masked_where(msk_slice == 0, msk_slice).T,
                       cmap="autumn", alpha=0.5, origin="lower")
        axes[2].set_title("overlay")
    for a in axes:
        a.axis("off")
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True, type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("reports"))
    args = ap.parse_args()

    root = args.data_root
    if not root.is_dir():
        sys.exit(f"data root not found: {root}")

    volumes = find_volumes(root)
    if not volumes:
        sys.exit(f"No volume files ({', '.join(VOLUME_EXTS)}) found under {root}")

    masks = [p for p in volumes if is_mask(p)]
    images = [p for p in volumes if not is_mask(p)]

    file_reports = []
    all_labels = set()
    for p in volumes[:50]:
        rep = describe_file(p)
        file_reports.append(rep)
        all_labels.update(rep.get("unique_labels", []))

    paired = []
    if images and masks:
        for m in masks[:10]:
            stem_m = Path(m.name).stem.lower()
            cands = sorted(images, key=lambda i: len(set(stem_m) ^ set(Path(i.name).stem.lower())))
            paired.append({"image": str(cands[0]), "mask": str(m)})
        if paired:
            save_visualization(Path(paired[0]["image"]), Path(paired[0]["mask"]),
                               args.out_dir / "sample_slice.png")

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "data_root": str(root),
        "n_volumes": len(volumes),
        "n_images": len(images),
        "n_masks": len(masks),
        "n_subject_tokens": len({subject_token(p) for p in volumes}),
        "subject_ids_sample": sorted({subject_token(p) for p in volumes})[:20],
        "union_of_mask_labels": sorted(all_labels),
        "medial_meniscus_label": "UNDETERMINED - requires manual verification",
        "files_inspected": file_reports,
        "example_pairs": paired,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.out_dir / "dataset_inspection.json"
    out_json.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {out_json}")
    if (args.out_dir / "sample_slice.png").exists():
        print(f"Wrote {args.out_dir / 'sample_slice.png'}")
    print(json.dumps({k: v for k, v in summary.items()
                      if k != "files_inspected"}, indent=2))


if __name__ == "__main__":
    main()
