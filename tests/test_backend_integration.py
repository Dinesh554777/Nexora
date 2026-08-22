"""Backend integration test for analyze_meniscus_for_backend().

Verifies the complete pipeline on a real fixture MRI:

  1. MRI loads
  2. ML model loads
  3. Inference runs (U-Net forward pass)
  4. Segmentation is produced (non-empty binary mask)
  5. Measurements are produced (anterior / middle / posterior)
  6. Overlay is produced (PNG written to disk)
  7. Returned result is JSON-serialisable

Run:
    python tests/test_backend_integration.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT,
           os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PASS_LIST: list[str] = []
FAIL_LIST: list[str] = []


def _ok(name: str) -> None:
    PASS_LIST.append(name)
    print(f"  PASS  {name}")


def _fail(name: str, detail: str = "") -> None:
    FAIL_LIST.append(name)
    print(f"  FAIL  {name}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"        {line}")


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        _ok(name)
    else:
        _fail(name, detail)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_IMG = os.path.join(_ROOT, "data", "fixtures_tmp", "images", "phantom_000.nii.gz")
_CKPT = os.path.join(_ROOT, "checkpoints", "best_model.pth")
_OUT  = os.path.join(_ROOT, "outputs", "backend_integration")


# ---------------------------------------------------------------------------
# Test body
# ---------------------------------------------------------------------------

def run_integration_test() -> dict | None:
    """Run analyze_meniscus_for_backend on phantom_000 and return the result."""

    # --- guard: fixture image must exist ----------------------------------
    if not os.path.isfile(_IMG):
        _fail("fixture image exists", f"not found: {_IMG}")
        return None
    _ok("fixture image exists")

    # --- guard: checkpoint must exist -------------------------------------
    if not os.path.isfile(_CKPT):
        _fail("checkpoint exists", f"not found: {_CKPT}")
        return None
    _ok("checkpoint exists")

    # --- import entry point -----------------------------------------------
    try:
        from ml.pipeline import analyze_meniscus_for_backend, get_predictor
        _ok("import analyze_meniscus_for_backend")
    except Exception:
        _fail("import analyze_meniscus_for_backend", traceback.format_exc())
        return None

    # --- call the function ------------------------------------------------
    result: dict | None = None
    try:
        predictor = get_predictor(_CKPT)          # cached model load
        result = analyze_meniscus_for_backend(
            _IMG,
            out_dir=_OUT,
            predictor=predictor,
        )
        _ok("pipeline call completed without exception")
    except Exception:
        _fail("pipeline call completed without exception", traceback.format_exc())
        return None

    return result


def verify_result(result: dict) -> None:
    """Assert every contract point against the returned dict."""

    # 1. MRI loads — inferred: pipeline returned a result at all
    _check("1. MRI loads",
           result.get("status") != "error",
           result.get("error", ""))

    # 2. ML model loads — model_version present and non-empty
    mv = result.get("model_version", "")
    _check("2. ML model loads",
           isinstance(mv, str) and len(mv) > 0,
           f"model_version={mv!r}")

    # 3. Inference runs — status is success or partial (not error)
    _check("3. Inference runs",
           result.get("status") in ("success", "partial"),
           f"status={result.get('status')!r}")

    # 4. Segmentation produced — mask_path points to an existing file
    seg = result.get("segmentation", {})
    mp  = seg.get("mask_path")
    _check("4. Segmentation produced (mask_path set)",
           isinstance(mp, str) and len(mp) > 0,
           f"mask_path={mp!r}")
    if mp:
        _check("4. Segmentation produced (mask file exists)",
               os.path.isfile(mp),
               f"not found: {mp}")

    # 5. Measurements produced — all three regions present with numeric values
    meas = result.get("measurements", {})
    _check("5. Measurements keys present",
           set(meas.keys()) == {"anterior", "middle", "posterior"},
           f"keys={set(meas.keys())}")
    for region in ("anterior", "middle", "posterior"):
        entry = meas.get(region, {})
        val   = entry.get("value")
        unit  = entry.get("unit")
        _check(f"5. {region} value is numeric",
               isinstance(val, (int, float)) and val is not None,
               f"value={val!r}")
        _check(f"5. {region} unit is mm or voxels",
               unit in ("mm", "voxels"),
               f"unit={unit!r}")

    # 6. Overlay produced — overlay_path points to an existing PNG
    viz = result.get("visualization", {})
    op  = viz.get("overlay_path")
    _check("6. Overlay path set",
           isinstance(op, str) and op.lower().endswith(".png"),
           f"overlay_path={op!r}")
    if op:
        _check("6. Overlay PNG exists on disk",
               os.path.isfile(op),
               f"not found: {op}")
        if os.path.isfile(op):
            size = os.path.getsize(op)
            _check("6. Overlay PNG non-trivial size",
                   size > 10_000,
                   f"{size} bytes")

    # 7. JSON-serialisable — round-trip through json.dumps / json.loads
    try:
        blob   = json.dumps(result)
        loaded = json.loads(blob)
        _check("7. Result is JSON-serialisable", True)
        _check("7. Round-trip preserves top-level keys",
               set(loaded.keys()) == set(result.keys()))
    except (TypeError, ValueError) as exc:
        _check("7. Result is JSON-serialisable", False, str(exc))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 62)
    print("Backend Integration Test — analyze_meniscus_for_backend()")
    print("=" * 62)
    print(f"  image      : {_IMG}")
    print(f"  checkpoint : {_CKPT}")
    print(f"  output dir : {_OUT}")

    result = run_integration_test()

    if result is not None:
        verify_result(result)

    total = len(PASS_LIST) + len(FAIL_LIST)
    print(f"\n{'=' * 62}")
    print(f"Results: {len(PASS_LIST)}/{total} passed,  {len(FAIL_LIST)} failed")

    if FAIL_LIST:
        print("\nFailed:")
        for name in FAIL_LIST:
            print(f"  FAIL  {name}")
        return 1

    # --- print the example output ----------------------------------------
    print("\n--- Example output ---")
    if result is not None:
        # Show the clean backend schema only (omit internal details)
        preview = {
            "status":        result["status"],
            "model_version": result["model_version"],
            "measurements": {
                r: {"value": result["measurements"][r]["value"],
                    "unit":  result["measurements"][r]["unit"]}
                for r in ("anterior", "middle", "posterior")
            },
            "segmentation":  result["segmentation"],
            "visualization": result["visualization"],
        }
        print(json.dumps(preview, indent=2))

    print("\nAll integration tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
