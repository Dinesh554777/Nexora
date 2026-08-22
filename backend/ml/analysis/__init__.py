"""Phase 10: analysis sub-package — geometric measurements on segmentation masks."""

from ml.analysis.thickness import (
    ThicknessResult,
    measure_from_inference_result,
    measure_thickness,
)

__all__ = [
    "ThicknessResult",
    "measure_thickness",
    "measure_from_inference_result",
]
