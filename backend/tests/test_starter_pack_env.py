"""TDD — Task B9: starter-pack .env.example must use BACKEND_URL, not localhost:8002."""

import pytest

from app.config import settings
from app.courses.router import build_starter_env


def test_starter_env_uses_backend_url(monkeypatch):
    monkeypatch.setattr(settings, "BACKEND_URL", "https://api.learn.devince.dev")
    env = build_starter_env(settings.BACKEND_URL)
    assert "https://api.learn.devince.dev" in env
    assert "localhost:8002" not in env


def test_starter_env_contains_api_key_placeholder():
    """The .env.example must still document NDQS_API_KEY."""
    env = build_starter_env(settings.BACKEND_URL)
    assert "NDQS_API_KEY" in env
