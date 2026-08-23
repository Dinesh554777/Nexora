import io
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
from main import app
from config import settings
import api.routes as api_routes
from services.model_adapter import (
    BaseModelAdapter,
    ModelPredictionOutput,
    PendingModelAdapter,
)
from services.postprocessor import (
    BasePostprocessor,
    PendingPostprocessor,
    PostprocessingInput,
    SegmentationResultOutput,
)
from services.preprocessor import PreprocessedImageContainer

client = TestClient(app)


def create_sample_png_bytes(width: int = 100, height: int = 100) -> bytes:
    """Helper to generate valid PNG image bytes in memory."""
    img = Image.new("RGB", (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class DummyConfiguredModelAdapter(BaseModelAdapter):
    """Dummy concrete adapter simulating a configured ML model."""

    def is_loaded(self) -> bool:
        return True

    def predict(
        self, container: PreprocessedImageContainer
    ) -> ModelPredictionOutput:
        h, w = container.processed_shape[:2]
        raw_array = np.zeros((h, w), dtype=np.float32)
        return ModelPredictionOutput(
            raw_prediction_array=raw_array,
            output_shape=raw_array.shape,
            execution_time_ms=8.5,
            metadata={"framework": "mock-test"},
        )


class DummyConfiguredPostprocessor(BasePostprocessor):
    """Dummy concrete postprocessor simulating a configured result generator."""

    def is_configured(self) -> bool:
        return True

    def process(
        self, input_data: PostprocessingInput
    ) -> SegmentationResultOutput:
        return SegmentationResultOutput(
            mask_image_base64="data:image/png;base64,mockmask",
            overlay_image_base64="data:image/png;base64,mockoverlay",
            metrics={"segmented_area_pixels": 150},
            metadata={"status": "processed"},
        )


def test_successful_segmentation_endpoint_when_configured(monkeypatch):
    """Test POST /api/v1/segment when both model adapter and postprocessor are configured."""
    monkeypatch.setattr(
        api_routes, "model_adapter_service", DummyConfiguredModelAdapter()
    )
    monkeypatch.setattr(
        api_routes, "postprocessor_service", DummyConfiguredPostprocessor()
    )

    image_bytes = create_sample_png_bytes(100, 100)
    response = client.post(
        "/api/v1/segment",
        files={"file": ("medical_scan.png", image_bytes, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "medical_scan.png"
    assert data["mask_image_base64"] == "data:image/png;base64,mockmask"
    assert data["overlay_image_base64"] == "data:image/png;base64,mockoverlay"
    assert data["metrics"] == {"segmented_area_pixels": 150}
    assert data["metadata"]["status"] == "processed"


def test_missing_image_request():
    """Test POST /api/v1/segment without file parameter."""
    response = client.post("/api/v1/segment")
    assert response.status_code == 422  # Unprocessable Entity


def test_unsupported_image_type():
    """Test POST /api/v1/segment with unsupported content type."""
    text_content = b"Plain text file"
    response = client.post(
        "/api/v1/segment",
        files={"file": ("doc.txt", text_content, "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_corrupted_image_file():
    """Test POST /api/v1/segment with corrupt image bytes."""
    corrupt_bytes = b"CORRUPTED_NON_IMAGE_BYTES"
    response = client.post(
        "/api/v1/segment",
        files={"file": ("corrupt.png", corrupt_bytes, "image/png")},
    )
    assert response.status_code == 400
    assert "Invalid or corrupted image" in response.json()["detail"]


def test_oversized_image_file():
    """Test POST /api/v1/segment with payload exceeding max size."""
    orig_max = settings.MAX_UPLOAD_SIZE_MB
    settings.MAX_UPLOAD_SIZE_MB = 1
    try:
        oversized_data = b"0" * (1 * 1024 * 1024 + 50 * 1024)
        response = client.post(
            "/api/v1/segment",
            files={"file": ("huge.png", oversized_data, "image/png")},
        )
        assert response.status_code == 413
        assert "exceeds maximum allowed limit" in response.json()["detail"]
    finally:
        settings.MAX_UPLOAD_SIZE_MB = orig_max


def test_model_not_configured_error(monkeypatch):
    """Test POST /api/v1/segment when model adapter is pending/unconfigured (HTTP 503)."""
    monkeypatch.setattr(
        api_routes, "model_adapter_service", PendingModelAdapter()
    )
    image_bytes = create_sample_png_bytes()

    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", image_bytes, "image/png")},
    )

    assert response.status_code == 503
    assert (
        "No trained ML model weights or framework adapter registered"
        in response.json()["detail"]
    )


def test_postprocessor_not_configured_error(monkeypatch):
    """Test POST /api/v1/segment when postprocessor is pending/unconfigured (HTTP 503)."""
    monkeypatch.setattr(
        api_routes, "model_adapter_service", DummyConfiguredModelAdapter()
    )
    monkeypatch.setattr(
        api_routes, "postprocessor_service", PendingPostprocessor()
    )
    image_bytes = create_sample_png_bytes()

    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", image_bytes, "image/png")},
    )

    assert response.status_code == 503
    assert "Postprocessing is not configured" in response.json()["detail"]


def test_pipeline_execution_order(monkeypatch):
    """Verify that validator -> preprocessor -> model_adapter -> postprocessor are called in order."""
    execution_trace = []

    # Mock validator
    async def mock_validate(file):
        execution_trace.append("validator")
        return b"fake_bytes", (100, 100)

    # Mock preprocessor
    def mock_preprocess(raw_bytes):
        execution_trace.append("preprocessor")
        container = MagicMock(spec=PreprocessedImageContainer)
        container.processed_shape = (256, 256, 3)
        return container

    # Mock model adapter
    class MockModelAdapter(BaseModelAdapter):

        def is_loaded(self):
            return True

        def predict(self, container):
            execution_trace.append("model_adapter")
            return MagicMock(spec=ModelPredictionOutput)

    # Mock postprocessor
    class MockPostprocessor(BasePostprocessor):

        def is_configured(self):
            return True

        def process(self, input_data):
            execution_trace.append("postprocessor")
            return SegmentationResultOutput(
                mask_image_base64=None,
                overlay_image_base64=None,
                metrics={},
                metadata={"traced": True},
            )

    monkeypatch.setattr(api_routes, "validate_image_upload", mock_validate)
    monkeypatch.setattr(
        api_routes.preprocessor_service, "preprocess", mock_preprocess
    )
    monkeypatch.setattr(
        api_routes, "model_adapter_service", MockModelAdapter()
    )
    monkeypatch.setattr(
        api_routes, "postprocessor_service", MockPostprocessor()
    )

    image_bytes = create_sample_png_bytes()
    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", image_bytes, "image/png")},
    )

    assert response.status_code == 200
    assert execution_trace == [
        "validator",
        "preprocessor",
        "model_adapter",
        "postprocessor",
    ]


def test_response_schema_contract(monkeypatch):
    """Verify exact JSON response schema contract when pipeline succeeds."""
    monkeypatch.setattr(
        api_routes, "model_adapter_service", DummyConfiguredModelAdapter()
    )
    monkeypatch.setattr(
        api_routes, "postprocessor_service", DummyConfiguredPostprocessor()
    )

    image_bytes = create_sample_png_bytes()
    response = client.post(
        "/api/v1/segment",
        files={"file": ("test.png", image_bytes, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()

    expected_keys = {
        "success",
        "filename",
        "mask_image_base64",
        "overlay_image_base64",
        "metrics",
        "metadata",
    }
    assert set(data.keys()) == expected_keys
