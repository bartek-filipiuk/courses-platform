import uuid
from datetime import datetime, timezone
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
async def test_re_enroll_after_revoke_clears_revoked_at(monkeypatch):
    """Re-purchase after a refund/chargeback must RESTORE access.

    A previously-REVOKED user already has an Enrollment row (with revoked_at
    set). Re-paying via the canonical paid path must clear revoked_at so the
    enrollment guards (which require `revoked_at IS NULL`) stop 403-ing. Quest
    states already exist from the original enroll, so initialize_quest_states
    must NOT run again (it is not idempotent — re-running violates the
    uq_quest_states_user_quest unique constraint).
    """
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    db = AsyncMock()
    existing_user = MagicMock()
    existing_user.id = uuid.uuid4()
    existing_user.email = "buyer@x.pl"
    course = MagicMock()
    course.is_published = True
    revoked_enrollment = MagicMock()
    revoked_enrollment.revoked_at = datetime.now(timezone.utc)  # was revoked
    # 1st: user lookup -> existing ; 2nd: course lookup -> course ;
    # 3rd: enrollment lookup -> existing-but-revoked
    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = existing_user
    course_res = MagicMock()
    course_res.scalar_one_or_none.return_value = course
    enr_res = MagicMock()
    enr_res.scalar_one_or_none.return_value = revoked_enrollment
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
            # Access RESTORED: revoked_at was cleared and the re-grant committed.
            assert revoked_enrollment.revoked_at is None
            db.commit.assert_awaited()
            # No NEW enrollment row inserted (the existing row was re-granted).
            db.add.assert_not_called()
            # Quest states already exist -> must NOT be re-initialized.
            iqs.assert_not_awaited()
            # Welcome magic-link is always (re)sent.
            send.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_enroll_existing_active_user_does_not_touch_revoked_at(monkeypatch):
    """An idempotent re-enroll of an already-ACTIVE user must not commit a
    spurious re-grant: revoked_at is already None, so no UPDATE/commit for it."""
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    db = AsyncMock()
    existing_user = MagicMock()
    existing_user.id = uuid.uuid4()
    existing_user.email = "buyer@x.pl"
    course = MagicMock()
    course.is_published = True
    active_enrollment = MagicMock()
    active_enrollment.revoked_at = None  # already active
    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = existing_user
    course_res = MagicMock()
    course_res.scalar_one_or_none.return_value = course
    enr_res = MagicMock()
    enr_res.scalar_one_or_none.return_value = active_enrollment
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
            assert r.json()["status"] == "enrolled"
            assert active_enrollment.revoked_at is None
            db.add.assert_not_called()
            iqs.assert_not_awaited()
            # No DB commit needed for an already-active enrollment.
            db.commit.assert_not_awaited()
            send.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_enroll_succeeds_when_welcome_email_fails(monkeypatch):
    """A transient Brevo failure must NOT fail an already-successful enrollment.

    Spec §7: the welcome email is BEST-EFFORT. send_magic_link_email raises
    RuntimeError on any non-2xx Brevo response (e.g. a re-delivered webhook), but
    the new-user enroll path must still commit and return 201 / status="enrolled".
    """
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
            patch(
                "app.admin.service.send_magic_link_email",
                AsyncMock(side_effect=RuntimeError("brevo 500")),
            ) as send,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://t"
            ) as c:
                r = await c.post(
                    "/api/admin/enroll-by-email",
                    headers={"X-Service-Token": "secret"},
                    json={"email": "buyer@x.pl", "course_id": str(uuid.uuid4())},
                )
            # Enrollment is NOT rolled back by an email failure.
            assert r.status_code == 201
            body = r.json()
            assert body["status"] == "enrolled"
            assert body["created_user"] is True
            iqs.assert_awaited_once()
            # The send was attempted (and failed), but it was best-effort.
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


@pytest.mark.asyncio
async def test_revoke_sets_revoked_at(monkeypatch):
    """With the service token, revoke-enrollment finds the enrollment, stamps
    revoked_at, commits, and returns status='revoked'."""
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    db = AsyncMock()
    existing_user = MagicMock()
    existing_user.id = uuid.uuid4()
    existing_user.email = "buyer@x.pl"
    enrollment = MagicMock()
    enrollment.revoked_at = None
    # 1st execute: user lookup -> existing ; 2nd: enrollment lookup -> enrollment
    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = existing_user
    enr_res = MagicMock()
    enr_res.scalar_one_or_none.return_value = enrollment
    db.execute.side_effect = [user_res, enr_res]
    app.dependency_overrides[get_db] = _override_db(db)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://t"
        ) as c:
            r = await c.post(
                "/api/admin/revoke-enrollment",
                headers={"X-Service-Token": "secret"},
                json={"email": "buyer@x.pl", "course_id": str(uuid.uuid4())},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "revoked"
        assert enrollment.revoked_at is not None
        db.commit.assert_awaited()
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_revoke_missing_enrollment_is_idempotent(monkeypatch):
    """Revoking a non-existent enrollment returns status='not_found' (idempotent,
    no commit, no crash)."""
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    db = AsyncMock()
    user_res = MagicMock()
    user_res.scalar_one_or_none.return_value = None  # no such user
    db.execute.side_effect = [user_res]
    app.dependency_overrides[get_db] = _override_db(db)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://t"
        ) as c:
            r = await c.post(
                "/api/admin/revoke-enrollment",
                headers={"X-Service-Token": "secret"},
                json={"email": "ghost@x.pl", "course_id": str(uuid.uuid4())},
            )
        assert r.status_code == 200
        assert r.json()["status"] == "not_found"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_revoke_rejects_bad_service_token(monkeypatch):
    monkeypatch.setattr(settings, "NDQS_SERVICE_TOKEN", "secret")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post(
            "/api/admin/revoke-enrollment",
            headers={"X-Service-Token": "wrong"},
            json={"email": "x@y.pl", "course_id": str(uuid.uuid4())},
        )
    assert r.status_code == 401
