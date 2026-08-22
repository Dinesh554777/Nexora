import io
from fastapi.testclient import TestClient
import numpy as np
import pytest
from PIL import Image
from main import app
from config import settings
import api.routes as api_routes
from services.model_adapter import BaseModelAdapter, ModelPredictionOutput
from services.postprocessor import BasePostprocessor

client = TestClient(app)


def create_sample_png_bytes(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color="green")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_debug_disabled_by_default():
    """DEBUG must default to False so unhandled errors never leak tracebacks."""
    assert settings.DEBUG is False


def test_preprocessing_value_error_returns_clean_400(monkeypatch):
    """Images passing validation but failing decode/resize must yield 400, not 500."""

    def broken_preprocess(raw_bytes):
        raise ValueError("PIL decode exploded")

    monkeypatch.setattr(
        api_routes.preprocessor_service, "preprocess", broken_preprocess
    )
    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", create_sample_png_bytes(), "image/png")},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "corrupted or in an unsupported format" in detail
    assert "PIL" not in detail
    assert "ValueError" not in detail


def test_preprocessing_unexpected_error_returns_clean_500(monkeypatch):
    def broken_preprocess(raw_bytes):
        raise RuntimeError("secret internal state /home/dev/app/preprocessor.py")

    monkeypatch.setattr(
        api_routes.preprocessor_service, "preprocess", broken_preprocess
    )
    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", create_sample_png_bytes(), "image/png")},
    )

    assert response.status_code == 500
    body = response.text
    assert response.json()["detail"] == "Image preprocessing failed."
    assert "Traceback" not in body
    assert "preprocessor.py" not in body
    assert "RuntimeError" not in body


def test_inference_unexpected_error_returns_clean_500(monkeypatch):
    class ExplodingAdapter(BaseModelAdapter):

        def is_loaded(self):
            return True

        def predict(self, container):
            raise RuntimeError("CUDA error at C:/models/weights.pt")

    monkeypatch.setattr(api_routes, "model_adapter_service", ExplodingAdapter())
    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", create_sample_png_bytes(), "image/png")},
    )

    assert response.status_code == 500
    body = response.text
    assert response.json()["detail"] == "Model inference processing failed."
    assert "Traceback" not in body
    assert "weights.pt" not in body


def test_postprocessing_unexpected_error_returns_clean_500(monkeypatch):
    class WorkingAdapter(BaseModelAdapter):

        def is_loaded(self):
            return True

        def predict(self, container):
            import numpy as np

            h, w = container.processed_shape[:2]
            return ModelPredictionOutput(
                raw_prediction_array=np.zeros((h, w), dtype=np.float32),
                output_shape=(h, w),
                execution_time_ms=1.0,
            )

    class ExplodingPostprocessor(BasePostprocessor):

        def is_configured(self):
            return True

        def process(self, input_data):
            raise RuntimeError("mask encoder crashed")

    monkeypatch.setattr(api_routes, "model_adapter_service", WorkingAdapter())
    monkeypatch.setattr(
        api_routes, "postprocessor_service", ExplodingPostprocessor()
    )
    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", create_sample_png_bytes(), "image/png")},
    )

    assert response.status_code == 500
    body = response.text
    assert (
        response.json()["detail"] == "Postprocessing result generation failed."
    )
    assert "Traceback" not in body
    assert "RuntimeError" not in body


def test_oversized_dimensions_rejected(monkeypatch):
    """Declared dimensions beyond the guard must be rejected before decoding."""
    monkeypatch.setattr(settings, "MAX_IMAGE_DIMENSION_PX", 10)
    response = client.post(
        "/api/v1/segment",
        files={
            "file": (
                "scan.png",
                create_sample_png_bytes(100, 100),
                "image/png",
            )
        },
    )

    assert response.status_code == 400
    assert "dimensions exceed" in response.json()["detail"]


def test_normal_dimensions_pass_guard(monkeypatch):
    monkeypatch.setattr(settings, "MAX_IMAGE_DIMENSION_PX", 10000)
    response = client.post(
        "/api/v1/segment",
        files={
            "file": (
                "scan.png",
                create_sample_png_bytes(100, 100),
                "image/png",
            )
        },
    )

    assert response.status_code == 503


@pytest.mark.parametrize("limit", [0, -5])
def test_non_positive_dimension_limit_disables_guard(monkeypatch, limit):
    monkeypatch.setattr(settings, "MAX_IMAGE_DIMENSION_PX", limit)
    response = client.post(
        "/api/v1/segment",
        files={
            "file": (
                "scan.png",
                create_sample_png_bytes(100, 100),
                "image/png",
            )
        },
    )

    assert response.status_code == 503
