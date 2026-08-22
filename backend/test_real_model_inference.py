import io

import numpy as np
from PIL import Image
import pytest

from config import settings
from services.model_adapter import ModelNotAvailableError, UNetModelAdapter
from services.postprocessor import UNetPostprocessor
from services.preprocessor import preprocessor_service


def create_test_image(width: int = 256, height: int = 256, mode: str = "RGB") -> bytes:
    img = Image.new(mode, (width, height), color=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_unet_checkpoint_loads_into_current_architecture():
    adapter = UNetModelAdapter()
    assert adapter.is_loaded() is True
    assert adapter.model is not None
    assert adapter.model.__class__.__name__ == "UNet2D"


def test_unet_adapter_predicts_real_output_on_preprocessed_image():
    image_bytes = create_test_image(256, 256, "RGB")
    container = preprocessor_service.preprocess(image_bytes)
    adapter = UNetModelAdapter()

    prediction = adapter.predict(container)

    assert prediction.raw_prediction_array.shape == (256, 256)
    assert prediction.output_shape == (256, 256)
    assert prediction.raw_prediction_array.dtype == np.float32
    assert np.isfinite(prediction.raw_prediction_array).all()
    assert prediction.raw_prediction_array.min() >= 0.0
    assert prediction.raw_prediction_array.max() <= 1.0


def test_missing_checkpoint_raises_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "MODEL_WEIGHTS_PATH", "missing_checkpoint.pth")
    with pytest.raises(ModelNotAvailableError, match="checkpoint"):
        UNetModelAdapter()


def test_incompatible_checkpoint_rejected(tmp_path):
    bad_path = tmp_path / "bad_checkpoint.pth"
    bad_path.write_bytes(b"not a valid checkpoint")
    with pytest.raises(ModelNotAvailableError, match="Unable to load checkpoint"):
        UNetModelAdapter(checkpoint_path=str(bad_path))


def test_unet_postprocessor_generates_real_mask_and_overlay():
    image_bytes = create_test_image(256, 256, "RGB")
    container = preprocessor_service.preprocess(image_bytes)
    adapter = UNetModelAdapter()
    prediction = adapter.predict(container)
    postprocessor = UNetPostprocessor()
    result = postprocessor.process(type("Input", (), {"prediction": prediction, "container": container})())

    assert result.mask_image_base64 is not None
    assert result.overlay_image_base64 is not None
    assert isinstance(result.metrics, dict)
    assert "mask_area_pixels" in result.metrics
