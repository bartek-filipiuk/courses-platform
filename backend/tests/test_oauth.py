"""Tests for GitHub OAuth callback and user upsert."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def mock_github_responses():
    """Mock GitHub API responses for OAuth flow."""
    token_response = MagicMock()
    token_response.status_code = 200
    token_response.json.return_value = {"access_token": "gh_test_token_123"}

    user_response = MagicMock()
    user_response.status_code = 200
    user_response.json.return_value = {
        "id": 12345,
        "login": "testuser",
        "name": "Test User",
        "email": "test@example.com",
        "avatar_url": "https://github.com/avatar.jpg",
    }

    return token_response, user_response


@pytest.mark.asyncio
async def test_github_login_redirects():
    """GET /api/auth/github/login redirects to GitHub OAuth."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/github/login", follow_redirects=False)
    assert resp.status_code == 302
    assert "github.com/login/oauth/authorize" in resp.headers["location"]


@pytest.mark.asyncio
async def test_github_callback_missing_code():
    """GET /api/auth/github/callback without code returns 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/github/callback")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_github_callback_invalid_code(mock_github_responses):
    """GET /api/auth/github/callback with invalid code returns 400."""
    error_response = MagicMock()
    error_response.status_code = 200
    error_response.json.return_value = {"error": "bad_verification_code"}

    with patch("app.auth.oauth.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = error_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auth/github/callback?code=invalid_code")
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_github_callback_success(mock_github_responses):
    """GET /api/auth/github/callback with valid code returns JWT tokens."""
    token_resp, user_resp = mock_github_responses

    # Mock user object
    mock_user = MagicMock()
    mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
    mock_user.email = "test@example.com"
    mock_user.display_name = "Test User"
    mock_user.role = "student"

    with (
        patch("app.auth.router.exchange_code_for_token", return_value="gh_test_token_123"),
        patch("app.auth.router.fetch_github_profile", return_value={
            "provider_id": "12345",
            "email": "test@example.com",
            "display_name": "Test User",
            "avatar_url": "https://github.com/avatar.jpg",
        }),
        patch("app.auth.router.upsert_user", return_value=mock_user),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/auth/github/callback?code=valid_code")

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
