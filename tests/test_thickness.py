"""Phase 10: unit tests for medial meniscus thickness measurement.

Run with:
    python tests/test_thickness.py

Each test function uses a synthetic mask with KNOWN geometry so that the
expected answer can be derived analytically without running any model code.

Test catalogue
--------------
test_uniform_cube_no_spacing        uniform 4×4×12 cube, no spacing
test_uniform_cube_with_spacing      uniform 4×4×12 cube, with spacing
test_tapered_mask_thirds_partition  tapered slab: exact per-region thickness
test_single_column_mask             1 voxel wide column
test_empty_mask                     all-zero mask
test_two_active_slices              insufficient slices edge case
test_missing_spacing_fallback       None spacing → voxels
test_invalid_spacing_fallback       non-finite spacing → voxels
test_wrong_ndim_raises              2-D mask raises ValueError
test_wrong_slice_axis_raises        slice_axis=5 raises ValueError
test_irregular_mask_no_crash        sparse irregular mask completes
test_slice_axis_0                   slice_axis=0 re-orientation
test_slice_axis_1                   slice_axis=1 re-orientation
test_measure_from_inference_result  wrapper with binary mask + spacing
test_measure_from_inference_result_label_map  wrapper with label map
test_large_uniform_mask_mm_units    large uniform mask, check mm conversion
test_result_schema                  output dict has exactly required keys
"""

from __future__ import annotations

import math
import os
import sys

# --- path setup (mirrors test_metrics.py) -----------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np  # noqa: E402

