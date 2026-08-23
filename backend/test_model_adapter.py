import io
import numpy as np
from PIL import Image
import pytest
from services.model_adapter import (
    BaseModelAdapter,
    ModelNotAvailableError,
    ModelPredictionOutput,
    PendingModelAdapter,
    model_adapter_service,
)
from services.preprocessor import (
    PreprocessedImageContainer,
    preprocessor_service,
)


def create_sample_container() -> PreprocessedImageContainer:
    """Helper to create a valid PreprocessedImageContainer."""
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return preprocessor_service.preprocess(buf.getvalue())


def test_model_adapter_interface_and_imports():
    """Verify that BaseModelAdapter, PendingModelAdapter, and contracts import cleanly."""
    assert issubclass(PendingModelAdapter, BaseModelAdapter)
    assert isinstance(model_adapter_service, BaseModelAdapter)
    assert model_adapter_service.is_loaded() is False


def test_input_contract_matches_preprocessed_container():
    """Verify that a valid PreprocessedImageContainer satisfies the adapter input contract."""
    container = create_sample_container()
    assert hasattr(container, "original_image")
    assert hasattr(container, "original_size")
    assert hasattr(container, "original_mode")
    assert hasattr(container, "processed_array")
    assert hasattr(container, "processed_shape")
    assert hasattr(container, "metadata")
    assert isinstance(container.processed_array, np.ndarray)


def test_prediction_output_contract_without_hardcoded_defaults():
    """Verify ModelPredictionOutput without hardcoded thresholds, sigmoid/softmax, or class assumptions."""
    dummy_array = np.zeros((256, 256), dtype=np.float32)
    output = ModelPredictionOutput(
        raw_prediction_array=dummy_array,
        output_shape=dummy_array.shape,
        execution_time_ms=12.5,
    )
    assert output.raw_prediction_array.shape == (256, 256)
    assert output.output_shape == (256, 256)
    assert output.num_classes is None  # Optional / pending ML spec
    assert output.execution_time_ms == 12.5
    assert (
        output.metadata.get("specification_status")
        == "TEMPORARY — PENDING ML SPECIFICATION"
    )


def test_pending_adapter_raises_error_without_fake_prediction():
    """Verify that predicting on pending adapter raises ModelNotAvailableError without generating fake data."""
    container = create_sample_container()
    pending_adapter = PendingModelAdapter()

    with pytest.raises(ModelNotAvailableError) as exc_info:
        pending_adapter.predict(container)

    assert "No trained ML model weights or framework adapter registered" in str(
        exc_info.value
    )


def test_concrete_subclass_implementation_conformance():
    """Verify that a concrete framework adapter conforming to BaseModelAdapter works as expected."""

    class DummyTestAdapter(BaseModelAdapter):

        def is_loaded(self) -> bool:
            return True

        def predict(
            self, container: PreprocessedImageContainer
        ) -> ModelPredictionOutput:
            h, w = container.processed_shape[:2]
            output_array = np.zeros((h, w), dtype=np.float32)
            return ModelPredictionOutput(
                raw_prediction_array=output_array,
                output_shape=output_array.shape,
                execution_time_ms=5.0,
                metadata={"adapter_type": "test-conformance"},
            )

    test_adapter = DummyTestAdapter()
    assert test_adapter.is_loaded() is True
    container = create_sample_container()
    res = test_adapter.predict(container)
    assert isinstance(res, ModelPredictionOutput)
    assert res.output_shape == (256, 256)
