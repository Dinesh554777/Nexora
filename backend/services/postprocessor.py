from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from services.model_adapter import ModelPredictionOutput
from services.preprocessor import PreprocessedImageContainer


class PostprocessingNotConfiguredError(Exception):
    """Raised when postprocessing is attempted before ML model output specifications

    and postprocessor parameters are configured.
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
    """Structured output contract for future frontend-ready segmentation results.

    Encapsulates Base64 encoded mask/overlay images, metrics, and metadata
    without assuming specific thresholds, class counts, or color maps.
    """

    mask_image_base64: str | None = None
    overlay_image_base64: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(
        default_factory=lambda: {
            "specification_status": "TEMPORARY — PENDING ML SPECIFICATION"
        }
    )


class BasePostprocessor(ABC):
    """Abstract interface for postprocessing model prediction outputs into

    frontend results.
    """

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if postprocessor has confirmed ML parameters loaded."""
        pass

    @abstractmethod
    def process(
        self, input_data: PostprocessingInput
    ) -> SegmentationResultOutput:
        """Transforms ModelPredictionOutput into SegmentationResultOutput.

        To be implemented by concrete postprocessors once ML output
        specifications are committed to main.
        """
        pass


class PendingPostprocessor(BasePostprocessor):
    """Placeholder postprocessor active while real ML output specifications are pending on main.

    Does NOT fabricate synthetic masks or overlay images. Raises
    PostprocessingNotConfiguredError if process() is called.
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
