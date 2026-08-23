"""Phase 3: deterministic preprocessing pipeline for 2D meniscus U-Net.

Order of operations (fixed, no randomness anywhere):
    raw slice -> percentile-clip + min-max normalize (image only)
              -> resize image with bilinear interpolation
              -> resize mask with NEAREST neighbor only, then re-binarize
              -> validate binary integrity
              -> compute effective spacing from ORIGINAL spacing
              -> convert to torch tensors

Physical spacing is never baked into pixels: the original header zooms are
carried through untouched (`spacing_mm_original`) and the post-resize
in-plane spacing is derived separately (`spacing_mm_resized`) so that later
thickness measurements can be done in true millimetres.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np
import torch
import torch.nn.functional as F

from nexora.data.loader import SliceSample


DEFAULT_TARGET_SIZE = (256, 256)
DEFAULT_CLIP_PERCENTILES = (1.0, 99.0)


@dataclass(frozen=True)
class PreprocessConfig:
    target_size: tuple[int, int] = DEFAULT_TARGET_SIZE   # (H_out, W_out)
    clip_percentiles: tuple[float, float] = DEFAULT_CLIP_PERCENTILES
    eps: float = 1e-8


@dataclass
class PreprocessedSample:
    image: torch.Tensor            # float32 (1, H, W), roughly [0, 1]
    mask: torch.Tensor             # float32 (1, H, W), values exactly {0.0, 1.0}
    spacing_mm_original: tuple[float, float, float]
    spacing_mm_resized: tuple[float, float, float]
    slice_index: int
    slice_axis: int
    volume_index: int
    source_image: str = ""
    source_mask: str = ""


def normalize_intensity(
    img: np.ndarray,
    percentiles: tuple[float, float] = DEFAULT_CLIP_PERCENTILES,
    eps: float = 1e-8,
) -> np.ndarray:
    """Deterministic MRI intensity normalization.

    Robust percentile clipping followed by min-max scaling to [0, 1].
    Operates on the slice only; identical input always yields identical output.
    """
    img = np.asarray(img, dtype=np.float32)
    lo, hi = np.percentile(img, percentiles)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi - lo < eps:
        raise ValueError("degenerate intensity range after percentile clipping")
    return np.clip((img - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def resize_image(img: np.ndarray, target_hw: tuple[int, int]) -> np.ndarray:
    """Bilinear resize for the IMAGE channel."""
    x = torch.from_numpy(np.ascontiguousarray(img, dtype=np.float32))[None, None]
    y = F.interpolate(x, size=target_hw, mode="bilinear", align_corners=False)
    return y[0, 0].numpy()


def resize_mask(mask: np.ndarray, target_hw: tuple[int, int]) -> np.ndarray:
    """NEAREST-neighbor-only resize for the MASK, then hard re-binarization.

    Binarizing again after nearest sampling guarantees the output contains
    exactly {0, 1} regardless of upstream label noise; no gray interpolation
    values can ever be introduced because `mode="nearest"` is the only path.
    """
    m = torch.from_numpy(np.ascontiguousarray((mask > 0).astype(np.uint8)))[None, None].float()
    y = F.interpolate(m, size=target_hw, mode="nearest")
    return (y[0, 0].numpy() > 0).astype(np.uint8)


def check_binary(mask: np.ndarray, name: str = "mask") -> None:
    uniq = set(np.unique(np.asarray(mask)).tolist())
    if not uniq.issubset({0, 1}):
        raise ValueError(
            f"{name} binary integrity violated: unique values {sorted(uniq)}"
        )


def derive_resized_spacing(
    spacing_inplane_mm: Sequence[float],
    original_hw: tuple[int, int],
    target_hw: tuple[int, int],
    slice_thickness_mm: float,
) -> tuple[float, float, float]:
    """Effective in-plane spacing after resize; thickness is untouched.

    physical extent is conserved: new_spacing = old_spacing * old_size / new_size
    """
    sy = spacing_inplane_mm[0] * (original_hw[0] / target_hw[0])
    sx = spacing_inplane_mm[1] * (original_hw[1] / target_hw[1])
    return (float(sx), float(sy), float(slice_thickness_mm))


def preprocess_slice(sample: SliceSample, config: PreprocessConfig | None = None) -> PreprocessedSample:
    cfg = config or PreprocessConfig()

    img_n = normalize_intensity(sample.image, cfg.clip_percentiles, cfg.eps)

    h0, w0 = img_n.shape
    img_r = resize_image(img_n, cfg.target_size)
    msk_r = resize_mask(sample.mask, cfg.target_size)

    check_binary(sample.mask, "source mask")
    check_binary(msk_r, "resized mask")

    spc_r = derive_resized_spacing(
        sample.spacing_inplane_mm,
        original_hw=(h0, w0),
        target_hw=cfg.target_size,
        slice_thickness_mm=sample.slice_thickness_mm,
    )

    return PreprocessedSample(
        image=torch.from_numpy(img_r[None].copy()).float(),
        mask=torch.from_numpy((msk_r > 0)[None].astype(np.float32)),
        spacing_mm_original=(
            sample.spacing_inplane_mm[0],
            sample.spacing_inplane_mm[1],
            sample.slice_thickness_mm,
        ),
        spacing_mm_resized=spc_r,
        slice_index=sample.slice_index,
        slice_axis=sample.slice_axis,
        volume_index=sample.volume_index,
        source_image=sample.source_image,
        source_mask=sample.source_mask,
    )
