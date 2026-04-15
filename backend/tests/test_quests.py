"""Tests for Quest Engine — FSM, artifacts, API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token
from app.database import get_db
from app.main import app
from app.quests.state_machine import TRANSITIONS, can_transition, _sign_artifact


# --- FSM unit tests ---


def test_valid_transitions():
    assert can_transition("LOCKED", "AVAILABLE")
    assert can_transition("AVAILABLE", "IN_PROGRESS")
    assert can_transition("IN_PROGRESS", "EVALUATING")
    assert can_transition("EVALUATING", "COMPLETED")
    assert can_transition("EVALUATING", "FAILED_ATTEMPT")
    assert can_transition("FAILED_ATTEMPT", "IN_PROGRESS")


def test_invalid_transitions():
    assert not can_transition("LOCKED", "COMPLETED")
    assert not can_transition("AVAILABLE", "COMPLETED")
    assert not can_transition("COMPLETED", "AVAILABLE")
    assert not can_transition("IN_PROGRESS", "LOCKED")
    assert not can_transition("COMPLETED", "IN_PROGRESS")


def test_artifact_signature_deterministic():
    user_id = uuid4()
    artifact_id = uuid4()
    sig1 = _sign_artifact(user_id, artifact_id)
    sig2 = _sign_artifact(user_id, artifact_id)
    assert sig1 == sig2
    assert len(sig1) == 64  # SHA256 hex


def test_artifact_signature_differs_per_user():
    artifact_id = uuid4()
    sig1 = _sign_artifact(uuid4(), artifact_id)
    sig2 = _sign_artifact(uuid4(), artifact_id)
    assert sig1 != sig2


# --- API tests ---


@pytest.fixture
def student_token():
    return create_access_token(data={"sub": str(uuid4()), "role": "student", "email": "s@test.com"})


@pytest.fixture
def admin_token():
    return create_access_token(data={"sub": str(uuid4()), "role": "admin", "email": "a@test.com"})


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    async def override():
        yield db
    app.dependency_overrides[get_db] = override
    yield db
    app.dependency_overrides.pop(get_db, None)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_briefing_locked_quest_returns_403(student_token, mock_db):
    """Briefing for LOCKED quest returns 403."""
    mock_qs = MagicMock()
    mock_qs.state = "LOCKED"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_qs
    mock_db.execute.return_value = mock_result

    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/quests/{uuid4()}/briefing",
                headers=_auth(student_token),
            )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_briefing_available_quest_returns_200(student_token, mock_db):
    """Briefing for AVAILABLE quest returns 200 and transitions to IN_PROGRESS."""
    quest_id = uuid4()

    mock_qs = MagicMock()
    mock_qs.state = "AVAILABLE"
    mock_qs.started_at = None

    mock_quest = MagicMock()
    mock_quest.id = quest_id
    mock_quest.title = "Test Quest"
    mock_quest.briefing = "Your mission..."
    mock_quest.evaluation_type = "text_answer"
    mock_quest.max_hints = 3
    mock_quest.skills = ["Python", "API"]

    # First call: get quest_state, second: get quest
    mock_result_qs = MagicMock()
    mock_result_qs.scalar_one_or_none.return_value = mock_qs
    mock_result_quest = MagicMock()
    mock_result_quest.scalar_one_or_none.return_value = mock_quest
    mock_db.execute.side_effect = [mock_result_qs, mock_result_quest]

    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/quests/{quest_id}/briefing",
                headers=_auth(student_token),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Quest"
        assert data["briefing"] == "Your mission..."


@pytest.mark.asyncio
async def test_admin_create_quest(admin_token, mock_db):
    """Admin can create a quest with artifact."""
    course_id = uuid4()

    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/quests",
                json={
                    "course_id": str(course_id),
                    "sort_order": 1,
                    "title": "First Quest",
                    "briefing": "Build the API",
                    "evaluation_type": "text_answer",
                    "artifact_name": "BLUEPRINT-KEY",
                    "artifact_description": "The blueprint for NEXUS network",
                },
                headers=_auth(admin_token),
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "First Quest"
        assert data["artifact_id"] is not None
        mock_db.add.assert_called()


@pytest.mark.asyncio
async def test_student_cannot_create_quest(student_token):
    """Student cannot create quests."""
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/quests",
                json={
                    "course_id": str(uuid4()),
                    "sort_order": 1,
                    "title": "Hack",
                    "briefing": "Nope",
                    "evaluation_type": "text_answer",
                },
                headers=_auth(student_token),
            )
        assert resp.status_code == 403
