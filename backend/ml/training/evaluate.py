"""Phase 8: final segmentation evaluation on the HELD-OUT TEST SET ONLY.

* Subjects come exclusively from the `test` partition of
  ml/training/splits.json (patient-level, created in Phase 4); the script
  asserts they do not overlap train/val subjects before touching data.
* "Complete test set" = EVERY meniscus-bearing slice of the test subjects,
  not the top-k subset used during training.
* Metrics: Dice / IoU / Precision / Recall (hard, threshold 0.5),
  reported as mean, median and std over slices.
* Visual examples (MRI | ground truth | prediction | overlay) are written
  to outputs/evaluation/.

Run:  python ml/training/evaluate.py --checkpoint checkpoints/best_model.pth
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (os.path.join(_ROOT, "src"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402

from ml.metrics import dice_score, iou_score, precision_score, recall_score  # noqa: E402
from ml.models import UNet2D  # noqa: E402
from ml.training.train import (  # noqa: E402
    BEST_CKPT,
    HISTORY_JSON,
    SPLITS_PATH,
    SliceDataset,
    load_partitions,
    resolve_pairs,
    set_seeds,
)
from nexora.data.splitting import extract_subject_id  # noqa: E402

OUT_DIR = os.path.join(_ROOT, "outputs", "evaluation")
METRICS_JSON = os.path.join(_ROOT, "outputs", "test_metrics.json")

LIMITATIONS = [
    "SYNTHETIC DATA: metrics were computed on generated phantom fixtures, "
    "not real knee MRI; they validate plumbing only and say NOTHING about "
    "clinical or real-world meniscus segmentation performance.",
    "TINY SAMPLE: the test partition contains very few subjects/slices; "
    "mean/median/std are unstable at this size and no statistical "
    "significance is claimed.",
    "SLICE-LEVEL EVALUATION: each slice is scored independently in 2D; no "
    "3D volumetric consistency is measured.",
    "SELECTION BIAS: only meniscus-bearing slices enter the set "
    "(min_mask_pixels >= 1), so empty-slice behaviour is untested.",
    "MODEL SELECTION NOISE: best_model.pth was chosen on a 3-slice "
    "validation subset; checkpoint choice may be luck rather than skill.",
    "SAME-DISTRIBUTION ASSUMPTION: test slices use the identical synthetic "
    "generator and preprocessing as training; domain shift is unmeasured.",
    "EMPTY-MASK CONVENTION: when GT and prediction are both empty, scores "
    "count as perfect agreement (1.0) per Phase 6 convention.",
]


def stats(values: list[float]) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "mean": round(float(arr.mean()), 6),
        "median": round(float(np.median(arr)), 6),
        "std": round(float(arr.std(ddof=0)), 6),
        "min": round(float(arr.min()), 6),
        "max": round(float(arr.max()), 6),
    }


def save_example(path: str, image: np.ndarray, gt: np.ndarray,
                 pred: np.ndarray, title: str) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    rgb = np.repeat(image[..., None], 3, axis=-1)

    overlay = rgb.copy()
    overlay[gt > 0.5] = [0.0, 1.0, 0.0]                       # GT green
    blend = overlay.copy()
    blend[pred > 0.5] = 0.55 * blend[pred > 0.5] + 0.45 * np.array([1.0, 0.0, 0.0])
    overlay[(pred > 0.5) & (gt <= 0.5)] = [1.0, 0.0, 0.0]     # FP red
    overlay[(pred > 0.5) & (gt > 0.5)] = [1.0, 1.0, 0.0]      # TP yellow

    for ax, img, t in zip(
        axes,
        [image, gt, pred, overlay],
        ["Original MRI", "Ground truth", "Predicted mask", "Overlay"],
    ):
        if img.ndim == 2 and img.max() > 1:
            ax.imshow(img, cmap="gray")
        elif img.ndim == 2:
            ax.imshow(img, cmap="gray", vmin=0, vmax=1)
        else:
            ax.imshow(img)
        ax.set_title(t, fontsize=10)
        ax.axis("off")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 8 held-out test evaluation")
    ap.add_argument("--checkpoint", default=BEST_CKPT)
    ap.add_argument("--splits", default=SPLITS_PATH)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--num-examples", type=int, default=4,
                    help="visual panels to render (spread across the set)")
    args = ap.parse_args()

    set_seeds(args.seed)

    with open(args.splits, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    partitions = {k: {s["subject_id"] for s in v["samples"]}
                  for k, v in manifest["splits"].items()}
    test_subjects = partitions["test"]
    assert not (test_subjects & partitions["train"]), "train/test subject leakage!"
    assert not (test_subjects & partitions["val"]), "val/test subject leakage!"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    input_size = tuple(ckpt["input_size"])
    model = UNet2D(in_channels=1, out_channels=1, base=ckpt.get("base", 16),
                   depth=ckpt.get("depth", 4), input_size=input_size).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    pairs, data_desc = resolve_pairs(None, args.seed)
    ds = SliceDataset(pairs, test_subjects, top_k=None, input_size=input_size)
    print(f"device    : {device}")
    print(f"data      : {data_desc}")
    print(f"splits    : source={manifest['source']}  seed={manifest['seed']}")
    print(f"test set  : {len(test_subjects)} subjects -> {len(ds)} meniscus-bearing slices")

    rows = []
    cache = []
    with torch.no_grad():
        for i in range(len(ds)):
            it = ds.items[i]
            sid = extract_subject_id(os.path.basename(it.source_image))
            x, y = ds[i]
            prob = torch.sigmoid(model(x.unsqueeze(0)))[0]
            kw = dict(threshold=args.threshold, reduction="none")
            row = {
                "subject_id": sid,
                "slice_index": int(it.slice_index),
                "dice": float(dice_score(prob, y, **kw)),
                "iou": float(iou_score(prob, y, **kw)),
                "precision": float(precision_score(prob, y, **kw)),
                "recall": float(recall_score(prob, y, **kw)),
                "gt_pixels": int((y > 0.5).sum()),
                "pred_pixels": int((prob > args.threshold).sum()),
            }
            rows.append(row)
            cache.append((sid, it.slice_index, x.numpy()[0], y.numpy()[0],
                          prob.numpy()[0]))

    report = {
        "checkpoint": os.path.relpath(args.checkpoint, _ROOT),
        "checkpoint_val_dice_at_save": ckpt.get("val_dice"),
        "splits_source": manifest["source"],
        "split_seed": manifest["seed"],
        "evaluated_on": data_desc,
        "device": str(device),
        "n_test_subjects": len(test_subjects),
        "n_test_slices": len(rows),
        "threshold": args.threshold,
        "metrics": {
            name: stats([r[name] for r in rows])
            for name in ("dice", "iou", "precision", "recall")
        },
        "per_slice": rows,
        "limitations": LIMITATIONS,
    }
    os.makedirs(os.path.dirname(METRICS_JSON), exist_ok=True)
    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    os.makedirs(OUT_DIR, exist_ok=True)
    picks = sorted(set(np.linspace(0, len(cache) - 1,
                                   num=min(args.num_examples, len(cache))).astype(int)))
    for j in picks:
        sid, sidx, img, gt, pr = cache[j]
        save_example(
            os.path.join(OUT_DIR, f"example_{j:03d}_sub{sid}_z{sidx:02d}.png"),
            img, gt, (pr > args.threshold).astype(np.float32),
            title=f"subject {sid} | slice z={sidx} | "
                  f"Dice {rows[j]['dice']:.3f} IoU {rows[j]['iou']:.3f}",
        )

    print(f"\n{'metric':<10}{'mean':>9}{'median':>9}{'std':>9}{'min':>9}{'max':>9}")
    for name, st in report["metrics"].items():
        print(f"{name:<10}{st['mean']:>9.4f}{st['median']:>9.4f}"
              f"{st['std']:>9.4f}{st['min']:>9.4f}{st['max']:>9.4f}")

    print(f"\nsaved metrics JSON : {METRICS_JSON}")
    print(f"saved {len(picks)} example panels -> {OUT_DIR}")
    print("NOTE: " + LIMITATIONS[0][:88] + "...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
