"""Phase 14: final ML testing and stabilization.

Aggregates ALL test suites and adds integration + failure-case coverage.

Sections
--------
1  Dataset loader tests       (Phase 3 loader)
2  Preprocessing tests        (Phase 3 pipeline)
3  U-Net forward test         (Phase 5 model)
4  Loss tests                 (Phase 6 dice_loss)
5  Metric tests               (Phase 6 scores)
6  Inference test             (Phase 9 MeniscusPredictor)
7  Measurement tests          (Phase 10 thickness)
8  Visualization test         (Phase 11 overlay)
9  Full pipeline test         (Phase 12 analyze_meniscus)
10 Failure cases              (invalid/missing/empty/corrupted inputs)

Run:
    python tests/test_phase14.py
"""

from __future__ import annotations

import math
import os
import sys
import tempfile
import traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "src"), _ROOT, os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import nibabel as nib
import numpy as np
import torch

from fixtures import MENISCUS_LABEL, SPACING_MM, VOL_SHAPE, build_phantom, write_fixtures

PASS_LIST: list[str] = []
FAIL_LIST: list[str] = []


def _ok(name: str) -> None:
    PASS_LIST.append(name)
    print(f"  PASS  {name}")


def _fail(name: str, detail: str = "") -> None:
    FAIL_LIST.append(name)
    msg = f"  FAIL  {name}"
    if detail:
        msg += f"\n        {detail.strip()}"
    print(msg)


def _run(name: str, fn) -> None:
    try:
        fn()
        _ok(name)
    except Exception:
        _fail(name, traceback.format_exc())


# ============================================================
# Section 1 – Dataset loader
# ============================================================

def _s1_loader_shapes(tmp: str) -> None:
    from nexora.data import load_volume_pair, discover_pairs

    pairs = discover_pairs(tmp)
    assert len(pairs) >= 1, "no pairs found"
    vp = load_volume_pair(*pairs[0], foreground_labels=(MENISCUS_LABEL,))
    assert vp.image.shape == VOL_SHAPE
    assert vp.mask.dtype == np.uint8
    assert vp.image.dtype == np.float32
    assert set(np.unique(vp.mask).tolist()).issubset({0, 1})
    got = tuple(round(s, 4) for s in vp.spacing_mm)
    want = tuple(round(s, 4) for s in SPACING_MM)
    assert got == want, f"spacing {got} != {want}"


def _s1_loader_label_selection(tmp: str) -> None:
    """Label-7 voxels become 1; label-3 distractor is dropped."""
    from nexora.data import load_volume_pair, discover_pairs

    vp = load_volume_pair(*discover_pairs(tmp)[0],
                          foreground_labels=(MENISCUS_LABEL,))
    raw = nib.load(discover_pairs(tmp)[0][1]).get_fdata()
    assert not np.any(vp.mask[raw == 3] == 1), \
        "distractor label 3 leaked into binary mask"
    assert np.any(vp.mask == 1), "no foreground voxels selected"


def _s1_slice_extraction(tmp: str) -> None:
    from nexora.data import load_volume_pair, discover_pairs, extract_slices

    vp = load_volume_pair(*discover_pairs(tmp)[0],
                          foreground_labels=(MENISCUS_LABEL,))
    slices = extract_slices(vp, slice_axis=2, top_k=4)
    assert len(slices) == 4
    for sl in slices:
        assert sl.image.shape == sl.mask.shape
        assert sl.image.ndim == 2


def run_section_1(tmp: str) -> None:
    print("\n[1] Dataset loader tests")
    _run("1.1 loader shapes & spacing",  lambda: _s1_loader_shapes(tmp))
    _run("1.2 label selection",          lambda: _s1_loader_label_selection(tmp))
    _run("1.3 slice extraction top-k",   lambda: _s1_slice_extraction(tmp))


# ============================================================
# Section 2 – Preprocessing
# ============================================================

def _s2_normalize() -> None:
    from nexora.preprocessing import normalize_intensity

    rng = np.random.default_rng(0)
    img = rng.normal(100.0, 30.0, (96, 96)).astype(np.float32)
    out = normalize_intensity(img)
    assert out.dtype == np.float32
    assert float(out.min()) >= 0.0 and float(out.max()) <= 1.0
    assert np.array_equal(out, normalize_intensity(img)), "not deterministic"


