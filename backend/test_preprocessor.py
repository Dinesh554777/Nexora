import io
import numpy as np
from PIL import Image
import pytest
from config import settings
from services.preprocessor import preprocessor_service


def create_test_image_bytes(
    width: int = 200, height: int = 150, color: str = "blue"
) -> bytes:
    """Creates in-memory PNG image bytes."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_preprocessing_pipeline_execution():
    """Test full preprocessing pipeline on a valid image."""
    raw_bytes = create_test_image_bytes(200, 150)
    container = preprocessor_service.preprocess(raw_bytes)

    assert container.original_size == (200, 150)  # (width, height)
    assert container.original_mode == "RGB"
    assert isinstance(container.processed_array, np.ndarray)
    assert container.metadata["status"] == "completed"
    assert (
        container.metadata["specification_status"]
        == "TEMPORARY — PENDING ML SPECIFICATION"
    )


def test_original_metadata_preservation():
    """Test that original PIL image, size, and mode are preserved unchanged."""
    raw_bytes = create_test_image_bytes(320, 240)
    container = preprocessor_service.preprocess(raw_bytes)

    assert container.original_image.size == (320, 240)
    assert container.original_image.mode == "RGB"
    # Ensure original PIL image is independent of processed_array dimensions
    assert container.original_image.size != (
        container.processed_shape[1],
        container.processed_shape[0],
    )


def test_dynamic_config_overrides():
    """Verify that preprocessor dynamically obeys centralized config settings

    without any hardcoded assumptions.
    """
    raw_bytes = create_test_image_bytes(100, 100)

    orig_target_size = settings.PREPROCESS_TARGET_SIZE
    orig_color_mode = settings.PREPROCESS_COLOR_MODE

    try:
        # Dynamically alter configuration
        settings.PREPROCESS_TARGET_SIZE = (512, 512)
        settings.PREPROCESS_COLOR_MODE = "L"

        container = preprocessor_service.preprocess(raw_bytes)
        assert container.processed_shape == (512, 512)
        assert container.metadata["color_mode"] == "L"
    finally:
        settings.PREPROCESS_TARGET_SIZE = orig_target_size
        settings.PREPROCESS_COLOR_MODE = orig_color_mode


def test_configurable_preprocessing_behavior():
    """Test custom parameters passed directly to preprocess()."""
    raw_bytes = create_test_image_bytes(100, 100)

    container = preprocessor_service.preprocess(
        raw_bytes,
        target_size=(128, 64),
        color_mode="L",
        normalize=True,
        mean=[0.5],
        std=[0.5],
    )

    # Grayscale array shape: (Height, Width) = (128, 64)
    assert container.processed_shape == (128, 64)
    assert container.metadata["color_mode"] == "L"
    assert container.metadata["mean_applied"] is True
    assert container.metadata["std_applied"] is True

    # Values scaled to [0,1] then (val - 0.5) / 0.5 -> array in range [-1.0, 1.0]
    assert container.processed_array.max() <= 1.0
    assert container.processed_array.min() >= -1.0


def test_invalid_color_mode_raises_error():
    """Test that specifying an unsupported color mode raises ValueError."""
    raw_bytes = create_test_image_bytes(50, 50)
    with pytest.raises(ValueError, match="Unsupported color mode"):
        preprocessor_service.preprocess(raw_bytes, color_mode="INVALID_MODE")


def test_invalid_target_dimensions_raises_error():
    """Test that non-positive dimensions raise ValueError."""
    raw_bytes = create_test_image_bytes(50, 50)
    with pytest.raises(ValueError, match="Target dimensions must be positive"):
        preprocessor_service.preprocess(raw_bytes, target_size=(-100, 256))
