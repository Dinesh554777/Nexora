"""Phase 11: visualization sub-package — measurement overlays for segmentation results."""

from ml.visualization.overlay import (
    OverlayMeta,
    build_json_result,
    draw_measurement_overlay,
)

__all__ = [
    "OverlayMeta",
    "draw_measurement_overlay",
    "build_json_result",
]
