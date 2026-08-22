import os
from urllib.parse import urlunsplit, urlparse, ParseResult

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr

load_dotenv()

_raw_api_key = os.getenv("NEXORA_API_KEY")


def urlreplace_netloc(parsed: ParseResult, netloc: str) -> str:
    """Rebuilds a URL string from a ParseResult with a replaced netloc."""
    return urlunsplit(
        (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )


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
        "http://localhost:3001",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
    ]
    CORS_ALLOW_LOCALHOST_REGEX: str = r"https?://(localhost|127\.0\.0\.1):(3000|3001|5173)"

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

    # Secret API key for future external ML/API integration. Stored as
    # SecretStr so repr()/str() never reveal the value in logs or errors.
    # Optional: the app starts without it; require_api_key() raises a clear
    # configuration error only when an integration actually needs it.
    NEXORA_API_KEY: SecretStr | None = (
        SecretStr(_raw_api_key) if _raw_api_key else None
    )

    # PostgreSQL connection string (SQLAlchemy format), e.g.
    # postgresql+psycopg://user:password@localhost:5432/nexora
    # Optional: the app starts without it; require_database_url() raises a
    # clear configuration error only when database access is attempted.
    # The URL contains credentials and is treated as a secret: never logged,
    # never included in API responses, and masked in any diagnostics.
    DATABASE_URL: str | None = os.getenv("DATABASE_URL") or None

    def require_api_key(self) -> str:
        """Returns the configured API key or raises a clear configuration error.

        The key value must never be logged.
        """
        if self.NEXORA_API_KEY is None:
            raise ValueError(
                "NEXORA_API_KEY is not configured. Set it via the environment "
                "or backend/.env (see backend/.env.example)."
            )
        return self.NEXORA_API_KEY.get_secret_value()

    def require_database_url(self) -> str:
        """Returns the configured DATABASE_URL or raises a clear config error.

        The returned URL contains credentials and must never be logged or
        embedded in API responses / exception messages shown to clients.
        """
        if self.DATABASE_URL is None or not self.DATABASE_URL.strip():
            raise ValueError(
                "DATABASE_URL is not configured. Set it via the environment "
                "or backend/.env (see backend/.env.example)."
            )
        return self.DATABASE_URL.strip()

    @staticmethod
    def mask_connection_string(url: str | None) -> str:
        """Returns a log-safe rendering of a database URL with credentials masked."""
        if not url:
            return "<unset>"
        try:
            parsed = urlparse(url)
            if parsed.password is None and parsed.username is None:
                return url
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            if parsed.username:
                netloc = f"{parsed.username}:***@{netloc}"
            elif parsed.password is not None:
                netloc = f"***@{netloc}"
            return urlreplace_netloc(parsed, netloc)
        except Exception:
            return "<redacted>"


settings = Settings()
