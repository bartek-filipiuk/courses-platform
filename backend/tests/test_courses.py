"""Tests for Course CRUD, Enrollment, and Starter Pack."""

import io
import zipfile
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token
from app.database import get_db
from app.main import app

ADMIN_ID = str(uuid4())
STUDENT_ID = str(uuid4())
COURSE_ID = str(uuid4())


@pytest.fixture
def admin_token():
    return create_access_token(data={"sub": ADMIN_ID, "role": "admin", "email": "admin@test.com"})


@pytest.fixture
def student_token():
    return create_access_token(data={"sub": STUDENT_ID, "role": "student", "email": "student@test.com"})


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.refresh = AsyncMock()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    yield db
    app.dependency_overrides.pop(get_db, None)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _mock_course(**overrides):
    from datetime import datetime, timezone
    defaults = {
        "id": uuid4(),
        "creator_id": uuid4(),
        "title": "Test Course",
        "narrative_title": "Operation Test",
        "description": "A test course",
        "global_context": "Test context",
        "persona_name": "ORACLE",
        "persona_prompt": "You are ORACLE",
        "cover_image_url": None,
        "model_id": "claude-sonnet-4-6",
        "is_published": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


# --- Admin CRUD ---


@pytest.mark.asyncio
async def test_create_course_as_admin(admin_token, mock_db):
    """POST /api/admin/courses — admin can create course."""
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/courses",
                json={"title": "My Course", "description": "A new course"},
                headers=_auth(admin_token),
            )
        assert resp.status_code == 201
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_course_as_student_forbidden(student_token):
    """POST /api/admin/courses — student gets 403."""
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/courses",
                json={"title": "Hack"},
                headers=_auth(student_token),
            )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_course_blank_title_rejected(admin_token):
    """POST /api/admin/courses — blank title rejected."""
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/admin/courses",
                json={"title": "   "},
                headers=_auth(admin_token),
            )
        assert resp.status_code == 422


# --- List courses ---


@pytest.mark.asyncio
async def test_list_courses(student_token, mock_db):
    """GET /api/courses — returns published courses."""
    mock_course = _mock_course()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_course]
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/courses", headers=_auth(student_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Course"


# --- Enrollment ---


@pytest.mark.asyncio
async def test_enroll_success(student_token, mock_db):
    """POST /api/courses/{id}/enroll — student can enroll."""
    mock_course = _mock_course(is_published=True)

    # First execute: find course. Second: check existing enrollment.
    mock_result_course = MagicMock()
    mock_result_course.scalar_one_or_none.return_value = mock_course
    mock_result_enroll = MagicMock()
    mock_result_enroll.scalar_one_or_none.return_value = None
    mock_db.execute.side_effect = [mock_result_course, mock_result_enroll]

    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/courses/{mock_course.id}/enroll",
                headers=_auth(student_token),
            )
        assert resp.status_code == 201
        mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_enroll_without_auth():
    """POST /api/courses/{id}/enroll — no auth returns 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(f"/api/courses/{uuid4()}/enroll")
    assert resp.status_code == 401


# --- Starter Pack ---


@pytest.mark.asyncio
async def test_starter_pack_download(student_token, mock_db):
    """GET /api/courses/{id}/starter-pack — returns ZIP with CLAUDE.md, .env.example, README."""
    mock_course = _mock_course(persona_prompt="You are ORACLE, a rogue AI.")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_course
    mock_db.execute.return_value = mock_result

    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                f"/api/courses/{mock_course.id}/starter-pack",
                headers=_auth(student_token),
            )
        assert resp.status_code == 200
        assert "application/zip" in resp.headers["content-type"]

        # Verify ZIP contents
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = zf.namelist()
        assert "CLAUDE.md" in names
        assert ".env.example" in names
        assert "README.md" in names

        claude_content = zf.read("CLAUDE.md").decode()
        assert "ORACLE" in claude_content
