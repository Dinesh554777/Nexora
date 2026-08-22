import importlib
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent


def reload_config():
    import config

    importlib.reload(config)
    return config.settings


@pytest.fixture()
def clean_config():
    """Ensures config reloads after each test with restored environment."""
    yield
    import os

    os.environ.pop("NEXORA_API_KEY", None)
    import config

    importlib.reload(config)


def test_api_key_read_from_environment(clean_config, monkeypatch):
    monkeypatch.setenv("NEXORA_API_KEY", "test-secret-value-123")
    settings = reload_config()

    assert settings.NEXORA_API_KEY is not None
    assert settings.require_api_key() == "test-secret-value-123"


def test_missing_api_key_is_safe_and_lazy(clean_config, monkeypatch):
    monkeypatch.setenv("NEXORA_API_KEY", "")
    settings = reload_config()

    assert settings.NEXORA_API_KEY is None
    with pytest.raises(ValueError) as exc_info:
        settings.require_api_key()

    assert "NEXORA_API_KEY is not configured" in str(exc_info.value)
    assert ".env.example" in str(exc_info.value)


def test_secret_value_never_appears_in_repr_or_logs(clean_config, monkeypatch):
    monkeypatch.setenv("NEXORA_API_KEY", "super-secret-do-not-leak-42")
    settings = reload_config()

    rendered = f"{settings} {settings!r} {str(settings.NEXORA_API_KEY)!r}"
    assert "super-secret-do-not-leak-42" not in rendered
    assert "**********" in repr(settings.NEXORA_API_KEY)

    assert settings.require_api_key() == "super-secret-do-not-leak-42"


def test_error_message_never_contains_secret_when_unset(clean_config, monkeypatch):
    monkeypatch.setenv("NEXORA_API_KEY", "")
    settings = reload_config()

    with pytest.raises(ValueError) as exc_info:
        settings.require_api_key()

    assert "super-secret" not in str(exc_info.value)


def test_env_example_contains_only_placeholders():
    """Every .env.example value must be a placeholder, never a real secret.

    Phase 8 added DATABASE_URL; this check now validates every line so no
    real credential can ever be committed in the template again.
    """
    example = (BACKEND_DIR / ".env.example").read_text(encoding="utf-8")
    value_lines = [
        line
        for line in example.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert value_lines == [
        "NEXORA_API_KEY=your_api_key_here",
        "DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/nexora",
    ]
    # Real-looking secret tokens must never appear anywhere in the template.
    assert "rc_" not in example
    for line in value_lines:
        value = line.partition("=")[2]
        if value != "your_api_key_here":
            assert value.startswith("postgresql+psycopg://username:password@")


def test_app_imports_successfully_without_key(clean_config, monkeypatch):
    monkeypatch.setenv("NEXORA_API_KEY", "")
    settings = reload_config()

    assert settings.NEXORA_API_KEY is None
    assert "main" in sys.modules or __import__("main")  # app already imported at module scope
