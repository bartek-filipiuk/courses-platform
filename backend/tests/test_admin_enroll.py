import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.admin.deps import require_service_token
from app.config import settings
from app.database import get_db
from app.main import app


def _override_db(db):
    async def _f():
        yield db

    return _f


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


@pytest.mark.asyncio
async def test_enroll_creates_user_and_enrollment(monkeypatch):
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    db = AsyncMock()
    course = MagicMock()
    course.is_published = True
    # 1st execute: user lookup -> None ; 2nd: course lookup -> course ; 3rd: enrollment lookup -> None
    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = None
    course_res = MagicMock()
    course_res.scalar_one_or_none.return_value = course
    enr_res = MagicMock()
    enr_res.scalar_one_or_none.return_value = None
    db.execute.side_effect = [user_res, course_res, enr_res]
    app.dependency_overrides[get_db] = _override_db(db)
    try:
        with (
            patch("app.admin.service.initialize_quest_states", AsyncMock()) as iqs,
            patch("app.admin.service.send_magic_link_email", AsyncMock()) as send,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://t"
            ) as c:
                r = await c.post(
                    "/api/admin/enroll-by-email",
                    headers={"X-Service-Token": "secret"},
                    json={"email": "buyer@x.pl", "course_id": str(uuid.uuid4())},
                )
            assert r.status_code == 201
            body = r.json()
            assert body["status"] == "enrolled"
            assert body["created_user"] is True
            iqs.assert_awaited_once()
            send.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_enroll_existing_user_is_idempotent(monkeypatch):
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    db = AsyncMock()
    existing_user = MagicMock()
    existing_user.id = uuid.uuid4()
    existing_user.email = "buyer@x.pl"
    course = MagicMock()
    course.is_published = True
    existing_enr = MagicMock()
    # 1st: user lookup -> existing ; 2nd: course lookup -> course ; 3rd: enrollment -> existing
    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = existing_user
    course_res = MagicMock()
    course_res.scalar_one_or_none.return_value = course
    enr_res = MagicMock()
    enr_res.scalar_one_or_none.return_value = existing_enr
    db.execute.side_effect = [user_res, course_res, enr_res]
    app.dependency_overrides[get_db] = _override_db(db)
    try:
        with (
            patch("app.admin.service.initialize_quest_states", AsyncMock()) as iqs,
            patch("app.admin.service.send_magic_link_email", AsyncMock()) as send,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://t"
            ) as c:
                r = await c.post(
                    "/api/admin/enroll-by-email",
                    headers={"X-Service-Token": "secret"},
                    json={"email": "buyer@x.pl", "course_id": str(uuid.uuid4())},
                )
            assert r.status_code == 201
            body = r.json()
            assert body["status"] == "enrolled"
            assert body["created_user"] is False
            # No new user, no new enrollment created
            db.add.assert_not_called()
            # Quest states must NOT be re-initialized for an existing enrollment
            iqs.assert_not_awaited()
            # Welcome magic-link is always (re)sent
            send.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_enroll_rejects_bad_service_token(monkeypatch):
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post(
            "/api/admin/enroll-by-email",
            headers={"X-Service-Token": "wrong"},
            json={"email": "x@y.pl", "course_id": str(uuid.uuid4())},
        )
    assert r.status_code == 401
