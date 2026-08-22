from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import numpy as np
from services.preprocessor import PreprocessedImageContainer


class ModelNotAvailableError(Exception):
    """Raised when model prediction is attempted before a real model or weights

    file is registered.
    """

    pass


@dataclass
class ModelPredictionOutput:
    """Structured framework-agnostic output contract for future model predictions.

    Encapsulates raw prediction output array, shape, execution time, and
    metadata. All ML-specific interpretations (class count, activation
    function, decision threshold, framework type) are optional and remain
    unresolved until official ML model specifications are committed to main.
    """

    raw_prediction_array: np.ndarray
    output_shape: tuple[int, ...]
    execution_time_ms: float
    num_classes: int | None = None  # Optional: TEMPORARY — PENDING ML SPECIFICATION
    metadata: dict[str, Any] = field(
        default_factory=lambda: {
            "specification_status": "TEMPORARY — PENDING ML SPECIFICATION"
        }
    )


class BaseModelAdapter(ABC):
    """Abstract base class defining the contract for all future ML model adapters.

    Accepts PreprocessedImageContainer from preprocessor and returns
    ModelPredictionOutput.
    """

    @abstractmethod
    def predict(
        self, container: PreprocessedImageContainer
    ) -> ModelPredictionOutput:
        """Executes model inference on preprocessed image container.

        To be implemented by concrete framework adapters (e.g. PyTorch,
        TensorFlow, ONNX).
        """
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Returns True if model weights and architecture are loaded in memory."""
        pass


class PendingModelAdapter(BaseModelAdapter):
    """Placeholder adapter active while real ML model specifications are pending on main.

    Does NOT fabricate synthetic predictions. Raises ModelNotAvailableError if
    predict() is called.
    """

    def is_loaded(self) -> bool:
        return False

    def predict(
        self, container: PreprocessedImageContainer
    ) -> ModelPredictionOutput:
        raise ModelNotAvailableError(
            "No trained ML model weights or framework adapter registered. "
            "Real model implementation is pending main branch updates from the ML team."
        )


model_adapter_service: BaseModelAdapter = PendingModelAdapter()
