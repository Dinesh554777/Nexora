import os
from pydantic import BaseModel


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    APP_NAME: str = "Nexora Backend API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = _env_flag("DEBUG", False)

    # CORS Settings for local development
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # File Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_IMAGE_DIMENSION_PX: int = int(
        os.getenv("MAX_IMAGE_DIMENSION_PX", "10000")
    )
    ALLOWED_IMAGE_TYPES: set[str] = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff",
    }

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # -------------------------------------------------------------------------
    # TEMPORARY PREPROCESSING SETTINGS — PENDING ML SPECIFICATION FROM MAIN BRANCH
    # Note: None of the values below represent final U-Net model requirements.
    # They are centralized temporary placeholders for pipeline construction and
    # must be updated when the ML team commits official specifications to main.
    # -------------------------------------------------------------------------
    PREPROCESS_TARGET_SIZE: tuple[int, int] = (
        256,
        256,
    )  # TEMPORARY — PENDING ML SPECIFICATION (Height, Width)
    PREPROCESS_COLOR_MODE: str = (
        "RGB"  # TEMPORARY — PENDING ML SPECIFICATION ("RGB" vs "L"/Grayscale)
    )
    PREPROCESS_NORMALIZE: bool = (
        True  # TEMPORARY — PENDING ML SPECIFICATION (Scale [0,255] -> [0,1])
    )
    PREPROCESS_MEAN: list[float] | None = (
        None  # TEMPORARY — PENDING ML SPECIFICATION (Channel mean subtraction)
    )
    PREPROCESS_STD: list[float] | None = (
        None  # TEMPORARY — PENDING ML SPECIFICATION (Channel std division)
    )
    MODEL_WEIGHTS_PATH: str | None = os.getenv(
        "MODEL_WEIGHTS_PATH", None
    )  # TEMPORARY — PENDING ML SPECIFICATION


settings = Settings()