def _s2_mask_binary_after_resize() -> None:
    from nexora.preprocessing import resize_mask

    rng = np.random.default_rng(1)
    m = (rng.random((96, 96)) > 0.5).astype(np.uint8)
    r = resize_mask(m, (256, 256))
    assert set(np.unique(r).tolist()).issubset({0, 1})


def _s2_preprocess_slice_end_to_end(tmp: str) -> None:
    from nexora.data import load_volume_pair, discover_pairs, extract_slices
    from nexora.preprocessing import PreprocessConfig, preprocess_slice

    vp = load_volume_pair(*discover_pairs(tmp)[0],
                          foreground_labels=(MENISCUS_LABEL,))
    sl = extract_slices(vp, slice_axis=2, top_k=1)[0]
    out = preprocess_slice(sl, PreprocessConfig(target_size=(256, 256)))
    assert out.image.shape == (1, 256, 256)
    assert out.mask.shape  == (1, 256, 256)
    assert torch.isfinite(out.image).all()
    vals = set(torch.unique(out.mask).tolist())
    assert vals.issubset({0.0, 1.0}), f"mask not binary: {vals}"


def _s2_spacing_preserved(tmp: str) -> None:
    from nexora.data import load_volume_pair, discover_pairs, extract_slices
    from nexora.preprocessing import PreprocessConfig, preprocess_slice

    vp = load_volume_pair(*discover_pairs(tmp)[0],
                          foreground_labels=(MENISCUS_LABEL,))
    sl = extract_slices(vp, slice_axis=2, top_k=1)[0]
    out = preprocess_slice(sl, PreprocessConfig())
    assert np.allclose(out.spacing_mm_original, SPACING_MM, atol=1e-5), \
        f"original spacing changed: {out.spacing_mm_original}"


def run_section_2(tmp: str) -> None:
    print("\n[2] Preprocessing tests")
    _run("2.1 normalize intensity",      _s2_normalize)
    _run("2.2 mask binary after resize", _s2_mask_binary_after_resize)
    _run("2.3 preprocess slice e2e",     lambda: _s2_preprocess_slice_end_to_end(tmp))
    _run("2.4 spacing preserved",        lambda: _s2_spacing_preserved(tmp))


# ============================================================
# Section 3 – U-Net forward
# ============================================================

def _s3_forward_shapes() -> None:
    from ml.models import UNet2D

    model = UNet2D(in_channels=1, out_channels=1, base=16, depth=4,
                   input_size=(256, 256))
    model.eval()
    x = torch.zeros(2, 1, 256, 256)
    with torch.no_grad():
        out = model(x)
    assert out.shape == (2, 1, 256, 256), f"wrong shape {tuple(out.shape)}"
    assert torch.isfinite(out).all()


def _s3_sigmoid_range() -> None:
    from ml.models import UNet2D

    model = UNet2D(base=16, depth=4, input_size=(256, 256))
    model.eval()
    with torch.no_grad():
        p = model.predict_proba(torch.randn(1, 1, 256, 256))
    assert 0.0 <= float(p.min()) and float(p.max()) <= 1.0


def _s3_wrong_spatial_size_raises() -> None:
    from ml.models import UNet2D

    model = UNet2D(base=16, input_size=(256, 256))
    raised = False
    try:
        model(torch.randn(1, 1, 128, 128))
    except ValueError:
        raised = True
    assert raised, "expected ValueError for wrong spatial size"


def run_section_3() -> None:
    print("\n[3] U-Net forward tests")
    _run("3.1 output shapes & finite",       _s3_forward_shapes)
    _run("3.2 sigmoid range [0,1]",          _s3_sigmoid_range)
    _run("3.3 wrong spatial size raises",    _s3_wrong_spatial_size_raises)


# ============================================================
# Section 4 – Loss tests
# ============================================================

def _s4_dice_loss_perfect() -> None:
    from ml.metrics import dice_loss

    p = torch.ones(2, 1, 8, 8)
    g = torch.ones(2, 1, 8, 8)
    loss = dice_loss(p, g)
    assert abs(float(loss)) < 1e-4, f"perfect overlap should give ~0 loss, got {loss}"


def _s4_dice_loss_zero_pred() -> None:
    from ml.metrics import dice_loss

    p = torch.zeros(2, 1, 8, 8)
    g = torch.ones(2, 1, 8, 8)
    loss = dice_loss(p, g)
    assert float(loss) > 0.9, f"zero pred vs full GT should give ~1 loss, got {loss}"


