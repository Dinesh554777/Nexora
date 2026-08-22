import pytest

from config import settings
from database.connection import dispose_engine


@pytest.fixture(autouse=True)
def isolated_test_configuration(monkeypatch):
    """Runs every test with persistence disabled unless a test opts in.

    Keeps the suite hermetic: tests never touch the developer's real
    PostgreSQL instance from backend/.env. Database tests override
    settings.DATABASE_URL with their own throwaway SQLite URL.
    """
    monkeypatch.setattr(settings, "DATABASE_URL", None)
    dispose_engine()
    yield
    dispose_engine()
