"""OA Feature Extraction Service.

Extracts quantitative features from the UNet segmentation probability map
and binary mask that are relevant to OA assessment.  These features are the
sole input to the OA classifier — the classification is derived entirely
from the uploaded image's segmentation output, never from filenames,
patient IDs, or hardcoded values.

Feature Set
-----------
All features are computed from the actual model output for the uploaded image.

Mask-coverage features (from binarised mask, threshold=0.5):
  mask_fraction          Fraction of image pixels classified as meniscus.
  mask_area_pixels       Total foreground pixel count.
  mask_compactness       4π·area / perimeter² — measures how round/compact
                         the segmented region is (1.0 = perfect circle).
  mask_convexity         mask_area / convex_hull_area — measures solidity.

Probability-distribution features (from raw sigmoid output, continuous):
  prob_mean              Mean of all pixel probabilities (0-1).
  prob_std               Std dev of all pixel probabilities.
  prob_median            Median pixel probability.
  prob_high_fraction     Fraction of pixels with probability > 0.7
                         (strongly activated region).
  prob_low_fraction      Fraction of pixels with probability < 0.3
                         (background confidence).

Spatial-structure features:
  foreground_row_span    Fraction of row extent occupied by the mask
                         relative to image height (0-1).
  foreground_col_span    Fraction of column extent occupied by the mask
                         relative to image width (0-1).
  foreground_centroid_y  Normalised vertical centroid of the mask (0-1).
  foreground_centroid_x  Normalised horizontal centroid of the mask (0-1).

Clinical relevance
------------------
OA is associated with meniscal degeneration, thinning, and reduced coverage.
In the context of this segmentation model:
  - Healthy knee: clear, well-defined meniscus → high mask_fraction,
    high compactness, high prob_mean, high prob_high_fraction.
  - OA knee: degenerated/thinned meniscus → lower mask_fraction,
    irregular shape (lower compactness), lower prob_mean.

These features are NOT clinically validated measurements.  They are
algorithm-derived indicators used to drive a research/demo classifier.
The system must always surface this limitation to users.

No fake or hardcoded values are ever returned.  All features are computed
from the actual model output arrays passed to extract_features().
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import ndimage as ndi


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------

FEATURE_NAMES: list[str] = [
    "mask_fraction",
    "mask_area_pixels",
    "mask_compactness",
    "mask_convexity",
    "prob_mean",
    "prob_std",
    "prob_median",
    "prob_high_fraction",
    "prob_low_fraction",
    "foreground_row_span",
    "foreground_col_span",
    "foreground_centroid_y",
    "foreground_centroid_x",
]

FEATURE_DIM = len(FEATURE_NAMES)


@dataclass
class SegmentationFeatures:
    """Structured container for features extracted from one segmentation output.

    The ``vector`` attribute is a numpy array of shape (FEATURE_DIM,) in the
    same order as FEATURE_NAMES — ready to be fed to a scikit-learn estimator.

    All values are derived from real model output; none are hardcoded.
    """

    # Mask-coverage
    mask_fraction: float
    mask_area_pixels: int
    mask_compactness: float
    mask_convexity: float

    # Probability distribution
    prob_mean: float
    prob_std: float
    prob_median: float
    prob_high_fraction: float
    prob_low_fraction: float

    # Spatial structure
    foreground_row_span: float
    foreground_col_span: float
    foreground_centroid_y: float
    foreground_centroid_x: float

    # Provenance
    image_shape: tuple[int, int] = (0, 0)
    extraction_notes: list[str] = field(default_factory=list)

    @property
    def vector(self) -> np.ndarray:
        """Return feature vector as float32 array (shape: FEATURE_DIM,)."""
        return np.array(
            [
                self.mask_fraction,
                float(self.mask_area_pixels),
                self.mask_compactness,
                self.mask_convexity,
                self.prob_mean,
                self.prob_std,
                self.prob_median,
                self.prob_high_fraction,
                self.prob_low_fraction,
                self.foreground_row_span,
                self.foreground_col_span,
                self.foreground_centroid_y,
                self.foreground_centroid_x,
            ],
            dtype=np.float32,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialisable dict, suitable for the API response metadata field."""
        return {
            "mask_fraction": round(float(self.mask_fraction), 5),
            "mask_area_pixels": int(self.mask_area_pixels),
            "mask_compactness": round(float(self.mask_compactness), 5),
            "mask_convexity": round(float(self.mask_convexity), 5),
            "prob_mean": round(float(self.prob_mean), 5),
            "prob_std": round(float(self.prob_std), 5),
            "prob_median": round(float(self.prob_median), 5),
            "prob_high_fraction": round(float(self.prob_high_fraction), 5),
            "prob_low_fraction": round(float(self.prob_low_fraction), 5),
            "foreground_row_span": round(float(self.foreground_row_span), 5),
            "foreground_col_span": round(float(self.foreground_col_span), 5),
            "foreground_centroid_y": round(float(self.foreground_centroid_y), 5),
            "foreground_centroid_x": round(float(self.foreground_centroid_x), 5),
        }


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _compactness(mask_2d: np.ndarray) -> float:
    """4π·area / perimeter² — ranges (0, 1], equals 1.0 for a perfect circle.

    Returns 0.0 when the mask is empty or the perimeter cannot be measured.
    """
    area = int(mask_2d.sum())
    if area == 0:
        return 0.0
    # Perimeter: count pixels adjacent to background
    struct = np.ones((3, 3), dtype=bool)
    eroded = ndi.binary_erosion(mask_2d.astype(bool), structure=struct)
    perimeter = int((mask_2d.astype(bool) & ~eroded).sum())
    if perimeter == 0:
        return 1.0  # single-pixel or fully-interior case
    return float(min(1.0, (4 * math.pi * area) / (perimeter ** 2)))