from ml.analysis.thickness import (  # noqa: E402
    _max_run_length_1d,
    _partition_active_slices,
    _slice_thickness_voxels,
    measure_from_inference_result,
    measure_thickness,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PASS = []
_FAIL = []


def _check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        _PASS.append(name)
        print(f"  PASS  {name}")
    else:
        _FAIL.append(name)
        msg = f"  FAIL  {name}"
        if detail:
            msg += f"  [{detail}]"
        print(msg)


def _near(a: float | None, b: float, tol: float = 1e-6) -> bool:
    if a is None:
        return False
    return abs(a - b) <= tol


def _uniform_cube(height: int, width: int, depth: int) -> np.ndarray:
    """Return an all-ones uint8 mask of shape (height, width, depth)."""
    return np.ones((height, width, depth), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Internal helper tests (whitebox)
# ---------------------------------------------------------------------------

def test_max_run_length_1d() -> None:
    """_max_run_length_1d returns the length of the longest run of 1s."""
    # simple run
    _check("run_1d_simple",
           _max_run_length_1d(np.array([0, 1, 1, 1, 0])) == 3)
    # all zeros
    _check("run_1d_all_zeros",
           _max_run_length_1d(np.array([0, 0, 0])) == 0)
    # all ones
    _check("run_1d_all_ones",
           _max_run_length_1d(np.array([1, 1, 1, 1])) == 4)
    # multiple runs – longest wins
    _check("run_1d_two_runs",
           _max_run_length_1d(np.array([1, 1, 0, 1, 1, 1, 0, 1])) == 3)
    # single element
    _check("run_1d_single_one",
           _max_run_length_1d(np.array([1])) == 1)
    _check("run_1d_single_zero",
           _max_run_length_1d(np.array([0])) == 0)


def test_slice_thickness_voxels() -> None:
    """_slice_thickness_voxels returns median of per-column run-lengths."""
    # 4 rows, 3 cols, all ones → each column has run=4 → median=4
    sl_all = np.ones((4, 3), dtype=bool)
    _check("slice_all_ones",
           _near(_slice_thickness_voxels(sl_all), 4.0))

    # 4 rows, 3 cols, only cols 0 and 2 have runs of 3 and 2 respectively
    sl_mixed = np.zeros((4, 3), dtype=bool)
    sl_mixed[0:3, 0] = True   # col 0 → run=3
    sl_mixed[0:2, 2] = True   # col 2 → run=2
    # col 1 empty → ignored; median([3, 2]) = 2.5
    _check("slice_mixed_cols",
           _near(_slice_thickness_voxels(sl_mixed), 2.5))

    # all zeros → None
    _check("slice_all_zeros",
           _slice_thickness_voxels(np.zeros((4, 3), dtype=bool)) is None)


def test_partition_active_slices() -> None:
    """Active slices are split into three groups by _partition_active_slices."""
    idxs = list(range(9))   # 0..8
    ant, mid, post = _partition_active_slices(idxs)
    _check("partition_9_anterior",  ant == [0, 1, 2])
    _check("partition_9_middle",    mid == [3, 4, 5])
    _check("partition_9_posterior", post == [6, 7, 8])

    # 10 elements: thirds are 3,3,4
    idxs10 = list(range(10))
    a10, m10, p10 = _partition_active_slices(idxs10)
    _check("partition_10_sizes",
           len(a10) == 3 and len(m10) == 3 and len(p10) == 4)

    # 3 elements: one each
    a3, m3, p3 = _partition_active_slices([0, 1, 2])
    _check("partition_3_one_each",
           len(a3) == 1 and len(m3) == 1 and len(p3) == 1)


# ---------------------------------------------------------------------------
# Public API tests (blackbox, synthetic cubes)
# ---------------------------------------------------------------------------

def test_uniform_cube_no_spacing() -> None:
    """Uniform 4×6×12 cube without spacing → results in voxels.

    The cube is foreground everywhere:
        - All 12 Z-slices are active.
        - Anterior = slices 0..3, middle = 4..7, posterior = 8..11.
        - Every 2-D slice has shape (4, 6) with all ones.
        - Each column has a run-length of 4 (the full row dimension).
        - _slice_thickness_voxels = median([4,4,4,4,4,4]) = 4.0
        - region thickness = median([4.0, 4.0, 4.0, 4.0]) = 4.0 voxels.
    """
    mask = _uniform_cube(4, 6, 12)
    result = measure_thickness(mask, spacing_mm=None, slice_axis=2)

    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"uniform_no_spacing_{region}_status",
               r["status"] == "ok",
               f"got status={r['status']!r}")
        _check(f"uniform_no_spacing_{region}_unit",
               r["unit"] == "voxels")
        _check(f"uniform_no_spacing_{region}_value",
               _near(r["value"], 4.0),
               f"got {r['value']}")


def test_uniform_cube_with_spacing() -> None:
    """Uniform 4×6×12 cube WITH spacing (0.5, 0.5, 1.0) mm.

    thickness_voxels = 4.0  (row-run-length = 4)
    row_mm = spacing_mm[0] = 0.5
    expected mm = 4.0 × 0.5 = 2.0 mm
    """
    mask = _uniform_cube(4, 6, 12)
    spacing = (0.5, 0.5, 1.0)
    result = measure_thickness(mask, spacing_mm=spacing, slice_axis=2)

    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"uniform_with_spacing_{region}_unit",
               r["unit"] == "mm")
        _check(f"uniform_with_spacing_{region}_value",
               _near(r["value"], 2.0),
               f"got {r['value']}")


def test_tapered_mask_thirds_partition() -> None:
    """Tapered slab: different heights in each third, exact expected values.

    Mask shape (R=10, C=5, Z=9).  Axis-2 is slice axis.
    Slices partitioned: anterior=[0,1,2], middle=[3,4,5], posterior=[6,7,8].

    Anterior slices (z=0,1,2): foreground rows 0..4 (5 rows).
        All 5 columns filled → run-length per column = 5.
        _slice_thickness = 5.0 for each z → region = 5.0 voxels.

    Middle slices (z=3,4,5): foreground rows 0..6 (7 rows).
        region = 7.0 voxels.

    Posterior slices (z=6,7,8): foreground rows 0..2 (3 rows).
        region = 3.0 voxels.
    """
    mask = np.zeros((10, 5, 9), dtype=np.uint8)
    mask[0:5, :, 0:3] = 1   # anterior   – 5 rows
    mask[0:7, :, 3:6] = 1   # middle     – 7 rows
    mask[0:3, :, 6:9] = 1   # posterior  – 3 rows

    result = measure_thickness(mask, spacing_mm=None, slice_axis=2)

    _check("tapered_anterior_value",
           _near(result["anterior"]["value"], 5.0),
           f"got {result['anterior']['value']}")
    _check("tapered_middle_value",
           _near(result["middle"]["value"], 7.0),
           f"got {result['middle']['value']}")
    _check("tapered_posterior_value",
           _near(result["posterior"]["value"], 3.0),
           f"got {result['posterior']['value']}")


