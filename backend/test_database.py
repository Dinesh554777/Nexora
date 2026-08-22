import io
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

import api.routes as api_routes
from config import settings
from database.connection import (
    check_database_connection,
    dispose_engine,
    get_engine,
    get_session_factory,
    session_scope,
)
from main import app
from models.prediction import Prediction
from services.model_adapter import BaseModelAdapter, ModelPredictionOutput
from services.postprocessor import BasePostprocessor, SegmentationResultOutput
from services.preprocessor import PreprocessedImageContainer


def make_sqlite_url(tmp_path) -> str:
    return f"sqlite:///{tmp_path / 'test_nexora.db'}"


@pytest.fixture()
def sqlite_db(tmp_path, monkeypatch):
    """Provides an isolated file-backed SQLite database per test."""
    url = make_sqlite_url(tmp_path)
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    dispose_engine()
    engine = get_engine()
    from database.base import Base
    from models import Prediction  # noqa: F401

    Base.metadata.create_all(engine)
    yield engine
    dispose_engine()


def create_sample_png_bytes(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class DummyConfiguredModelAdapter(BaseModelAdapter):
    def is_loaded(self) -> bool:
        return True

    def predict(
        self, container: PreprocessedImageContainer
    ) -> ModelPredictionOutput:
        h, w = container.processed_shape[:2]
        raw_array = np_zeros(h, w)
        return ModelPredictionOutput(
            raw_prediction_array=raw_array,
            output_shape=raw_array.shape,
            execution_time_ms=12.5,
        )


def np_zeros(h: int, w: int):
    import numpy as np

    return np.zeros((h, w), dtype=np.float32)


class DummyConfiguredPostprocessor(BasePostprocessor):
    def is_configured(self) -> bool:
        return True

    def process(self, input_data) -> SegmentationResultOutput:
        return SegmentationResultOutput(
            mask_image_base64="data:image/png;base64,mockmask",
            overlay_image_base64="data:image/png;base64,mockoverlay",
            metrics={"segmented_area_pixels": 150},
            metadata={"status": "processed"},
        )


# 1. Database configuration loading


def test_require_database_url_returns_configured_value(monkeypatch):
    monkeypatch.setattr(
        settings,
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@localhost:5432/nexora",
    )
    assert (
        settings.require_database_url()
        == "postgresql+psycopg://user:pass@localhost:5432/nexora"
    )


def test_missing_database_url_raises_clear_safe_error(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    with pytest.raises(ValueError) as exc_info:
        settings.require_database_url()
    message = str(exc_info.value)
    assert "DATABASE_URL is not configured" in message
    assert ".env.example" in message


def test_mask_connection_string_hides_password():
    masked = settings.mask_connection_string(
        "postgresql+psycopg://admin:s3cr3t@db.internal:5432/nexora"
    )
    assert "s3cr3t" not in masked
    assert "***" in masked
    assert "db.internal:5432" in masked


# 2. Database session creation


def test_session_factory_creates_working_session(sqlite_db):
    factory = get_session_factory()
    session = factory()
    try:
        assert session.execute(select(1)).scalar() == 1
    finally:
        session.close()


# 3. Database connection failure handling


def test_connection_failure_reports_safe_error(monkeypatch):
    unreachable = (
        "postgresql+psycopg://nexora_user:supersecret@127.0.0.1:1/nexora"
    )
    monkeypatch.setattr(settings, "DATABASE_URL", unreachable)
    dispose_engine()

    ok, detail = check_database_connection()

    assert ok is False
    assert "database connection failed" in detail
    assert "supersecret" not in detail
    assert unreachable not in detail
    assert "@" not in detail


def test_missing_configuration_reports_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    dispose_engine()

    ok, detail = check_database_connection()

    assert ok is False
    assert "DATABASE_URL is not configured" in detail


# 4. Prediction model validation


def test_prediction_model_defaults(sqlite_db):
    record = Prediction(status="success")
    assert record.id is None
    assert record.original_filename is None
    assert record.image_width is None
    assert record.error_message is None
    assert "Prediction" in repr(record)


def test_prediction_status_is_required(sqlite_db):
    factory = get_session_factory()
    session = factory()
    try:
        session.add(Prediction())
        with pytest.raises(Exception):
            session.flush()
    finally:
        session.rollback()
        session.close()


# 5. Creating a database record


def test_create_prediction_record(sqlite_db):
    with session_scope() as session:
        record = Prediction(
            status="success",
            original_filename="scan.png",
            image_width=640,
            image_height=480,
            execution_time_ms=9.75,
            metrics_json={"area": 123},
            metadata_json={"status": "processed"},
        )
        session.add(record)
        session.flush()
        assert record.id is not None

    with session_scope() as session:
        stored = session.get(Prediction, record.id)
        assert stored is not None
        assert stored.status == "success"
        assert stored.metrics_json == {"area": 123}


# 6. Reading a database record


def test_read_prediction_record_roundtrip(sqlite_db):
    with session_scope() as session:
        session.add(
            Prediction(
                status="failed",
                original_filename="broken.png",
                error_message="inference: RuntimeError",
            )
        )

    with session_scope() as session:
        found = session.scalars(
            select(Prediction).where(Prediction.status == "failed")
        ).one()
        assert found.original_filename == "broken.png"
        assert found.error_message == "inference: RuntimeError"
        assert found.created_at is not None
        assert found.updated_at is not None


# 7. Updating a record


def test_update_prediction_record(sqlite_db):
    with session_scope() as session:
        record = Prediction(status="success", image_width=100)
        session.add(record)
        session.flush()
        record_id = record.id

    with session_scope() as session:
        stored = session.get(Prediction, record_id)
        stored.image_height = 200
        stored.execution_time_ms = 3.25

    with session_scope() as session:
        updated = session.get(Prediction, record_id)
        assert updated.image_width == 100
        assert updated.image_height == 200
        assert updated.execution_time_ms == 3.25


# 8. Transaction rollback


def test_transaction_rollback_on_failure(sqlite_db):
    with pytest.raises(RuntimeError):
        with session_scope() as session:
            session.add(Prediction(status="success", original_filename="x"))
            raise RuntimeError("boom")

    with session_scope() as session:
        count = len(session.scalars(select(Prediction)).all())
    assert count == 0


# 9. Segmentation API -> database persistence


def test_segmentation_api_persists_prediction_record(
    sqlite_db, monkeypatch
):
    monkeypatch.setattr(
        api_routes, "model_adapter_service", DummyConfiguredModelAdapter()
    )
    monkeypatch.setattr(
        api_routes, "postprocessor_service", DummyConfiguredPostprocessor()
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/segment",
        files={
            "file": ("medical_scan.png", create_sample_png_bytes(), "image/png")
        },
    )

    assert response.status_code == 200
    with session_scope() as session:
        records = session.scalars(select(Prediction)).all()
        assert len(records) == 1
        record = records[0]
        assert record.status == "success"
        assert record.original_filename == "medical_scan.png"
        assert record.image_width == 100
        assert record.image_height == 100
        assert record.execution_time_ms == 12.5
        assert record.metrics_json == {"segmented_area_pixels": 150}
        assert record.metadata_json["status"] == "processed"
        assert record.metadata_json["specification_status"] == "TEMPORARY — PENDING ML SPECIFICATION"
        assert record.error_message is None


# 10. Failed segmentation does not create an invalid successful record


def test_failed_inference_does_not_create_success_record(
    sqlite_db, monkeypatch
):
    from services.model_adapter import PendingModelAdapter

    monkeypatch.setattr(api_routes, "model_adapter_service", PendingModelAdapter())
    client = TestClient(app)

    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", create_sample_png_bytes(), "image/png")},
    )

    assert response.status_code == 503
    with session_scope() as session:
        records = session.scalars(select(Prediction)).all()
        assert all(r.status != "success" for r in records)


def test_failed_postprocessing_records_failure_not_success(
    sqlite_db, monkeypatch
):
    from services.postprocessor import PendingPostprocessor

    monkeypatch.setattr(
        api_routes, "model_adapter_service", DummyConfiguredModelAdapter()
    )
    monkeypatch.setattr(
        api_routes, "postprocessor_service", PendingPostprocessor()
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/segment",
        files={"file": ("scan.png", create_sample_png_bytes(), "image/png")},
    )

    assert response.status_code == 503
    with session_scope() as session:
        success_rows = [
            r for r in session.scalars(select(Prediction)).all()
            if r.status == "success"
        ]
        failed_rows = [
            r for r in session.scalars(select(Prediction)).all()
            if r.status == "failed"
        ]
    assert success_rows == []
    assert len(failed_rows) == 1
    assert "postprocessing" in failed_rows[0].error_message


# Health endpoint truthfulness (never hides DB state)


def test_database_health_endpoint_reports_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    dispose_engine()
    client = TestClient(app)

    response = client.get("/health/db")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["database"]["configured"] is False
    assert body["database"]["connected"] is False


def test_database_health_endpoint_connected(sqlite_db):
    client = TestClient(app)

    response = client.get("/health/db")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"]["configured"] is True
    assert body["database"]["connected"] is True


def test_database_health_endpoint_never_exposes_credentials(monkeypatch):
    secret_url = (
        "postgresql+psycopg://nexora:hunter2secret@127.0.0.1:1/nexora"
    )
    monkeypatch.setattr(settings, "DATABASE_URL", secret_url)
    dispose_engine()
    client = TestClient(app)

    response = client.get("/health/db")

    body_text = response.text
    assert "hunter2secret" not in body_text
    assert "nexora:hunter2secret" not in body_text
