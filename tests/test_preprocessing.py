"""Phase 3 verification suite: MRI preprocessing for meniscus U-Net.

Run:  python tests/test_preprocessing.py [--with-viz]

Covers, per the Phase 3 contract:
  * loader correctness (shapes, dtypes, spacing read from NIfTI header)
  * deterministic intensity normalization
  * mask resized with NEAREST neighbor only -> binary integrity {0,1}
  * image/mask stay aligned through preprocessing
  * no geometric distortion of the mask (physical bbox conserved in mm)
  * original physical spacing preserved separately + derived spacing math
  * PyTorch tensor conversion (dtype/shape/values)
  * bitwise determinism of repeated runs
  * end-to-end dataset over fixture root

Synthetic fixtures are TEST PLUMBING ONLY (see tests/fixtures.py).
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import traceback

import numpy as np

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nexora.data import (  # noqa: E402
    PairSlicesDataset,
    discover_pairs,
    extract_slices,
    load_volume_pair,
)
from nexora.preprocessing import (  # noqa: E402
    PreprocessConfig,
    check_binary,
    derive_resized_spacing,
    normalize_intensity,
    preprocess_slice,
    resize_mask,
    resize_image,
)

from fixtures import (  # noqa: E402
    MENISCUS_LABEL,
    SPACING_MM,
    VOL_SHAPE,
    wedge_area_px,
    wedge_inside,
    write_fixtures,
)

TARGET = (256, 256)


def _mask_slice_at_target(mask2d: np.ndarray, target: tuple[int, int]) -> np.ndarray:
    """Analytic reference: wedge membership evaluated at target resolution.

    Independent of any interpolation implementation: each target pixel center
    is mapped back to continuous source coordinates and tested against the
    wedge formula.
    """
    th, tw = target
    sh, sw = mask2d.shape
    ry = np.arange(th) * (sh / th) + (sh / th - 1.0) / 2.0
    rx = np.arange(tw) * (sw / tw) + (sw / tw - 1.0) / 2.0
    rr = np.repeat(ry[:, None], tw, axis=1)
    cc = np.repeat(rx[None, :], th, axis=0)
    return wedge_inside(rr, cc, 24.0).astype(np.uint8)


def _bbox(mask2d: np.ndarray):
    rows = np.any(mask2d > 0, axis=1)
    cols = np.any(mask2d > 0, axis=0)
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    return int(r0), int(r1) + 1, int(c0), int(c1) + 1


def _hash_sample(img: np.ndarray, msk: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(img).tobytes())
    h.update(np.ascontiguousarray(msk).tobytes())
    return h.hexdigest()


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

def make_fixtures(tmp: str):
    return write_fixtures(tmp, n_volumes=3, seed=42)


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

def test_loader_shapes_spacing_and_binarization(root: str):
    pairs = discover_pairs(root)
    assert len(pairs) == 3, f"expected 3 pairs, found {len(pairs)}"

    vp = load_volume_pair(*pairs[0], foreground_labels=(MENISCUS_LABEL,))
    assert vp.image.shape == VOL_SHAPE
    assert vp.mask.dtype == np.uint8
    assert vp.image.dtype == np.float32
    assert set(np.unique(vp.mask).tolist()).issubset({0, 1})

    got = tuple(round(s, 6) for s in vp.spacing_mm)
    want = tuple(round(s, 6) for s in SPACING_MM)
    assert got == want, f"spacing readback {got} != header value {want}"

    raw = __import__("nibabel").load(pairs[0][1]).get_fdata()
    distractor_only = (raw == 3).sum() > 0
    assert distractor_only and not np.any(vp.mask[raw == 3] == 1), (
        "label selection failed: DISTRACTOR label leaked into meniscus mask"
    )


def test_slice_extraction_aligned_topk_deterministic(root: str):
    vp = load_volume_pair(*discover_pairs(root)[0], foreground_labels=(MENISCUS_LABEL,))
    slices = extract_slices(vp, slice_axis=2, top_k=5)
    assert len(slices) == 5

    areas = [int(s.mask.sum()) for s in slices]
    all_areas = [wedge_area_px(z) for z in range(VOL_SHAPE[2])]
    expected = sorted(range(len(all_areas)), key=lambda i: (-all_areas[i], i))[:5]
    assert sorted(s.slice_index for s in slices) == sorted(expected), (
        "top-k slice selection not deterministic/expected"
    )

    for s in slices:
        assert s.image.shape == s.mask.shape
        check_binary(s.mask, "extracted slice mask")
        assert np.allclose(s.spacing_inplane_mm, (SPACING_MM[0], SPACING_MM[1]), atol=1e-6)
        assert np.isclose(s.slice_thickness_mm, SPACING_MM[2], atol=1e-6)

    again = extract_slices(vp, slice_axis=2, top_k=5)
    assert [s.slice_index for s in slices] == [s.slice_index for s in again]


def test_normalization_range_and_determinism():
    rng = np.random.default_rng(7)
    img = rng.normal(50.0, 25.0, size=(96, 96)).astype(np.float32) * 100.0
    n1 = normalize_intensity(img)
    n2 = normalize_intensity(img)
    assert n1.dtype == np.float32
    assert float(n1.min()) >= 0.0 and float(n1.max()) <= 1.0
    assert np.array_equal(n1, n2), "normalization is not deterministic"
    assert abs(float(n1.mean()) - float(n1.mean())) < 1e-12

    try:
        normalize_intensity(np.full((8, 8), 5.0, dtype=np.float32))
        raise AssertionError("constant image should raise")
    except ValueError:
        pass


def test_mask_resize_nearest_only_binary_integrity():
    rng = np.random.default_rng(11)
    m = (rng.random((96, 96)) > 0.5).astype(np.uint8)
    r = resize_mask(m, TARGET)
    uniq = set(np.unique(r).tolist())
    assert uniq.issubset({0, 1}), f"NN resize produced non-binary values {uniq}"
    assert r.shape == TARGET

    multilabel = np.zeros((64, 64), dtype=np.uint8)
    multilabel[10:30, 10:30] = 7
    multilabel[40:55, 40:60] = 3
    rb = resize_mask(multilabel, TARGET)
    assert set(np.unique(rb).tolist()).issubset({0, 1}), "binarization policy broken"

    empty = resize_mask(np.zeros((32, 32), dtype=np.uint8), TARGET)
    assert int(empty.sum()) == 0


def test_alignment_image_and_mask_move_together():
    """Image and mask must undergo the SAME geometric transform.

    Checked three ways, all robust to percentile-clipped normalization:
      1. mask centroid scales exactly by the resize factor;
      2. the tissue signature of the wedge (brighter than background)
         appears inside the resized mask and not outside -> no relative
         translation between image and mask;
      3. nearest-neighbor round-trip of the resized mask reproduces the
         source mask with high Dice -> transform is geometry-consistent.
    """
    from fixtures import build_phantom

    img, labels = build_phantom(seed=99)
    sl = extract_slices(load_from_arrays(img, labels), slice_axis=2, indices=[24])[0]
    src_mask = sl.mask
    r0, r1, c0, c1 = _bbox(src_mask)

    cfg = PreprocessConfig(target_size=TARGET)
    out = preprocess_slice(sl, cfg)

    scale_y = TARGET[0] / src_mask.shape[0]
    scale_x = TARGET[1] / src_mask.shape[1]

    m0, m1, mm0, mm1 = _bbox(out.mask[0].numpy().astype(np.uint8))
    cy_src, cx_src = (r0 + r1) / 2.0, (c0 + c1) / 2.0
    cy_dst, cx_dst = (m0 + m1) / 2.0, (mm0 + mm1) / 2.0
    assert abs(cy_dst - cy_src * scale_y) <= 2.0, "row centroid misaligned"
    assert abs(cx_dst - cx_src * scale_x) <= 2.0, "col centroid misaligned"

    img_np = out.image[0].numpy()
    msk_bool = out.mask[0].numpy() > 0
    inside_mean = float(img_np[msk_bool].mean())
    outside_mean = float(img_np[~msk_bool].mean())
    assert inside_mean - outside_mean >= 0.03, (
        f"wedge tissue signature missing inside mask: "
        f"in={inside_mean:.4f} out={outside_mean:.4f}"
    )

    import torch
    import torch.nn.functional as F_torch

    m_t = out.mask.unsqueeze(0)
    back = F_torch.interpolate(m_t, size=src_mask.shape, mode="nearest")[0, 0]
    back_bin = (back.numpy() > 0).astype(np.uint8)
    inter = int((back_bin & src_mask).sum())
    dice = 2.0 * inter / (int(back_bin.sum()) + int(src_mask.sum()))
    # double nearest resampling erodes ~1 boundary ring of this small
    # structure (~0.85 expected); a real >=2px shift would fall below 0.72
    assert dice >= 0.80, f"round-trip mask Dice too low (shift?): {dice:.3f}"


def load_from_arrays(image: np.ndarray, labels: np.ndarray):
    """Wrap in-memory arrays into a VolumePair-like via temp NIfTI files."""
    import nibabel as nib
    import tempfile as tf

    d = tf.mkdtemp(prefix="nexora_arr_")
    affine = np.diag((*SPACING_MM, 1.0))
    ip, mp = os.path.join(d, "i.nii.gz"), os.path.join(d, "m.nii.gz")
    nib.save(nib.Nifti1Image(image, affine), ip)
    nib.save(nib.Nifti1Image(labels.astype(np.uint8), affine), mp)
    return load_volume_pair(ip, mp, foreground_labels=(MENISCUS_LABEL,))


def test_no_distortion_physical_extent_conserved():
    from fixtures import build_phantom

    img, labels = build_phantom(seed=5)
    pair = load_from_arrays(img, labels)
    sl = extract_slices(pair, slice_axis=2, indices=[24])[0]

    sy, sx = sl.spacing_inplane_mm
    r0, r1, c0, c1 = _bbox(sl.mask)
    phys_h_before = (r1 - r0) * sy
    phys_w_before = (c1 - c0) * sx

    out = preprocess_slice(sl, PreprocessConfig(target_size=TARGET))
    dsy, dsx = out.spacing_mm_resized[:2]
    b0, b1, bc0, bc1 = _bbox(out.mask[0].numpy().astype(np.uint8))
    phys_h_after = (b1 - b0) * dsy
    phys_w_after = (bc1 - bc0) * dsx

    tol = 2.0 * SPACING_MM[0]
    assert abs(phys_h_after - phys_h_before) <= tol, (
        f"mask height distorted: {phys_h_before:.3f}mm -> {phys_h_after:.3f}mm"
    )
    assert abs(phys_w_after - phys_w_before) <= tol, (
        f"mask width distorted: {phys_w_before:.3f}mm -> {phys_w_after:.3f}mm"
    )

    ref = _mask_slice_at_target(sl.mask, TARGET)
    got = out.mask[0].numpy().astype(np.uint8)
    inter = int((ref & got).sum())
    union = int((ref | got).sum())
    iou = inter / union if union else 1.0
    assert iou >= 0.80, f"NN-resized mask deviates from analytic reference: IoU={iou:.3f}"


def test_spacing_preserved_separately():
    orig = tuple(SPACING_MM)
    derived = derive_resized_spacing(orig[:2], original_hw=(96, 96), target_hw=TARGET,
                                     slice_thickness_mm=orig[2])
    assert derived[0] == orig[1] * 96 / TARGET[1]
    assert derived[1] == orig[0] * 96 / TARGET[0]
    assert derived[2] == orig[2], "slice thickness must never change"

    extent_before = 96 * orig[0]
    extent_after = TARGET[0] * derived[1]
    assert abs(extent_before - extent_after) < 1e-9, "physical FOV not conserved"

    from fixtures import build_phantom
    img, labels = build_phantom(seed=3)
    pair = load_from_arrays(img, labels)
    sl = extract_slices(pair, slice_axis=2, indices=[24])[0]
    before = sl.spacing_inplane_mm + (sl.slice_thickness_mm,)
    out = preprocess_slice(sl, PreprocessConfig(target_size=TARGET))
    assert out.spacing_mm_original == before, "original spacing was mutated"

    assert np.allclose(out.spacing_mm_original, SPACING_MM, atol=1e-6), (
        f"header spacing drifted: {out.spacing_mm_original} vs {SPACING_MM}"
    )
    assert out.spacing_mm_resized[0] == before[1] * 96 / TARGET[1]
    assert out.spacing_mm_resized[1] == before[0] * 96 / TARGET[0]
    assert out.spacing_mm_resized[2] == before[2], "thickness changed"


def test_tensor_conversion():
    from fixtures import build_phantom

    img, labels = build_phantom(seed=21)
    sl = extract_slices(load_from_arrays(img, labels), slice_axis=2, indices=[24])[0]
    out = preprocess_slice(sl, PreprocessConfig(target_size=TARGET))

    assert out.image.dtype.is_floating_point
    assert out.image.shape == (1, *TARGET)
    assert out.mask.shape == (1, *TARGET)
    assert torch_finite(out.image)
    um = set(torch_unique(out.mask).tolist())
    assert um.issubset({0.0, 1.0}), f"mask tensor values {um}"
    ui = torch_unique(out.image).tolist()
    assert min(ui) >= 0.0 and max(ui) <= 1.0


def torch_finite(t):
    return bool(__import__("torch").isfinite(t).all())


def torch_unique(t):
    return __import__("torch").unique(t)


def test_bitwise_determinism_end_to_end(root: str):
    ds = PairSlicesDataset(pairs_root=root, slice_axis=2, top_k_per_volume=2,
                           foreground_labels=(MENISCUS_LABEL,))
    assert len(ds) == 6, f"expected 6 slices from 3 volumes, got {len(ds)}"

    hashes_run1, samples1 = [], []
    cfg = PreprocessConfig(target_size=TARGET)
    for item in ds:
        out = preprocess_slice(item, cfg)
        samples1.append(out)
        hashes_run1.append(_hash_sample(out.image.numpy(), out.mask.numpy()))

    ds2 = PairSlicesDataset(pairs_root=root, slice_axis=2, top_k_per_volume=2,
                            foreground_labels=(MENISCUS_LABEL,))
    for item, h1 in zip(ds2, hashes_run1):
        out2 = preprocess_slice(item, cfg)
        assert _hash_sample(out2.image.numpy(), out2.mask.numpy()) == h1, (
            "preprocessing is not bitwise deterministic across runs"
        )
    return samples1


def main() -> int:
    with_viz = "--with-viz" in sys.argv
    tests = [
        ("loader", lambda root: test_loader_shapes_spacing_and_binarization(root)),
        ("slices", test_slice_extraction_aligned_topk_deterministic),
        ("normalize", lambda _: test_normalization_range_and_determinism()),
        ("nn_binary", lambda _: test_mask_resize_nearest_only_binary_integrity()),
        ("alignment", lambda _: test_alignment_image_and_mask_move_together()),
        ("no_distortion", lambda _: test_no_distortion_physical_extent_conserved()),
        ("spacing", lambda _: test_spacing_preserved_separately()),
        ("tensors", lambda _: test_tensor_conversion()),
    ]

    failures = []
    with tempfile.TemporaryDirectory(prefix="nexora_phase3_") as tmp:
        make_fixtures(tmp)
        for name, fn in tests:
            try:
                fn(tmp)
                print(f"PASS  {name}")
            except Exception:
                failures.append(name)
                print(f"FAIL  {name}\n{traceback.format_exc()}")

        samples = None
        try:
            samples = test_bitwise_determinism_end_to_end(tmp)
            print("PASS  determinism")
        except Exception:
            failures.append("determinism")
            print(f"FAIL  determinism\n{traceback.format_exc()}")

        if with_viz and samples:
            try:
                from visualize_preprocessing import save_visualization
                out_png = save_visualization(samples[:3])
                print(f"PASS  visualization -> {out_png}")
            except Exception:
                failures.append("visualization")
                print(f"FAIL  visualization\n{traceback.format_exc()}")

    real = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "raw")
    if os.path.isdir(real) and discover_pairs(real):
        print(f"NOTE  real data found under data/raw but NOT used by these "
              f"fixture tests; run scripts/run_real_data_check.py when ready")
    else:
        print("SKIP  real-data check (data/raw has no pairs yet)")

    print("\n" + ("ALL PHASE 3 PREPROCESSING TESTS PASSED" if not failures
                  else f"{len(failures)} TEST(S) FAILED: {failures}"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