def test_single_column_mask() -> None:
    """Mask with a single foreground column (C=1), thickness = row count.

    Shape (6, 1, 9).  All foreground.  Row run-length = 6.  No spacing.
    """
    mask = _uniform_cube(6, 1, 9)
    result = measure_thickness(mask, spacing_mm=None, slice_axis=2)
    for region in ("anterior", "middle", "posterior"):
        _check(f"single_col_{region}",
               _near(result[region]["value"], 6.0),
               f"got {result[region]['value']}")


def test_empty_mask() -> None:
    """All-zero mask → status 'empty_mask', value None."""
    mask = np.zeros((10, 10, 20), dtype=np.uint8)
    result = measure_thickness(mask, spacing_mm=None, slice_axis=2)
    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"empty_mask_{region}_status",
               r["status"] == "empty_mask",
               f"got {r['status']!r}")
        _check(f"empty_mask_{region}_value",
               r["value"] is None)


def test_two_active_slices() -> None:
    """Mask with only 2 active slices → 'insufficient_slices' for all."""
    mask = np.zeros((8, 8, 10), dtype=np.uint8)
    mask[2:5, 2:5, 3] = 1
    mask[2:5, 2:5, 7] = 1  # only slices 3 and 7 are active

    result = measure_thickness(mask, spacing_mm=None, slice_axis=2)
    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"two_slices_{region}_status",
               r["status"] == "insufficient_slices",
               f"got {r['status']!r}")
        _check(f"two_slices_{region}_value",
               r["value"] is None)


def test_missing_spacing_fallback() -> None:
    """None spacing → unit is 'voxels', value is still computed."""
    mask = _uniform_cube(5, 5, 9)
    result = measure_thickness(mask, spacing_mm=None, slice_axis=2)
    for region in ("anterior", "middle", "posterior"):
        _check(f"no_spacing_{region}_unit",
               result[region]["unit"] == "voxels")
        _check(f"no_spacing_{region}_value_not_none",
               result[region]["value"] is not None)


def test_invalid_spacing_fallback() -> None:
    """Non-finite or zero spacing components → falls back to voxels."""
    mask = _uniform_cube(5, 5, 9)

    for bad_spacing, label in [
        ((0.0, 0.5, 1.0), "zero_row"),
        ((float("nan"), 0.5, 1.0), "nan_row"),
        ((float("inf"), 0.5, 1.0), "inf_row"),
        ((-1.0, 0.5, 1.0), "neg_row"),
    ]:
        r = measure_thickness(mask, spacing_mm=bad_spacing, slice_axis=2)
        _check(f"bad_spacing_{label}_unit",
               r["anterior"]["unit"] == "voxels",
               f"got {r['anterior']['unit']!r}")


def test_wrong_ndim_raises() -> None:
    """2-D mask raises ValueError."""
    mask_2d = np.ones((10, 10), dtype=np.uint8)
    raised = False
    try:
        measure_thickness(mask_2d)
    except ValueError:
        raised = True
    _check("wrong_ndim_raises", raised)


def test_wrong_slice_axis_raises() -> None:
    """slice_axis=5 raises ValueError."""
    mask = _uniform_cube(4, 4, 9)
    raised = False
    try:
        measure_thickness(mask, slice_axis=5)
    except ValueError:
        raised = True
    _check("wrong_slice_axis_raises", raised)


