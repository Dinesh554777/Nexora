"""Deterministic synthetic DESS-like knee phantom for Phase 3 TESTS ONLY.

This module exists purely to verify preprocessing mechanics (alignment,
binary integrity, spacing bookkeeping) BEFORE the real dataset is placed.
It makes no claim of anatomical realism and must never be used as
research data.

Geometry: volume axes (R, C, Z) with slice_axis=2.
Meniscus wedge: analytic region per slice z:
    rows in [z_row0(z), z_row0(z) + z_height(z))
    cols in [cx - half_width(z), cx + half_width(z))
All boundary functions are smooth so that physical-extent checks survive
resampling to any resolution.
"""

from __future__ import annotations

import os

import nibabel as nib
import numpy as np

SPACING_MM = (0.36, 0.36, 0.70)
VOL_SHAPE = (96, 96, 48)
MENISCUS_LABEL = 7
DISTRACTOR_LABEL = 3

_CX = 48.0


def _half_width(z: float) -> float:
    return 6.0 + 4.0 * np.exp(-((z - 24.0) ** 2) / (2.0 * 8.0**2))


def _row_top(z: float) -> float:
    return 62.0 + 0.15 * (z - 24.0)


def _row_bot(z: float) -> float:
    return _row_top(z) + 7.0 + 0.05 * (z - 24.0)


def wedge_inside(r: np.ndarray | float, c: np.ndarray | float, z: float) -> np.ndarray:
    """Continuous membership test for the meniscus wedge at slice z."""
    hw = _half_width(z)
    rt = _row_top(z)
    rb = _row_bot(z)
    return (
        (np.asarray(r) >= rt) & (np.asarray(r) <= rb) &
        (np.asarray(c) >= _CX - hw) & (np.asarray(c) <= _CX + hw)
    )


def wedge_area_px(z: int) -> int:
    rr, cc = np.mgrid[0:VOL_SHAPE[0], 0:VOL_SHAPE[1]]
    return int(wedge_inside(rr, cc, float(z)).sum())


def build_phantom(seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Return (image float32 RxCxZ, label uint8 RxCxZ with values {0,3,7})."""
    rng = np.random.default_rng(seed)
    R, C, Z = VOL_SHAPE

    zz = np.arange(Z, dtype=np.float32)[None, None, :]
    base = 12.0 + 8.0 * zz / Z

    image = np.empty(VOL_SHAPE, dtype=np.float32)
    labels = np.zeros(VOL_SHAPE, dtype=np.uint8)

    rr, cc = np.mgrid[0:R, 0:C].astype(np.float32)

    def blob(arr: np.ndarray, cr: float, ccol: float, amp: float, rad: float) -> None:
        d2 = (rr - cr) ** 2 + (cc - ccol) ** 2
        arr += amp * np.exp(-d2 / (2.0 * rad**2))

    for z in range(Z):
        sl = np.full((R, C), base[0, 0, z], dtype=np.float32)

        blob(sl, 30.0, 40.0, 150.0, 9.0)
        blob(sl, 78.0, 52.0, 120.0, 11.0)
        blob(sl, 55.0, 20.0, 60.0, 6.0)

        m = wedge_inside(rr, cc, float(z))
        sl[m] += 35.0

        sl += rng.normal(0.0, 5.0, size=(R, C)).astype(np.float32)
        image[..., z] = np.clip(sl, 0.0, None)

        labels[..., z][m] = MENISCUS_LABEL

    labels[:, :, 10][30:45, 30:45] = DISTRACTOR_LABEL

    return image, labels


def write_fixtures(root: str, n_volumes: int = 3, seed: int = 42) -> list[tuple[str, str]]:
    """Write n volumes under root/images and root/masks; return pair list."""
    img_dir = os.path.join(root, "images")
    msk_dir = os.path.join(root, "masks")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(msk_dir, exist_ok=True)

    affine = np.diag((*SPACING_MM, 1.0)).astype(np.float64)
    pairs = []
    for i in range(n_volumes):
        image, labels = build_phantom(seed=seed + i)
        name = f"phantom_{i:03d}"
        ip = os.path.join(img_dir, name + ".nii.gz")
        mp = os.path.join(msk_dir, name + ".nii.gz")
        nib.save(nib.Nifti1Image(image, affine), ip)
        nib.save(nib.Nifti1Image(labels, affine), mp)
        pairs.append((ip, mp))
    return pairs
