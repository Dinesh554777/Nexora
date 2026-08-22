import io
import numpy as np
from PIL import Image
import pytest
from services.model_adapter import ModelPredictionOutput
from services.postprocessor import (
    BasePostprocessor,
    PendingPostprocessor,
    PostprocessingInput,
    PostprocessingNotConfiguredError,
    SegmentationResultOutput,
    postprocessor_service,
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


def create_sample_prediction() -> ModelPredictionOutput:
    """Helper to create a sample ModelPredictionOutput."""
    dummy_array = np.zeros((256, 256), dtype=np.float32)
    return ModelPredictionOutput(
        raw_prediction_array=dummy_array,
        output_shape=dummy_array.shape,
        execution_time_ms=10.0,
    )


def test_postprocessor_interface_and_imports():
    """Verify postprocessor interfaces, errors, and contracts import cleanly."""
    assert issubclass(PendingPostprocessor, BasePostprocessor)
    assert isinstance(postprocessor_service, BasePostprocessor)
    assert postprocessor_service.is_configured() is False


def test_postprocessing_input_contract():
    """Verify PostprocessingInput encapsulates prediction output and original container."""
    container = create_sample_container()
    prediction = create_sample_prediction()
    input_data = PostprocessingInput(
        prediction=prediction, container=container
    )

    assert input_data.prediction == prediction
    assert input_data.container == container
    assert input_data.container.original_size == (100, 100)


def test_segmentation_result_output_contract_defaults():
    """Verify SegmentationResultOutput has no fake masks/overlays or hardcoded thresholds."""
    output = SegmentationResultOutput()
    assert output.mask_image_base64 is None
    assert output.overlay_image_base64 is None
    assert output.metrics == {}
    assert (
        output.metadata.get("specification_status")
        == "TEMPORARY — PENDING ML SPECIFICATION"
    )


def test_pending_postprocessor_raises_error_without_fake_results():
    """Verify PendingPostprocessor raises PostprocessingNotConfiguredError without fabricating masks."""
    container = create_sample_container()
    prediction = create_sample_prediction()
    input_data = PostprocessingInput(
        prediction=prediction, container=container
    )

    pending_postprocessor = PendingPostprocessor()

    with pytest.raises(PostprocessingNotConfiguredError) as exc_info:
        pending_postprocessor.process(input_data)

    assert "Postprocessing is not configured" in str(exc_info.value)


def test_concrete_postprocessor_subclass_conformance():
    """Verify that a concrete postprocessor subclass can process input data when configured."""

    class ConcreteTestPostprocessor(BasePostprocessor):

        def is_configured(self) -> bool:
            return True

        def process(
            self, input_data: PostprocessingInput
        ) -> SegmentationResultOutput:
            return SegmentationResultOutput(
                mask_image_base64=None,
                overlay_image_base64=None,
                metrics={"area_pixels": 0},
                metadata={"status": "test-processed"},
            )

    postprocessor = ConcreteTestPostprocessor()
    assert postprocessor.is_configured() is True

    container = create_sample_container()
    prediction = create_sample_prediction()
    input_data = PostprocessingInput(
        prediction=prediction, container=container
    )

    res = postprocessor.process(input_data)
    assert isinstance(res, SegmentationResultOutput)
    assert res.metrics["area_pixels"] == 0
    assert res.metadata["status"] == "test-processed"
