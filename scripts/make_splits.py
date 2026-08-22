"""Phase 4 CLI: build ml/training/splits.json from discovered pairs.

Prefers real data under data/raw (root/images + root/masks). If absent,
falls back to SYNTHETIC fixtures and stamps the manifest accordingly -
regenerate this file with the same command once real data is placed.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.join(_ROOT, "tests"))

from nexora.data import discover_pairs  # noqa: E402
from nexora.data.splitting import build_manifest, print_summary, save_splits, verify_splits  # noqa: E402

from fixtures import write_fixtures  # noqa: E402

SPLITS_PATH = os.path.join(_ROOT, "ml", "training", "splits.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--force-synthetic", action="store_true")
    args = ap.parse_args()

    real_root = os.path.join(_ROOT, "data", "raw")
    pairs = discover_pairs(real_root) if not args.force_synthetic else []

    if pairs:
        source = f"real:{real_root}"
    else:
        tmp = tempfile.mkdtemp(prefix="nexora_phase4_")
        write_fixtures(tmp, n_volumes=9, seed=args.seed)
        pairs = discover_pairs(tmp)
        source = "synthetic_fixtures_test_only"

    manifest = build_manifest(pairs, seed=args.seed, source=source)
    counts = verify_splits(manifest)
    save_splits(manifest, SPLITS_PATH)

    print(f"data source : {source}")
    print(f"splits file : {SPLITS_PATH}\n")
    print_summary(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
