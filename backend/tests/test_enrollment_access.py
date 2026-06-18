"""Task 1 — close the free-access bypass.

Self-service enrollment must be service-token-only, and quest content +
evaluation must require an active enrollment. Without these gates, any
logged-in user could self-enroll in any published course for free and
consume quest/eval endpoints.
"""

import uuid  # noqa: F401  (kept for parity with sibling test modules)
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
