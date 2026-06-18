import pytest
from fastapi import HTTPException
from app.admin.deps import require_service_token
from app.config import settings


def test_service_token_rejects_when_missing(monkeypatch):
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    with pytest.raises(HTTPException) as e:
        require_service_token(None)
    assert e.value.status_code == 401


def test_service_token_rejects_wrong(monkeypatch):
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    with pytest.raises(HTTPException) as e:
        require_service_token("nope")
    assert e.value.status_code == 401


def test_service_token_accepts_correct(monkeypatch):
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    assert require_service_token("secret") is None