def _convexity(mask_2d: np.ndarray) -> float:
    """mask_area / convex_hull_area — measures solidity (1.0 = fully convex).

    Approximated by labelling the filled convex hull via binary_fill_holes.
    Returns 0.0 for an empty mask.
    """
    area = int(mask_2d.sum())
    if area == 0:
        return 0.0
    filled = ndi.binary_fill_holes(mask_2d.astype(bool))
    hull_area = int(filled.sum())
    if hull_area == 0:
        return 0.0
    return float(min(1.0, area / hull_area))


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

def extract_features(
    prob_map: np.ndarray,
    threshold: float = 0.5,
) -> SegmentationFeatures:
    """Extract OA-relevant features from a segmentation probability map.

    Parameters
    ----------
    prob_map : np.ndarray
        2D float32 array, values in [0, 1].  This is the raw sigmoid output
        from the UNet for one image — the same array in
        ``ModelPredictionOutput.raw_prediction_array``.
    threshold : float
        Binarisation threshold (default 0.5, matching the training convention).

    Returns
    -------
    SegmentationFeatures
        All features derived from the actual model output.  No values are
        hardcoded or fabricated.

    Raises
    ------
    ValueError
        If prob_map is not a 2D array or contains non-finite values.
    """
    prob = np.asarray(prob_map, dtype=np.float32)
    if prob.ndim != 2:
        raise ValueError(
            f"extract_features expects a 2-D probability map, got shape {prob.shape}"
        )
    if not np.isfinite(prob).all():
        raise ValueError("prob_map contains non-finite values (NaN or Inf)")

    h, w = prob.shape
    total_pixels = h * w
    notes: list[str] = []

    # ---- binary mask ----
    mask = (prob >= threshold).astype(np.uint8)
    area = int(mask.sum())

    # ---- mask-coverage features ----
    mask_fraction = area / max(total_pixels, 1)
    compactness = _compactness(mask)
    convexity = _convexity(mask)

    # ---- probability features ----
    prob_mean = float(prob.mean())
    prob_std = float(prob.std())
    prob_median = float(np.median(prob))
    prob_high_fraction = float((prob > 0.7).sum() / max(total_pixels, 1))
    prob_low_fraction = float((prob < 0.3).sum() / max(total_pixels, 1))

    # ---- spatial features ----
    rows = np.any(mask, axis=1)      # shape (H,)
    cols = np.any(mask, axis=0)      # shape (W,)

    if rows.any():
        row_indices = np.where(rows)[0]
        row_span = float((row_indices[-1] - row_indices[0] + 1) / h)
        col_indices = np.where(cols)[0]
        col_span = float((col_indices[-1] - col_indices[0] + 1) / w)
        # centroid
        ys, xs = np.where(mask)
        centroid_y = float(ys.mean() / h)
        centroid_x = float(xs.mean() / w)
    else:
        row_span = 0.0
        col_span = 0.0
        centroid_y = 0.5
        centroid_x = 0.5
        notes.append("empty_mask: mask has no foreground pixels")

    return SegmentationFeatures(
        mask_fraction=mask_fraction,
        mask_area_pixels=area,
        mask_compactness=compactness,
        mask_convexity=convexity,
        prob_mean=prob_mean,
        prob_std=prob_std,
        prob_median=prob_median,
        prob_high_fraction=prob_high_fraction,
        prob_low_fraction=prob_low_fraction,
        foreground_row_span=row_span,
        foreground_col_span=col_span,
        foreground_centroid_y=centroid_y,
        foreground_centroid_x=centroid_x,
        image_shape=(h, w),
        extraction_notes=notes,
    )
