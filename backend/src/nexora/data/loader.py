"""Slice data container.

INTEGRATION NOTE (backend team): reconstructed as a plain dataclass from the
exact attribute contract consumed by nexora.preprocessing.pipeline (image,
mask, spacing, indices, provenance strings). Contains no behavior. Replace
with the ML developer's original module when nexora.data is restored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np


@dataclass
class SliceSample:
    """One 2-D image/mask slice plus its geometry and provenance."""

    image: np.ndarray
    mask: np.ndarray
    spacing_inplane_mm: Sequence[float]
    slice_thickness_mm: float
    slice_index: int
    slice_axis: int
    volume_index: int
    source_image: str = field(default="")
    source_mask: str = field(default="")