def _s4_loss_gradient_flows() -> None:
    from ml.metrics import dice_loss

    # Keep the leaf tensor so .grad is populated after backward()
    logits = torch.randn(2, 1, 8, 8, requires_grad=True)
    p = torch.sigmoid(logits)          # non-leaf – grad lives on logits
    g = (torch.rand(2, 1, 8, 8) > 0.5).float()
    loss = dice_loss(p, g)
    loss.backward()
    assert logits.grad is not None, "no gradient on leaf logit tensor"
    assert torch.isfinite(logits.grad).all()


def _s4_both_empty_safe() -> None:
    from ml.metrics import dice_loss

    p = torch.zeros(1, 1, 8, 8)
    g = torch.zeros(1, 1, 8, 8)
    loss = dice_loss(p, g)
    assert torch.isfinite(loss), "both-empty should not produce NaN/Inf"


def run_section_4() -> None:
    print("\n[4] Loss tests")
    _run("4.1 perfect overlap → loss ≈ 0",  _s4_dice_loss_perfect)
    _run("4.2 zero pred → loss ≈ 1",        _s4_dice_loss_zero_pred)
    _run("4.3 gradients flow",              _s4_loss_gradient_flows)
    _run("4.4 both-empty safe",             _s4_both_empty_safe)


# ============================================================
# Section 5 – Metric tests
# ============================================================

def _s5_dice_score() -> None:
    from ml.metrics import dice_score

    perfect = torch.ones(1, 8, 8)
    assert abs(float(dice_score(perfect, perfect)) - 1.0) < 1e-5
    zeros = torch.zeros(1, 8, 8)
    assert float(dice_score(zeros, perfect)) == 0.0


def _s5_iou_score() -> None:
    from ml.metrics import iou_score

    p = torch.zeros(1, 4, 4)
    p[0, :2, :2] = 1.0
    g = torch.zeros(1, 4, 4)
    g[0, :2, :2] = 1.0
    assert abs(float(iou_score(p, g)) - 1.0) < 1e-5


def _s5_precision_recall() -> None:
    from ml.metrics import precision_score, recall_score

    p = torch.zeros(1, 4, 4)
    p[0, :2, :2] = 1.0            # 4 positives
    g = torch.zeros(1, 4, 4)
    g[0, :3, :3] = 1.0            # 9 GT positives; TP=4, FP=0, FN=5
    prec = float(precision_score(p, g))
    rec  = float(recall_score(p, g))
    assert abs(prec - 1.0) < 1e-5, f"precision {prec}"
    assert abs(rec  - 4/9) < 1e-5, f"recall {rec}"


def _s5_both_empty_convention() -> None:
    from ml.metrics import dice_score, iou_score

    z = torch.zeros(1, 8, 8)
    assert float(dice_score(z, z, empty_value=1.0)) == 1.0
    assert float(iou_score(z, z,  empty_value=1.0)) == 1.0


def run_section_5() -> None:
    print("\n[5] Metric tests")
    _run("5.1 Dice score",              _s5_dice_score)
    _run("5.2 IoU score",               _s5_iou_score)
    _run("5.3 precision & recall",      _s5_precision_recall)
    _run("5.4 both-empty convention",   _s5_both_empty_convention)


# ============================================================
# Section 6 – Inference test
# ============================================================

def _s6_predict_volume(tmp: str) -> None:
    from ml.inference.predict import MeniscusPredictor

    ckpt = os.path.join(_ROOT, "checkpoints", "best_model.pth")
    if not os.path.isfile(ckpt):
        raise FileNotFoundError(f"checkpoint not found: {ckpt}")

    img_path = os.path.join(tmp, "images", "phantom_000.nii.gz")
    pred = MeniscusPredictor(ckpt)
    result = pred.predict_volume(img_path)

    assert result["mask"].dtype  == np.uint8
    assert result["mask"].shape  == VOL_SHAPE
    assert set(np.unique(result["mask"]).tolist()).issubset({0, 1})
    assert result["spacing"] is not None
    assert result["model_version"]
    assert int(result["mask"].sum()) > 0, "model predicts zero foreground on fixture"


def _s6_probability_range(tmp: str) -> None:
    from ml.inference.predict import MeniscusPredictor

    ckpt = os.path.join(_ROOT, "checkpoints", "best_model.pth")
    img_path = os.path.join(tmp, "images", "phantom_000.nii.gz")
    pred = MeniscusPredictor(ckpt)
    result = pred.predict_volume(img_path)
    probs = result["probability"]
    assert probs.min() >= 0.0 and probs.max() <= 1.0, \
        f"probability out of [0,1]: [{probs.min():.4f}, {probs.max():.4f}]"


