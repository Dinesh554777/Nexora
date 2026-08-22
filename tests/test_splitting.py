"""Phase 4 verification suite: patient-level splitting.

Run:  python tests/test_splitting.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexora.data.splitting import (  # noqa: E402
    build_manifest,
    extract_subject_id,
    load_splits,
    split_subjects,
    verify_splits,
)

from fixtures import write_fixtures  # noqa: E402


def test_subject_id_parsing():
    cases = {
        "9000099_LEFT-label": "9000099",
        "9000099_RIGHT.nii.gz": "9000099",
        "12345_L": "12345",
        "777_r_seg": "777",
        "phantom_000": "phantom_000",
        "sub-12_T2": "sub-12_T2",
    }
    for raw, want in cases.items():
        got = extract_subject_id(raw)
        assert got == want, f"{raw}: {got} != {want}"


def _fake_pairs(subjects, knee_tags=("LEFT", "RIGHT")):
    pairs = []
    for s in subjects:
        for k in knee_tags:
            pairs.append((f"/x/{s}_{k}-img", f"/x/{s}_{k}-label"))
    return pairs


def test_no_leakage_and_exhaustive():
    subjects = [f"S{i:03d}" for i in range(100)]
    manifest = build_manifest(_fake_pairs(subjects), seed=42)

    names = ("train", "val", "test")
    sets = {n: set(manifest["splits"][n]["subjects"]) for n in names}
    for i in range(3):
        for j in range(i + 1, 3):
            assert not (sets[names[i]] & sets[names[j]]), "subject leaked across splits"
    union = set().union(*sets.values())
    assert union == set(subjects), "some subject missing from all splits"

    verify_splits(manifest)


def test_ratio_approx_70_15_15():
    subjects = [f"P{i:04d}" for i in range(200)]
    parts = split_subjects(subjects, seed=7)
    n = len(subjects)
    assert abs(len(parts["train"]) - 0.70 * n) <= max(1, 0.02 * n)
    assert abs(len(parts["val"]) - 0.15 * n) <= max(1, 0.02 * n)
    assert abs(len(parts["test"]) - 0.15 * n) <= max(1, 0.02 * n)
    assert all(len(parts[k]) >= 1 for k in parts)


def test_slices_of_same_stay_together():
    subjects = [f"Q{i}" for i in range(30)]
    manifest = build_manifest(_fake_pairs(subjects), seed=3)
    owner = {}
    for name in ("train", "val", "test"):
        for s in manifest["splits"][name]["samples"]:
            sid = s["subject_id"]
            assert owner.setdefault(sid, name) == name, (
                f"sample of subject {sid} appears in two partitions"
            )


def test_determinism_and_json_roundtrip():
    subjects = [f"D{i:03d}" for i in range(40)]
    m1 = build_manifest(_fake_pairs(subjects), seed=11)
    m2 = build_manifest(_fake_pairs(subjects), seed=11)
    assert m1["splits"] == m2["splits"], "same seed produced different split"

    m3 = build_manifest(_fake_pairs(subjects), seed=12)
    assert m1["splits"] != m3["splits"], "different seed produced identical split"

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "splits.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m1, f)
        loaded = load_splits(p)
        verify_splits(loaded)
        assert loaded["splits"] == m1["splits"]


def test_small_dataset_minimum_partitions():
    subjects = ["A", "B", "C"]
    parts = split_subjects(subjects, seed=0)
    assert all(len(parts[k]) == 1 for k in ("train", "val", "test"))
    try:
        split_subjects(["only", "two"])
        raise AssertionError("should reject <3 subjects")
    except ValueError:
        pass


def main() -> int:
    tests = [
        ("subject_ids", lambda _: test_subject_id_parsing()),
        ("no_leakage", lambda _: test_no_leakage_and_exhaustive()),
        ("ratios", lambda _: test_ratio_approx_70_15_15()),
        ("grouped", lambda _: test_slices_of_same_stay_together()),
        ("deterministic", lambda _: test_determinism_and_json_roundtrip()),
        ("small_n", lambda _: test_small_dataset_minimum_partitions()),
    ]
    failures = []
    for name, fn in tests:
        try:
            fn(None)
            print(f"PASS  {name}")
        except Exception:
            failures.append(name)
            print(f"FAIL  {name}\n{traceback.format_exc()}")

    print("\n" + ("ALL PHASE 4 SPLITTING TESTS PASSED" if not failures
                  else f"{len(failures)} TEST(S) FAILED: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
