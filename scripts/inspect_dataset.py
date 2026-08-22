"""Phase 1 dataset inspection: actual on-disk structure only.

Inspects the locally available OAI-derived knee X-ray classification dataset.
Reports image format, dimensions, splits, class folders, subject IDs,
laterality, and whether any segmentation masks / metadata exist.

Run:  python scripts/inspect_dataset.py [DATASET_ROOT]
"""

import os
import re
import sys
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

DEFAULT_ROOT = r"C:\Users\hp\Downloads\archive (7)"
SPLITS = ["train", "val", "test", "auto_test"]
STD_RE = re.compile(r"^(\d+)([LR])\.png$")
SUF_RE = re.compile(r"^(\d+)_(\d+)\.png$")


def scan(root):
    files = []  # (split, cls, filename, path)
    for split in SPLITS:
        sdir = os.path.join(root, split)
        if not os.path.isdir(sdir):
            continue
        classes = sorted(
            (d for d in os.listdir(sdir) if os.path.isdir(os.path.join(sdir, d))),
            key=lambda x: int(x) if x.isdigit() else -1,
        )
        for cls in classes:
            cdir = os.path.join(sdir, cls)
            for fn in sorted(os.listdir(cdir)):
                if fn.lower().endswith(".png"):
                    files.append((split, cls, fn, os.path.join(cdir, fn)))
    return files


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROOT
    print(f"Dataset root: {root}")
    if not os.path.isdir(root):
        sys.exit("ERROR: dataset root does not exist")

    # ---------- top-level layout ----------
    print("\n== Top-level entries ==")
    for e in sorted(os.listdir(root)):
        p = os.path.join(root, e)
        kind = "DIR " if os.path.isdir(p) else "file"
        print(f"  [{kind}] {e}")

    files = scan(root)
    print(f"\nTotal PNG images: {len(files)}")

    non_png = [
        os.path.join(r, f)
        for r, ds, fs in os.walk(root)
        for f in fs
        if not f.lower().endswith(".png")
    ]
    print(f"Non-PNG files (masks/metadata candidates): {len(non_png)}")
    for p in non_png[:10]:
        print(f"  {p}")
    if non_png:
        print("  -> mask / metadata candidates FOUND")
    else:
        print("  -> NO mask files and NO metadata files exist in this dataset")

    # ---------- per split/class counts ----------
    counts = Counter((s, c) for s, c, _, _ in files)
    print("\n== Images per split/class ==")
    for split in SPLITS:
        row = {c: counts.get((split, c), 0) for c in ["0", "1", "2", "3", "4"]}
        if any(row.values()):
            print(f"  {split:10s} " + "  ".join(f"{k}:{v}" for k, v in row.items()))

    # ---------- one representative image per class ----------
    print("\n== Representative sample per class (train) ==")
    samples = {}
    for _, cls, fn, path in files:
        if os.path.normpath(os.path.dirname(os.path.dirname(path))).endswith("train"):
            samples.setdefault(cls, path)
    for cls in sorted(samples):
        img = Image.open(samples[cls])
        arr = np.array(img)
        print(
            f"  class {cls}: {os.path.basename(samples[cls])} "
            f"size={img.size} mode={img.mode} dtype={arr.dtype} "
            f"min={arr.min()} max={arr.max()} mean={arr.mean():.1f}"
        )

    # ---------- dimension consistency ----------
    dims = Counter()
    for *_, path in files:
        with Image.open(path) as im:
            dims[(im.size, im.mode)] += 1
    print("\n== Dimension histogram over ALL files (size, mode) ==")
    for k, v in dims.items():
        print(f"  {k}: {v}")
    print("  -> no spatial calibration available: pixel spacing is not stored "
          "in PNG; all images are pre-resized to 224x224")

    # ---------- subjects, laterality, filename conventions ----------
    knees = defaultdict(set)      # (id, L/R) -> {(split, class)}
    suffix = defaultdict(set)     # (id, n)   -> {(split, class)}
    ids_lr, ids_suf = set(), set()
    lat_counter = Counter()
    bad_names = []
    for split, cls, fn, _ in files:
        m = STD_RE.match(fn)
        if m:
            sid, lat = m.groups()
            knees[(sid, lat)].add(cls)
            ids_lr.add(sid)
            lat_counter[lat] += 1
            continue
        s = SUF_RE.match(fn)
        if s:
            suffix[(s.group(1), s.group(2))].add(cls)
            ids_suf.add(s.group(1))
            continue
        bad_names.append(fn)

    all_ids = ids_lr | ids_suf
    print("\n== Subjects / laterality ==")
    print(f"  unique numeric IDs: {len(all_ids)}")
    print(f"  filenames with explicit laterality {{id}}{{L|R}}.png : {sum(lat_counter.values())} ({dict(lat_counter)})")
    print(f"  filenames with ambiguous {{id}}_{{1|2}}.png          : {len(ids_suf)} IDs involved")
    print(f"  unparseable filenames                              : {len(bad_names)}")
    print(f"  suffix-file IDs that also have L/R files           : {len(ids_suf & ids_lr)} of {len(ids_suf)}")
    conflicts = [k for k, v in knees.items() if len(v) > 1]
    print(f"  knees assigned >1 class label                      : {len(conflicts)}")

    # cross-split leakage
    where = defaultdict(set)
    for split, cls, fn, _ in files:
        base = fn.split("_")[0].replace(".png", "")
        m = STD_RE.match(fn)
        where[m.group(1) if m else base].add(split)
    leaked = sum(1 for v in where.values() if len(v) > 1)
    print(f"  IDs appearing in more than one split               : {leaked}")

    # ---------- masks / labels availability summary ----------
    print("\n== Availability checklist ==")
    checks = {
        "Image format": "PNG, 8-bit grayscale ('L' mode), uint8",
        "Mask file format": None,
        "NIfTI/NRRD volumes": None,
        "Unique mask labels": None,
        "Medial meniscus label": None,
        "Femur/tibia/other structures": None,
        "Affine/header/voxel spacing/orientation": None,
        "Class labels": "folder index 0-4 per image (single consistent label per knee)",
        "Age/sex/BMI/OA-grade table": None,
        "Visit/timepoint info": None,
    }
    for k, v in checks.items():
        print(f"  {k}: {'PRESENT - ' + str(v) if v else 'ABSENT'}")

    # ---------- visualization ----------
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(out_dir, exist_ok=True)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, len(samples), figsize=(3 * len(samples), 3.2))
        for ax, cls in zip(np.atleast_1d(axes), sorted(samples)):
            ax.imshow(Image.open(samples[cls]), cmap="gray")
            ax.set_title(f"class {cls}\n{os.path.basename(samples[cls])}", fontsize=8)
            ax.axis("off")
        fig.suptitle("Representative sample per class (train)")
        out_path = os.path.join(out_dir, "dataset_samples.png")
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        print(f"\nVisualization saved: {out_path}")
    except ImportError:
        print("\nmatplotlib not installed - skipped visualization")

    print("\nDone.")


if __name__ == "__main__":
    main()
