import io
from fastapi.testclient import TestClient
from PIL import Image
from main import app
from config import settings

client = TestClient(app)


def create_sample_png_bytes(width: int = 100, height: int = 100) -> bytes:
    """Helper to generate valid PNG image bytes in memory."""
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_valid_image_upload_and_preprocessing():
    """Test uploading a valid PNG image file and verifying preprocessing metadata."""
    image_bytes = create_sample_png_bytes(128, 128)
    response = client.post(
        "/api/v1/segment",
        files={"file": ("test_scan.png", image_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "test_scan.png"
    assert data["content_type"] == "image/png"
    assert data["original_dimensions"] == {"width": 128, "height": 128}
    assert "preprocessing" in data
    assert data["preprocessing"]["status"] == "completed"
    assert "preprocessed successfully" in data["message"]


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