def test_irregular_mask_no_crash() -> None:
    """Sparse irregular mask (random voxels) completes without error.

    No numerical assertion — only checks it returns the expected schema.
    """
    rng = np.random.default_rng(0)
    mask = (rng.random((20, 20, 15)) > 0.85).astype(np.uint8)

    try:
        result = measure_thickness(mask, spacing_mm=(0.3, 0.3, 0.7),
                                   slice_axis=2)
        ok = all(k in result for k in ("anterior", "middle", "posterior"))
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"    exception: {exc}")
    _check("irregular_no_crash", ok)


def test_slice_axis_0() -> None:
    """slice_axis=0 is handled correctly.

    Mask shape (9, 6, 4) with slice_axis=0.
    After moveaxis(mask, 0, 2) → shape (6, 4, 9).
    Row dimension = 6, all foreground → expected thickness = 6.0 voxels.
    """
    mask = np.ones((9, 6, 4), dtype=np.uint8)  # (Z, R, C) layout
    result = measure_thickness(mask, spacing_mm=None, slice_axis=0)
    for region in ("anterior", "middle", "posterior"):
        _check(f"slice_axis0_{region}",
               _near(result[region]["value"], 6.0),
               f"got {result[region]['value']}")


def test_slice_axis_1() -> None:
    """slice_axis=1 is handled correctly.

    Mask shape (6, 9, 4) with slice_axis=1.
    After moveaxis(mask, 1, 2) → shape (6, 4, 9).
    Row dimension = 6, all foreground → expected thickness = 6.0 voxels.
    """
    mask = np.ones((6, 9, 4), dtype=np.uint8)  # (R, Z, C) layout
    result = measure_thickness(mask, spacing_mm=None, slice_axis=1)
    for region in ("anterior", "middle", "posterior"):
        _check(f"slice_axis1_{region}",
               _near(result[region]["value"], 6.0),
               f"got {result[region]['value']}")


def test_measure_from_inference_result() -> None:
    """measure_from_inference_result works with a binary mask + spacing."""
    mask = _uniform_cube(4, 6, 12)
    inference_result = {"mask": mask, "spacing": (0.5, 0.5, 1.0)}
    result = measure_from_inference_result(inference_result,
                                           foreground_labels=None,
                                           slice_axis=2)
    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"from_inference_{region}_unit", r["unit"] == "mm")
        _check(f"from_inference_{region}_value",
               _near(r["value"], 2.0),
               f"got {r['value']}")


def test_measure_from_inference_result_label_map() -> None:
    """measure_from_inference_result extracts foreground by label index.

    Mask contains labels {0, 3, 7}.  foreground_labels=(7,) should give
    the same result as a binary mask with only the label-7 voxels.
    """
    # Build a label mask: label 7 fills rows 0..3 (4 rows), all cols, all z.
    # Label 3 fills rows 5..7 (3 rows).  Label 7 row-thickness = 4.
    label_mask = np.zeros((8, 5, 9), dtype=np.uint8)
    label_mask[0:4, :, :] = 7
    label_mask[5:8, :, :] = 3

    inference_result = {"mask": label_mask, "spacing": (1.0, 1.0, 1.0)}
    result = measure_from_inference_result(
        inference_result, foreground_labels=(7,), slice_axis=2
    )
    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"label_map_{region}_value",
               _near(r["value"], 4.0),
               f"got {r['value']}")
        _check(f"label_map_{region}_unit", r["unit"] == "mm")


def test_large_uniform_mask_mm_units() -> None:
    """Large uniform block: verify mm conversion with a round number.

    Shape (10, 8, 30).  Row dimension = 10 voxels.
    spacing_mm = (0.36, 0.36, 0.70) (matches fixture spacing).
    Expected thickness = 10 × 0.36 = 3.6 mm.
    """
    mask = _uniform_cube(10, 8, 30)
    result = measure_thickness(mask, spacing_mm=(0.36, 0.36, 0.70),
                               slice_axis=2)
    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"large_mm_{region}_unit", r["unit"] == "mm")
        _check(f"large_mm_{region}_value",
               _near(r["value"], 3.6, tol=1e-4),
               f"got {r['value']}")