def run_section_6(tmp: str) -> None:
    print("\n[6] Inference tests")
    _run("6.1 predict_volume output schema",  lambda: _s6_predict_volume(tmp))
    _run("6.2 probability in [0, 1]",         lambda: _s6_probability_range(tmp))


# ============================================================
# Section 7 – Measurement tests
# ============================================================

def _s7_uniform_cube() -> None:
    from ml.analysis.thickness import measure_thickness

    mask = np.ones((4, 6, 12), dtype=np.uint8)
    result = measure_thickness(mask, spacing_mm=(0.5, 0.5, 1.0))
    for r in ("anterior", "middle", "posterior"):
        assert result[r]["status"] == "ok", result[r]["status"]
        assert result[r]["unit"] == "mm"
        assert abs(result[r]["value"] - 2.0) < 1e-4, result[r]["value"]


def _s7_empty_mask() -> None:
    from ml.analysis.thickness import measure_thickness

    mask = np.zeros((10, 10, 20), dtype=np.uint8)
    result = measure_thickness(mask)
    for r in ("anterior", "middle", "posterior"):
        assert result[r]["status"] == "empty_mask"
        assert result[r]["value"] is None


def _s7_missing_spacing_fallback() -> None:
    from ml.analysis.thickness import measure_thickness

    mask = np.ones((5, 5, 9), dtype=np.uint8)
    result = measure_thickness(mask, spacing_mm=None)
    for r in ("anterior", "middle", "posterior"):
        assert result[r]["unit"] == "voxels"


def _s7_fixture_phantom() -> None:
    from ml.analysis.thickness import measure_thickness

    _, labels = build_phantom(seed=0)
    binary = (labels == MENISCUS_LABEL).astype(np.uint8)
    result = measure_thickness(binary, spacing_mm=SPACING_MM)
    for r in ("anterior", "middle", "posterior"):
        assert result[r]["status"] == "ok", result[r]["status"]
        assert result[r]["value"] is not None
        assert math.isfinite(result[r]["value"]) and result[r]["value"] > 0


def run_section_7() -> None:
    print("\n[7] Measurement tests")
    _run("7.1 uniform cube → 2.0 mm",        _s7_uniform_cube)
    _run("7.2 empty mask → empty_mask",       _s7_empty_mask)
    _run("7.3 missing spacing → voxels",      _s7_missing_spacing_fallback)
    _run("7.4 fixture phantom positive vals", _s7_fixture_phantom)


# ============================================================
# Section 8 – Visualization test
# ============================================================

def _s8_overlay_png_written(tmp: str) -> None:
    from ml.analysis.thickness import measure_thickness
    from ml.visualization.overlay import draw_measurement_overlay

    image, labels = build_phantom(seed=0)
    mask = (labels == MENISCUS_LABEL).astype(np.uint8)
    thickness = measure_thickness(mask, spacing_mm=SPACING_MM)

    out_png = os.path.join(tmp, "test_overlay.png")
    meta = draw_measurement_overlay(
        volume=image, mask=mask, thickness=thickness,
        spacing_mm=SPACING_MM, out_png=out_png,
        model_version="phase14_test",
    )
    assert os.path.isfile(out_png), "PNG not written"
    assert os.path.getsize(out_png) > 10_000, "PNG suspiciously small"
    assert meta is not None
    for r in ("anterior", "middle", "posterior"):
        assert r in meta.regions


def _s8_overlay_empty_mask_no_crash(tmp: str) -> None:
    """Empty segmentation must produce a PNG without crashing."""
    from ml.analysis.thickness import measure_thickness
    from ml.visualization.overlay import draw_measurement_overlay

    image, _ = build_phantom(seed=0)
    empty_mask = np.zeros(VOL_SHAPE, dtype=np.uint8)
    thickness = measure_thickness(empty_mask, spacing_mm=SPACING_MM)

    out_png = os.path.join(tmp, "empty_overlay.png")
    draw_measurement_overlay(
        volume=image, mask=empty_mask, thickness=thickness,
        spacing_mm=SPACING_MM, out_png=out_png,
    )
    assert os.path.isfile(out_png)


