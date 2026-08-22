import io
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image
from main import app
from config import settings
import api.routes as api_routes
from services.model_adapter import BaseModelAdapter, ModelPredictionOutput
from services.postprocessor import (
    BasePostprocessor,
    PostprocessingInput,
    SegmentationResultOutput,
)
from services.preprocessor import PreprocessedImageContainer

client = TestClient(app)


def create_sample_png_bytes(width: int = 100, height: int = 100) -> bytes:
    """Helper to generate valid PNG image bytes in memory."""
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class DummyAdapterForUploadTest(BaseModelAdapter):

    def is_loaded(self):
        return True

    def predict(self, container: PreprocessedImageContainer):
        return ModelPredictionOutput(
            raw_prediction_array=np.zeros((128, 128)),
            output_shape=(128, 128),
            execution_time_ms=5.0,
        )


class DummyPostprocessorForUploadTest(BasePostprocessor):

    def is_configured(self):
        return True

    def process(self, input_data: PostprocessingInput):
        return SegmentationResultOutput(
            mask_image_base64=None,
            overlay_image_base64=None,
            metrics={},
            metadata={"status": "completed"},
        )


def test_valid_image_upload_and_preprocessing(monkeypatch):
    """Test uploading a valid PNG image file through the full segment route when configured."""
    monkeypatch.setattr(
        api_routes, "model_adapter_service", DummyAdapterForUploadTest()
    )
    monkeypatch.setattr(
        api_routes, "postprocessor_service", DummyPostprocessorForUploadTest()
    )

    image_bytes = create_sample_png_bytes(128, 128)
    response = client.post(
        "/api/v1/segment",
        files={"file": ("test_scan.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "test_scan.png"
    assert data["metadata"]["status"] == "completed"


def test_unsupported_file_type():
    """Test uploading a file with an unsupported file/content type."""
    text_content = b"This is a text file, not an image."
    response = client.post(
        "/api/v1/segment",
        files={"file": ("notes.txt", text_content, "text/plain")},
    )
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported file type" in data["detail"]


def test_corrupted_image_file():
    """Test uploading fake corrupt data claiming to be an image."""
    corrupt_bytes = b"NOT_A_REAL_IMAGE_DATA_CORRUPTED_BYTES"
    response = client.post(
        "/api/v1/segment",
        files={"file": ("corrupt.png", corrupt_bytes, "image/png")},
    )
    assert response.status_code == 400
    data = response.json()
    assert "Invalid or corrupted image" in data["detail"]


def test_oversized_file():
    """Test uploading a file that exceeds the max upload size limit."""
    original_max_size = settings.MAX_UPLOAD_SIZE_MB
    settings.MAX_UPLOAD_SIZE_MB = 1  # 1 MB in config

    try:
        oversized_data = b"0" * (1 * 1024 * 1024 + 100 * 1024)
        response = client.post(
            "/api/v1/segment",
            files={"file": ("large_scan.png", oversized_data, "image/png")},
        )
        assert response.status_code == 413
        data = response.json()
        assert "exceeds maximum allowed limit" in data["detail"]
    finally:
        settings.MAX_UPLOAD_SIZE_MB = original_max_size
