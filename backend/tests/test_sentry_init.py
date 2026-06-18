"""Tests for optional Sentry initialisation (B8).

Sentry must be a no-op when SENTRY_DSN is unset so that local/dev
runs work without any DSN configured.
"""
from app.config import settings
from app.main import init_sentry


def test_init_sentry_skips_without_dsn(monkeypatch):
    monkeypatch.setattr(settings, "SENTRY_DSN", None)
    called = {}
    monkeypatch.setattr("app.main.sentry_sdk.init", lambda **kw: called.setdefault("x", kw))
    init_sentry()
    assert "x" not in called


def test_init_sentry_runs_with_dsn(monkeypatch):
    monkeypatch.setattr(settings, "SENTRY_DSN", "https://x@y/1")
    called = {}
    monkeypatch.setattr("app.main.sentry_sdk.init", lambda **kw: called.setdefault("x", kw))
    init_sentry()
    assert called["x"]["dsn"] == "https://x@y/1"