def _s8_json_result_schema(tmp: str) -> None:
    from ml.analysis.thickness import measure_thickness
    from ml.visualization.overlay import build_json_result

    _, labels = build_phantom(seed=0)
    mask = (labels == MENISCUS_LABEL).astype(np.uint8)
    thickness = measure_thickness(mask, spacing_mm=SPACING_MM)

    result = build_json_result(
        thickness=thickness,
        overlay_path=os.path.join(tmp, "dummy.png"),
        model_version="v_test",
        spacing_mm=SPACING_MM,
        subject_id="phantom_000",
    )
    assert "measurements" in result
    assert "overlay_path" in result
    assert "model_version" in result
    assert "spacing" in result
    for r in ("anterior", "middle", "posterior"):
        assert r in result["measurements"]


def run_section_8(tmp: str) -> None:
    print("\n[8] Visualization tests")
    _run("8.1 overlay PNG written",             lambda: _s8_overlay_png_written(tmp))
    _run("8.2 empty mask overlay no crash",     lambda: _s8_overlay_empty_mask_no_crash(tmp))
    _run("8.3 JSON result schema",              lambda: _s8_json_result_schema(tmp))


# ============================================================
# Section 9 – Full pipeline test
# ============================================================

def _s9_analyze_meniscus_e2e(tmp: str) -> None:
    from ml.pipeline import analyze_meniscus

    img_path = os.path.join(tmp, "images", "phantom_000.nii.gz")
    out_dir  = os.path.join(tmp, "pipeline_out")
    result = analyze_meniscus(img_path, out_dir=out_dir)

    # Top-level keys
    for key in ("model_version", "segmentation", "measurements",
                "visualization", "metadata"):
        assert key in result, f"missing key: {key}"

    # Segmentation
    seg = result["segmentation"]
    assert seg["voxel_count"] > 0
    assert seg["slices_with_mask"] > 0
    assert os.path.isfile(seg["mask_path"])

    # Measurements
    for r in ("anterior", "middle", "posterior"):
        entry = result["measurements"][r]
        assert entry["status"] == "ok", f"{r}: {entry['status']}"
        assert entry["unit"] == "mm"
        assert entry["value"] > 0

    # Visualization
    assert os.path.isfile(result["visualization"]["overlay_path"])

    # Metadata
    meta = result["metadata"]
    assert meta["spacing"] is not None
    assert isinstance(meta["subject_id"], str)


def _s9_complete_data_flow(tmp: str) -> None:
    """Verify physical path: MRI → mask → thickness → overlay → JSON."""
    from ml.pipeline import analyze_meniscus
    import json

    img_path = os.path.join(tmp, "images", "phantom_001.nii.gz")
    out_dir  = os.path.join(tmp, "flow_check")
    result = analyze_meniscus(img_path, out_dir=out_dir)

    # Serialisable to JSON (no numpy arrays, no non-finite floats)
    blob = json.dumps(result["measurements"])
    loaded = json.loads(blob)
    assert set(loaded.keys()) == {"anterior", "middle", "posterior"}


def run_section_9(tmp: str) -> None:
    print("\n[9] Full pipeline tests")
    _run("9.1 analyze_meniscus end-to-end",  lambda: _s9_analyze_meniscus_e2e(tmp))
    _run("9.2 MRI→mask→measure→viz→JSON",    lambda: _s9_complete_data_flow(tmp))


# ============================================================
# Section 10 – Failure cases
# ============================================================

def _s10_invalid_image_path() -> None:
    from ml.pipeline import analyze_meniscus

    raised = False
    try:
        analyze_meniscus("/nonexistent/path/scan.nii.gz")
    except FileNotFoundError:
        raised = True
    assert raised, "expected FileNotFoundError for missing image"


def _s10_wrong_file_extension() -> None:
    from ml.pipeline import analyze_meniscus

    raised = False
    try:
        # File doesn't need to exist for the extension check
        analyze_meniscus("/tmp/some_scan.dcm")
    except (ValueError, FileNotFoundError):
        raised = True
    assert raised, "expected ValueError/FileNotFoundError for .dcm input"


def _s10_empty_segmentation_no_crash(tmp: str) -> None:
    """A volume that produces zero foreground voxels must not raise."""
    from ml.analysis.thickness import measure_thickness
    from ml.visualization.overlay import draw_measurement_overlay

    image, _ = build_phantom(seed=0)
    empty = np.zeros(VOL_SHAPE, dtype=np.uint8)
    t = measure_thickness(empty, spacing_mm=SPACING_MM)
    for r in ("anterior", "middle", "posterior"):
        assert t[r]["status"] == "empty_mask"

    out_png = os.path.join(tmp, "empty_seg.png")
    draw_measurement_overlay(image, empty, t, SPACING_MM, out_png)
    assert os.path.isfile(out_png)


