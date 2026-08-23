import base64
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from PIL import Image

from services.model_adapter import ModelPredictionOutput
from services.preprocessor import PreprocessedImageContainer


class PostprocessingNotConfiguredError(Exception):
    """Raised when postprocessing is attempted before model output metadata or
    parameters are configured.
    """

    pass


@dataclass
class PostprocessingInput:
    """Input contract encapsulating model prediction output and original image
    information required for postprocessing and overlay generation.
    """

    prediction: ModelPredictionOutput
    container: PreprocessedImageContainer


@dataclass
class SegmentationResultOutput:
    """Structured output contract for frontend-ready segmentation results."""

    mask_image_base64: str | None = None
    overlay_image_base64: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.metadata = dict(self.metadata or {})
        self.metadata.setdefault(
            "specification_status",
            "TEMPORARY — PENDING ML SPECIFICATION",
        )


class BasePostprocessor(ABC):
    """Abstract interface for postprocessing model prediction outputs into
    frontend results.
    """

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def process(
        self, input_data: PostprocessingInput
    ) -> SegmentationResultOutput:
        pass


class UNetPostprocessor(BasePostprocessor):
    """Concrete postprocessor for the actual PyTorch U-Net probability output."""

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = float(threshold)
        self.model_name = "unet2d"

    def is_configured(self) -> bool:
        return True

    @staticmethod
    def _encode_png(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def process(
        self, input_data: PostprocessingInput
    ) -> SegmentationResultOutput:
        prediction = input_data.prediction
        container = input_data.container

        raw = np.asarray(prediction.raw_prediction_array, dtype=np.float32)
        if raw.ndim == 3:
            if raw.shape[0] == 1:
                raw = raw[0]
            elif raw.shape[-1] == 1:
                raw = raw[..., 0]
        if raw.ndim != 2:
            raise ValueError(
                "Expected a 2D probability map from the model prediction; "
                f"got shape {raw.shape}"
            )

        mask_uint8 = (raw >= self.threshold).astype(np.uint8)
        original_image = container.original_image.convert("RGB")
        original_size = container.original_size

        mask_image = Image.fromarray((mask_uint8 * 255).astype(np.uint8), mode="L")
        mask_image = mask_image.resize(original_size, Image.Resampling.NEAREST)
        mask_png = self._encode_png(mask_image)

        overlay = original_image.convert("RGBA")
        red_mask = Image.new("RGBA", original_size, (255, 0, 0, 128))
        alpha_mask = Image.fromarray((mask_uint8 * 255).astype(np.uint8), mode="L")
        alpha_mask = alpha_mask.resize(original_size, Image.Resampling.NEAREST)
        overlay = Image.composite(red_mask, overlay, alpha_mask)
        overlay_png = self._encode_png(overlay)

        mask_area = int(mask_uint8.sum())
        probability_mean = float(raw.mean()) if raw.size else 0.0

        return SegmentationResultOutput(
            mask_image_base64=mask_png,
            overlay_image_base64=overlay_png,
            metrics={
                "mask_area_pixels": mask_area,
                "mask_fraction": float(mask_area / max(raw.size, 1)),
                "probability_mean": probability_mean,
                "threshold": self.threshold,
            },
            metadata={
                "model_name": self.model_name,
                "threshold": self.threshold,
                "input_shape": list(raw.shape),
                "original_size": list(original_size),
                "output_size": list(raw.shape),
            },
        )


class PendingPostprocessor(BasePostprocessor):
    """Placeholder postprocessor retained for compatibility with existing tests
    and explicit failure handling.
    """

    def is_configured(self) -> bool:
        return False

    def process(
        self, input_data: PostprocessingInput
    ) -> SegmentationResultOutput:
        raise PostprocessingNotConfiguredError(
            "Postprocessing is not configured. "
            "Real ML model output specifications are pending main branch updates from the ML team."
        )


postprocessor_service: BasePostprocessor = PendingPostprocessor()
