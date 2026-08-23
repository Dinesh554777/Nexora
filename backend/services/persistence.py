import logging

from sqlalchemy.exc import SQLAlchemyError

from database.connection import session_scope
from models.prediction import Prediction

logger = logging.getLogger(__name__)

_MAX_FILENAME_LENGTH = 512
_MAX_ERROR_LENGTH = 2000


def _truncate(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return value[:limit]


def persist_prediction_success(
    *,
    original_filename: str | None,
    image_width: int | None,
    image_height: int | None,
    metrics: dict | None = None,
    metadata: dict | None = None,
    execution_time_ms: float | None = None,
    model_name: str | None = None,
) -> int | None:
    """Persists one committed 'success' prediction record.

    Returns the new record id, or None when persistence fails. Persistence
    failures are logged server-side (without credentials or connection
    strings) and never mask an already-successful segmentation response.
    """
    try:
        with session_scope() as session:
            record = Prediction(
                status="success",
                original_filename=_truncate(
                    original_filename, _MAX_FILENAME_LENGTH
                ),
                image_width=image_width,
                image_height=image_height,
                model_name=model_name,
                execution_time_ms=execution_time_ms,
                metrics_json=metrics,
                metadata_json=metadata,
            )
            session.add(record)
            session.flush()
            return record.id
    except ValueError:
        # DATABASE_URL not configured: persistence is disabled by design.
        logger.debug("Persistence skipped: DATABASE_URL is not configured")
        return None
    except SQLAlchemyError:
        logger.error(
            "Failed to persist successful prediction record", exc_info=True
        )
        return None


def persist_prediction_failure(
    *,
    original_filename: str | None,
    image_width: int | None,
    image_height: int | None,
    stage: str,
    error: Exception,
) -> int | None:
    """Persists one committed 'failed' prediction record after validation passed.

    Only the sanitized exception class name and pipeline stage are stored;
    full tracebacks stay in server logs only. Returns the new record id or
    None when persistence itself fails (also logged, never raised).
    """
    try:
        with session_scope() as session:
            record = Prediction(
                status="failed",
                original_filename=_truncate(
                    original_filename, _MAX_FILENAME_LENGTH
                ),
                image_width=image_width,
                image_height=image_height,
                error_message=_truncate(
                    f"{stage}: {type(error).__name__}", _MAX_ERROR_LENGTH
                ),
            )
            session.add(record)
            session.flush()
            return record.id
    except ValueError:
        logger.debug("Persistence skipped: DATABASE_URL is not configured")
        return None
    except SQLAlchemyError:
        logger.error(
            "Failed to persist failed-prediction record", exc_info=True
        )
        return None