def _s10_missing_spacing_returns_voxels() -> None:
    from ml.analysis.thickness import measure_thickness

    mask = np.ones((5, 5, 9), dtype=np.uint8)
    result = measure_thickness(mask, spacing_mm=None)
    for r in ("anterior", "middle", "posterior"):
        assert result[r]["unit"] == "voxels", \
            f"expected voxels without spacing, got {result[r]['unit']}"


def _s10_corrupted_model_raises(tmp: str) -> None:
    """A checkpoint that lacks required keys raises ValueError."""
    from ml.inference.predict import MeniscusPredictor

    bad_ckpt = os.path.join(tmp, "bad_model.pth")
    torch.save({"garbage": 42}, bad_ckpt)

    raised = False
    try:
        MeniscusPredictor(bad_ckpt)
    except (ValueError, RuntimeError):
        raised = True
    assert raised, "expected ValueError/RuntimeError for corrupted checkpoint"


def _s10_unsupported_dimensions(tmp: str) -> None:
    """A 4-D NIfTI must be rejected with ValueError."""
    from ml.inference.predict import MeniscusPredictor

    ckpt = os.path.join(_ROOT, "checkpoints", "best_model.pth")
    if not os.path.isfile(ckpt):
        raise FileNotFoundError("checkpoint not found — skip")

    # Write a 4-D NIfTI
    vol4d = np.zeros((16, 16, 4, 3), dtype=np.float32)
    bad_nii = os.path.join(tmp, "four_d.nii.gz")
    nib.save(nib.Nifti1Image(vol4d, np.eye(4)), bad_nii)

    raised = False
    try:
        pred = MeniscusPredictor(ckpt)
        pred.predict_volume(bad_nii)
    except ValueError:
        raised = True
    assert raised, "expected ValueError for 4-D input"


def _s10_wrong_ndim_mask_raises() -> None:
    from ml.analysis.thickness import measure_thickness

    raised = False
    try:
        measure_thickness(np.ones((10, 10), dtype=np.uint8))
    except ValueError:
        raised = True
    assert raised, "expected ValueError for 2-D mask"


def _s10_invalid_spacing_components_fallback() -> None:
    from ml.analysis.thickness import measure_thickness

    mask = np.ones((5, 5, 9), dtype=np.uint8)
    for bad in [(0.0, 0.5, 1.0), (float("nan"), 0.5, 1.0), (-1.0, 0.5, 1.0)]:
        result = measure_thickness(mask, spacing_mm=bad)
        assert result["anterior"]["unit"] == "voxels", \
            f"expected voxel fallback for spacing {bad}"


def run_section_10(tmp: str) -> None:
    print("\n[10] Failure case tests")
    _run("10.1 invalid image path",              _s10_invalid_image_path)
    _run("10.2 wrong file extension",            _s10_wrong_file_extension)
    _run("10.3 empty segmentation no crash",     lambda: _s10_empty_segmentation_no_crash(tmp))
    _run("10.4 missing spacing → voxels",        _s10_missing_spacing_returns_voxels)
    _run("10.5 corrupted model raises",          lambda: _s10_corrupted_model_raises(tmp))
    _run("10.6 unsupported dimensions raises",   lambda: _s10_unsupported_dimensions(tmp))
    _run("10.7 2-D mask raises ValueError",      _s10_wrong_ndim_mask_raises)
    _run("10.8 invalid spacing → voxel fallback",_s10_invalid_spacing_components_fallback)


# ============================================================
# Runner
# ============================================================

def main() -> int:
    print("=" * 64)
    print("PHASE 14 — Final ML Testing and Stabilization")
    print("=" * 64)

    with tempfile.TemporaryDirectory(prefix="nexora_phase14_") as tmp:
        write_fixtures(tmp, n_volumes=3, seed=42)

        run_section_1(tmp)
        run_section_2(tmp)
        run_section_3()
        run_section_4()
        run_section_5()
        run_section_6(tmp)
        run_section_7()
        run_section_8(tmp)
        run_section_9(tmp)
        run_section_10(tmp)

    total = len(PASS_LIST) + len(FAIL_LIST)
    print(f"\n{'=' * 64}")
    print(f"Results: {len(PASS_LIST)}/{total} passed,  {len(FAIL_LIST)} failed")

    if FAIL_LIST:
        print("\nFailed tests:")
        for name in FAIL_LIST:
            print(f"  FAIL  {name}")
        return 1

    print("\nAll Phase 14 tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
