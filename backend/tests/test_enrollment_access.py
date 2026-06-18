"""Task 1 — close the free-access bypass.

Self-service enrollment must be service-token-only, and quest content +
evaluation must require an active enrollment. Without these gates, any
logged-in user could self-enroll in any published course for free and
consume quest/eval endpoints.
"""

import uuid  # noqa: F401  (kept for parity with sibling test modules)
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token
from app.database import get_db
from app.main import app


@pytest.fixture
def student_token():
    return create_access_token(data={"sub": str(uuid4()), "role": "student", "email": "s@t.com"})


def _override(db):
    async def f():
        yield db
    app.dependency_overrides[get_db] = f


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_enroll_without_service_token_is_blocked(student_token):
    """Self-service enroll with a JWT but no X-Service-Token is rejected."""
    db = AsyncMock()
    _override(db)
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post(
                f"/api/courses/{uuid4()}/enroll", headers=_auth(student_token)
            )
        assert r.status_code in (401, 403)
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_submit_for_non_enrolled_user_403(student_token):
    """submit for a quest whose course the user is NOT enrolled in -> 403."""
    db = AsyncMock()
    # quest lookup ok, enrollment lookup -> None (not enrolled)
    quest = MagicMock()
    quest.evaluation_type = "text_answer"
    quest.id = uuid4()
    qres = MagicMock()
    qres.scalar_one_or_none.return_value = quest
    enr = MagicMock()
    enr.first.return_value = None
    db.execute.side_effect = [qres, enr]
    _override(db)
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post(
                f"/api/quests/{quest.id}/submit",
                headers=_auth(student_token),
                json={"type": "text_answer", "payload": {"answer": "x"}},
            )
        assert r.status_code == 403
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_briefing_for_non_enrolled_user_403(student_token):
    """briefing for a quest whose course the user is NOT enrolled in -> 403.

    The quest_state is AVAILABLE (so the legacy LOCKED gate passes), but the
    enrollment check must still reject because there is no enrollment row.
    """
    db = AsyncMock()
    quest_id = uuid4()

    qs = MagicMock()
    qs.state = "AVAILABLE"
    enr = MagicMock()
    enr.first.return_value = None
    # briefing order: quest_state lookup, then enrollment check
    qsres = MagicMock()
    qsres.scalar_one_or_none.return_value = qs
    db.execute.side_effect = [qsres, enr]
    _override(db)
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.get(
                f"/api/quests/{quest_id}/briefing", headers=_auth(student_token)
            )
        assert r.status_code == 403
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_hint_for_non_enrolled_user_403(student_token):
    """hint for a quest whose course the user is NOT enrolled in -> 403."""
    db = AsyncMock()
    quest = MagicMock()
    quest.id = uuid4()
    qres = MagicMock()
    qres.scalar_one_or_none.return_value = quest
    enr = MagicMock()
    enr.first.return_value = None
    db.execute.side_effect = [qres, enr]
    _override(db)
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post(
                f"/api/quests/{quest.id}/hint",
                headers=_auth(student_token),
                json={"context": "stuck"},
            )
        assert r.status_code == 403
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_course_quests_for_non_enrolled_user_403(student_token):
    """GET /api/courses/{id}/quests for a non-enrolled user -> 403.

    The quest list leaks every quest's title/skills/evaluation_type, so it must
    be gated by an active enrollment before the list query runs.
    """
    db = AsyncMock()
    course_id = uuid4()
    # enrollment check is the first (and only) execute -> None means not enrolled
    enr = MagicMock()
    enr.first.return_value = None
    db.execute.side_effect = [enr]
    _override(db)
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.get(
                f"/api/courses/{course_id}/quests", headers=_auth(student_token)
            )
        assert r.status_code == 403
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_starter_pack_for_non_enrolled_user_403(student_token):
    """GET /api/courses/{id}/starter-pack for a non-enrolled user -> 403.

    The starter pack streams persona_prompt + global_context (the Game-Master
    IP), so it must require an active enrollment before streaming.
    """
    db = AsyncMock()
    course_id = uuid4()
    course = MagicMock()
    course.id = course_id
    course.title = "Locked Course"
    cres = MagicMock()
    cres.scalar_one_or_none.return_value = course
    enr = MagicMock()
    enr.first.return_value = None
    # course lookup, then enrollment check -> None (not enrolled)
    db.execute.side_effect = [cres, enr]
    _override(db)
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.get(
                f"/api/courses/{course_id}/starter-pack", headers=_auth(student_token)
            )
        assert r.status_code == 403
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_submit_for_revoked_enrollment_403(student_token):
    """submit for a quest in a course the user WAS enrolled in but has been
    REVOKED (refund/chargeback) -> 403.

    Task 8 adds `Enrollment.revoked_at IS NULL` to the access query, so a row
    with a non-None revoked_at no longer matches and `.first()` returns None.
    The mock models that filtered query: the revoked enrollment is excluded, so
    the guard must reject the request even though the user once had access.
    """
    db = AsyncMock()
    quest = MagicMock()
    quest.evaluation_type = "text_answer"
    quest.id = uuid4()
    qres = MagicMock()
    qres.scalar_one_or_none.return_value = quest
    # The enrollment exists but is revoked; the `revoked_at IS NULL` clause in
    # the access query excludes it, so the filtered lookup yields no row.
    revoked_enrollment = MagicMock()
    revoked_enrollment.revoked_at = datetime.now(timezone.utc)
    enr = MagicMock()
    enr.first.return_value = None  # revoked row filtered out by revoked_at IS NULL
    db.execute.side_effect = [qres, enr]
    _override(db)
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post(
                f"/api/quests/{quest.id}/submit",
                headers=_auth(student_token),
                json={"type": "text_answer", "payload": {"answer": "x"}},
            )
        assert r.status_code == 403
    app.dependency_overrides.pop(get_db, None)