def test_result_schema() -> None:
    """Every region dict contains exactly the required keys with correct types."""
    mask = _uniform_cube(5, 5, 9)
    result = measure_thickness(mask, spacing_mm=(0.5, 0.5, 1.0),
                               slice_axis=2)
    required_keys = {"value", "unit", "method", "status"}
    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"schema_{region}_keys",
               set(r.keys()) == required_keys,
               f"got {set(r.keys())}")
        _check(f"schema_{region}_value_type",
               r["value"] is None or isinstance(r["value"], float))
        _check(f"schema_{region}_unit_str",
               isinstance(r["unit"], str))
        _check(f"schema_{region}_method_str",
               isinstance(r["method"], str))
        _check(f"schema_{region}_status_str",
               isinstance(r["status"], str))


# ---------------------------------------------------------------------------
# Integration smoke test using the phantom fixture
# ---------------------------------------------------------------------------

def test_phantom_fixture_smoke() -> None:
    """Phantom fixture produces finite positive thickness measurements.

    This is a smoke test: we do not assert exact values because they depend
    on wedge geometry details.  We only verify:
    - All three regions return status "ok".
    - Values are positive finite numbers.
    - Units are "mm" (fixture provides valid spacing).
    """
    # Import here so a missing nibabel does not kill the other tests.
    try:
        from tests.fixtures import (  # type: ignore[import]
            MENISCUS_LABEL,
            SPACING_MM,
            VOL_SHAPE,
            build_phantom,
        )
    except ImportError:
        try:
            sys.path.insert(0, os.path.join(_ROOT, "tests"))
            from fixtures import (  # type: ignore[import]  # noqa: PLC0415
                MENISCUS_LABEL,
                SPACING_MM,
                VOL_SHAPE,
                build_phantom,
            )
        except ImportError:
            print("  SKIP  phantom_fixture_smoke (fixtures not importable)")
            return

    _, labels = build_phantom(seed=0)

    # Binarise with the known foreground label
    binary = (labels == MENISCUS_LABEL).astype(np.uint8)

    result = measure_thickness(binary, spacing_mm=SPACING_MM, slice_axis=2)

    for region in ("anterior", "middle", "posterior"):
        r = result[region]
        _check(f"phantom_{region}_status",
               r["status"] == "ok",
               f"got {r['status']!r}")
        _check(f"phantom_{region}_unit",
               r["unit"] == "mm")
        ok_value = (
            r["value"] is not None
            and math.isfinite(r["value"])
            and r["value"] > 0.0
        )
        _check(f"phantom_{region}_positive_finite",
               ok_value,
               f"got {r['value']}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    test_functions = [
        test_max_run_length_1d,
        test_slice_thickness_voxels,
        test_partition_active_slices,
        test_uniform_cube_no_spacing,
        test_uniform_cube_with_spacing,
        test_tapered_mask_thirds_partition,
        test_single_column_mask,
        test_empty_mask,
        test_two_active_slices,
        test_missing_spacing_fallback,
        test_invalid_spacing_fallback,
        test_wrong_ndim_raises,
        test_wrong_slice_axis_raises,
        test_irregular_mask_no_crash,
        test_slice_axis_0,
        test_slice_axis_1,
        test_measure_from_inference_result,
        test_measure_from_inference_result_label_map,
        test_large_uniform_mask_mm_units,
        test_result_schema,
        test_phantom_fixture_smoke,
    ]

    for fn in test_functions:
        print(f"\n[{fn.__name__}]")
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _FAIL.append(fn.__name__)
            print(f"  ERROR  {fn.__name__}: {exc}")

    total = len(_PASS) + len(_FAIL)
    print(f"\n{'=' * 60}")
    print(f"Results: {len(_PASS)}/{total} passed, {len(_FAIL)} failed")
    if _FAIL:
        print("Failed:")
        for name in _FAIL:
            print(f"  - {name}")
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
