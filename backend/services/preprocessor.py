from dataclasses import dataclass, field
import io
from typing import Any
import numpy as np
from PIL import Image
from config import settings


@dataclass
class PreprocessedImageContainer:
    """Encapsulates preprocessed numeric array data for future model inference

    and preserved original image metadata for postprocessing and overlay
    generation.
    """

    original_image: Image.Image
    original_size: tuple[int, int]  # (width, height)
    original_mode: str
    processed_array: np.ndarray
    processed_shape: tuple[int, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class ImagePreprocessor:
    """Generic image preprocessing service.

    Note: All transformation parameters (target size, color mode,
    normalization scaling, mean/std) are loaded dynamically from configuration
    and represent TEMPORARY generic defaults until ML model specifications are
    committed to main.
    """

    @staticmethod
    def load_image(raw_bytes: bytes) -> Image.Image:
        """Loads and returns a PIL Image from raw bytes."""
        try:
            return Image.open(io.BytesIO(raw_bytes))
        except Exception as e:
            raise ValueError(f"Failed to load image from bytes: {e}") from e

    @staticmethod
    def convert_color_mode(image: Image.Image, color_mode: str) -> Image.Image:
        """Converts PIL image to target color mode ('RGB', 'L', etc.).

        Target mode parameter is TEMPORARY — PENDING ML SPECIFICATION.
        """
        valid_modes = {"RGB", "L", "RGBA", "CMYK"}
        color_mode_upper = color_mode.upper()
        if color_mode_upper not in valid_modes:
            raise ValueError(
                f"Unsupported color mode '{color_mode}'. Valid options: {valid_modes}"
            )
        if image.mode != color_mode_upper:
            return image.convert(color_mode_upper)
        return image

    @staticmethod
    def resize_image(
        image: Image.Image, target_size: tuple[int, int]
    ) -> Image.Image:
        """Resizes PIL image to target_size (height, width).

        Target size parameter is TEMPORARY — PENDING ML SPECIFICATION. Pillow
        resize expects (width, height).
        """
        h, w = target_size
        if h <= 0 or w <= 0:
            raise ValueError(
                f"Target dimensions must be positive integers, got height={h}, width={w}"
            )
        return image.resize((w, h), Image.Resampling.BILINEAR)

    @staticmethod
    def normalize_array(
        array: np.ndarray,
        normalize: bool = True,
        mean: list[float] | None = None,
        std: list[float] | None = None,
    ) -> np.ndarray:
        """Converts uint8 array to float32, scales to [0.0, 1.0] if normalize=True,

        and optionally applies channel-wise mean/std standardization.
        Normalization values are TEMPORARY — PENDING ML SPECIFICATION.
        """
        arr = array.astype(np.float32)

        if normalize:
            arr /= 255.0

        if mean is not None:
            mean_arr = np.array(mean, dtype=np.float32)
            arr = arr - mean_arr

        if std is not None:
            std_arr = np.array(std, dtype=np.float32)
            std_arr = np.where(std_arr == 0, 1e-7, std_arr)
            arr = arr / std_arr

        return arr

    def preprocess(
        self,
        raw_bytes: bytes,
        target_size: tuple[int, int] | None = None,
        color_mode: str | None = None,
        normalize: bool | None = None,
        mean: list[float] | None = None,
        std: list[float] | None = None,
    ) -> PreprocessedImageContainer:
        """Executes generic preprocessing pipeline using centralized config values.

        All defaults are marked TEMPORARY — PENDING ML SPECIFICATION.
        """
        t_size = (
            target_size
            if target_size is not None
            else settings.PREPROCESS_TARGET_SIZE
        )
        c_mode = (
            color_mode
            if color_mode is not None
            else settings.PREPROCESS_COLOR_MODE
        )
        norm = (
            normalize
            if normalize is not None
            else settings.PREPROCESS_NORMALIZE
        )
        m_vec = mean if mean is not None else settings.PREPROCESS_MEAN
        s_vec = std if std is not None else settings.PREPROCESS_STD

        # 1. Load original image and preserve attributes
        raw_image = self.load_image(raw_bytes)
        original_size = raw_image.size  # (width, height)
        original_mode = raw_image.mode
        original_preserved = raw_image.copy()

        # 2. Convert color mode
        converted_image = self.convert_color_mode(raw_image, c_mode)

        # 3. Resize image
        resized_image = self.resize_image(converted_image, t_size)

        # 4. Convert to NumPy array & Normalize
        np_array = np.array(resized_image)
        processed_array = self.normalize_array(
            np_array, normalize=norm, mean=m_vec, std=s_vec
        )

        metadata = {
            "target_size": t_size,
            "color_mode": c_mode,
            "normalized": norm,
            "mean_applied": m_vec is not None,
            "std_applied": s_vec is not None,
            "processed_shape": processed_array.shape,
            "status": "completed",
            "specification_status": "TEMPORARY — PENDING ML SPECIFICATION",
        }

        return PreprocessedImageContainer(
            original_image=original_preserved,
            original_size=original_size,
            original_mode=original_mode,
            processed_array=processed_array,
            processed_shape=processed_array.shape,
            metadata=metadata,
        )


preprocessor_service = ImagePreprocessor()
