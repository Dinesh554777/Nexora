import logging
import threading
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from config import settings

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_engine_lock = threading.Lock()


def _is_sqlite_url(url: str) -> bool:
    return url.strip().lower().startswith("sqlite")


def get_engine() -> Engine:
    """Returns the shared SQLAlchemy engine, creating it lazily on first use.

    The engine is created only when database access is actually attempted so
    the application can still boot without DATABASE_URL configured.
    Raises a ValueError with a safe message when DATABASE_URL is missing.
    """
    global _engine, _session_factory
    if _engine is not None:
        return _engine

    with _engine_lock:
        if _engine is not None:
            return _engine

        url = settings.require_database_url()

        engine_kwargs: dict = {
            "pool_pre_ping": True,
            "future": True,
        }
        connect_args: dict = {}
        if _is_sqlite_url(url):
            # SQLite connections are per-request; allow cross-thread usage in
            # test servers without weakening PostgreSQL behavior.
            connect_args["check_same_thread"] = False
        else:
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10
            # Fail fast when PostgreSQL is unreachable instead of hanging.
            connect_args["connect_timeout"] = 5
        if connect_args:
            engine_kwargs["connect_args"] = connect_args

        new_engine = create_engine(url, **engine_kwargs)
        _session_factory = sessionmaker(
            bind=new_engine,
            autoflush=False,
            expire_on_commit=False,
            future=True,
        )
        _engine = new_engine
        logger.info(
            "Database engine initialized for %s",
            settings.mask_connection_string(url),
        )
        return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Returns the session factory bound to the shared engine."""
    get_engine()
    assert _session_factory is not None
    return _session_factory


@contextmanager
def session_scope():
    """Provides a transactional session scope.

    Commits when the block exits cleanly; rolls back and re-raises on error;
    always closes the session. Callers must not commit/rollback manually
    unless composing an explicit multi-step transaction.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_database_connection() -> tuple[bool, str]:
    """Executes SELECT 1 to verify connectivity.

    Returns (ok, detail). `detail` is always safe for logs/API responses:
    it contains at most the masked connection string and never credentials,
    full URLs, or stack traces.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "database connection ok"
    except ValueError as e:
        return False, str(e)
    except SQLAlchemyError:
        logger.warning("Database connectivity check failed", exc_info=True)
        return (
            False,
            "database connection failed. Check that PostgreSQL is running "
            "and that DATABASE_URL is configured correctly.",
        )


def dispose_engine() -> None:
    """Disposes the shared engine and resets singletons.

    Used by tests and graceful shutdown so pooled connections are never leaked.
    """
    global _engine, _session_factory
    with _engine_lock:
        if _engine is not None:
            _engine.dispose()
        _engine = None
        _session_factory = None
