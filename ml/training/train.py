"""Phase 7: U-Net training pipeline for medial meniscus segmentation.

Wires together the existing stack:
  loader + preprocessing (Phase 3) -> patient-level splits (Phase 4)
  -> UNet2D (Phase 5) -> Dice loss / Dice score / IoU (Phase 6)

Data resolution
---------------
Partitions ALWAYS come from ml/training/splits.json, keyed by SUBJECT ID -
the file written in Phase 4 guarantees leakage-free patient-level splits.
Sample paths are resolved against a data root:
  * real dataset under data/raw when present;
  * otherwise the synthetic fixtures are regenerated deterministically
    (same seed as split creation) and mapped onto the SAME subject
    partitions - clearly labeled so no one mistakes metrics for real
    meniscus performance.

Run:  python ml/training/train.py --epochs 15 --batch-size 4 --lr 1e-3 \
         --max-slices-per-volume 3 --seed 42
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (os.path.join(_ROOT, "src"), _ROOT, os.path.join(_ROOT, "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import torch  # noqa: E402
from torch.utils.data import DataLoader, Dataset  # noqa: E402

from ml.metrics import dice_loss, dice_score, iou_score  # noqa: E402
from ml.models import UNet2D  # noqa: E402
from nexora.data import PairSlicesDataset, discover_pairs  # noqa: E402
from nexora.data.splitting import extract_subject_id  # noqa: E402
from nexora.preprocessing import PreprocessConfig, preprocess_slice  # noqa: E402

from fixtures import MENISCUS_LABEL, write_fixtures  # noqa: E402

SPLITS_PATH = os.path.join(_ROOT, "ml", "training", "splits.json")
BEST_CKPT = os.path.join(_ROOT, "checkpoints", "best_model.pth")
HISTORY_JSON = os.path.join(_ROOT, "outputs", "training_history.json")
FIXTURE_DIR = os.path.join(_ROOT, "data", "fixtures_tmp")


def set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_partitions(splits_path: str = SPLITS_PATH) -> dict:
    with open(splits_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    return {
        name: {s["subject_id"] for s in part["samples"]}
        for name, part in manifest["splits"].items()
    }


def resolve_pairs(source_label: str, seed: int) -> tuple[list, str]:
    """Return (pairs, description) for the configured data source."""
    real_root = os.path.join(_ROOT, "data", "raw")
    real_pairs = discover_pairs(real_root) if os.path.isdir(real_root) else []
    if real_pairs:
        return real_pairs, f"real:{real_root}"

    write_fixtures(FIXTURE_DIR, n_volumes=9, seed=seed)
    pairs = discover_pairs(FIXTURE_DIR)
    if not pairs:
        raise FileNotFoundError("no data available to train on")
    return pairs, f"SYNTHETIC fixtures (regenerated at {FIXTURE_DIR})"


class SliceDataset(Dataset):
    """Preprocessed slice samples restricted to an allowed subject set."""

    def __init__(self, pairs: list, subjects: set, top_k: int,
                 input_size: tuple[int, int], foreground_labels=(MENISCUS_LABEL,)):
        self.cfg = PreprocessConfig(target_size=input_size)
        full = PairSlicesDataset(pairs=pairs, slice_axis=2, top_k=top_k,
                                 foreground_labels=foreground_labels)
        self.items = [it for it in full if it.volume_index is not None and True]
        ds = full
        kept = []
        for it in ds:
            src = os.path.basename(it.source_image)
            from nexora.data.splitting import extract_subject_id
            sid = extract_subject_id(src)
            if sid in subjects:
                kept.append(it)
        self.items = kept

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int):
        out = preprocess_slice(self.items[idx], self.cfg)
        return out.image, out.mask


def evaluate(model, loader, device) -> dict:
    model.eval()
    totals = {"loss": 0.0, "dice": 0.0, "iou": 0.0}
    n = 0
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            probs = torch.sigmoid(model(x))
            bs = x.shape[0]
            totals["loss"] += dice_loss(probs, y).item() * bs
            totals["dice"] += dice_score(probs, y).item() * bs
            totals["iou"] += iou_score(probs, y).item() * bs
            n += bs
    return {k: v / max(n, 1) for k, v in totals.items()}


def train(args) -> dict:
    set_seeds(args.seed)
    device = get_device()
    print(f"device    : {device}")
    print(f"torch     : {torch.__version__}")

    partitions = load_partitions()
    pairs, data_desc = resolve_pairs(None, args.seed)
    print(f"data      : {data_desc}")

    train_ds = SliceDataset(pairs, partitions["train"], args.max_slices_per_volume, args.input_size)
    val_ds = SliceDataset(pairs, partitions["val"], args.max_slices_per_volume, args.input_size)
    test_ds = SliceDataset(pairs, partitions["test"], args.max_slices_per_volume, args.input_size)
    print(f"slices    : train={len(train_ds)}  val={len(val_ds)}  test={len(test_ds)}")

    g = torch.Generator().manual_seed(args.seed)
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                          num_workers=args.num_workers, generator=g)
    val_dl = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                        num_workers=args.num_workers)

    model = UNet2D(in_channels=1, out_channels=1, base=args.base,
                   depth=4, input_size=args.input_size).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    history, best_dice = [], -1.0
    t0 = time.time()
    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        seen = 0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            probs = torch.sigmoid(model(x))
            loss = dice_loss(probs, y)
            loss.backward()
            opt.step()
            running += loss.item() * x.shape[0]
            seen += x.shape[0]

        train_loss = running / max(seen, 1)
        val = evaluate(model, val_dl, device)
        history.append({
            "epoch": epoch, "train_loss": train_loss,
            "val_loss": val["loss"], "val_dice": val["dice"], "val_iou": val["iou"],
        })
        marker = ""
        if val["dice"] > best_dice:
            best_dice = val["dice"]
            os.makedirs(os.path.dirname(BEST_CKPT), exist_ok=True)
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "input_size": list(args.input_size),
                "base": args.base,
                "depth": 4,
                "val_dice": best_dice,
                "val_iou": val["iou"],
                "data_source": data_desc,
            }, BEST_CKPT)
            marker = "  <- best"

        print(f"Epoch {epoch:03d} | TrainLoss {train_loss:.4f} | ValLoss {val['loss']:.4f} "
              f"| ValDice {val['dice']:.4f} | ValIoU {val['iou']:.4f}{marker}")

    elapsed = time.time() - t0
    summary = {
        "config": vars(args),
        "data_source": data_desc,
        "device": str(device),
        "elapsed_seconds": round(elapsed, 2),
        "best_val_dice": best_dice,
        "history": history,
        "caveat": ("metrics measured on SYNTHETIC fixtures; they verify that "
                   "learning mechanics work and say NOTHING about real "
                   "meniscus segmentation performance"),
    }
    os.makedirs(os.path.dirname(HISTORY_JSON), exist_ok=True)
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nsaved checkpoint : {BEST_CKPT}")
    print(f"saved history    : {HISTORY_JSON}")
    print(f"best val Dice    : {best_dice:.4f}   ({elapsed:.1f}s total)")
    return summary


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Phase 7 meniscus U-Net training")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--base", type=int, default=16)
    ap.add_argument("--input-size", type=int, nargs=2, default=[256, 256])
    ap.add_argument("--max-slices-per-volume", type=int, default=3)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    return ap


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.input_size = tuple(args.input_size)
    train(args)
