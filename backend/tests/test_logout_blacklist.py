"""Tests for logout with Redis token blacklist."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token
from app.main import app


@pytest.fixture
def valid_token():
    """Create a valid JWT access token for testing."""
    return create_access_token(
        data={"sub": "test-user-id", "role": "student", "email": "test@example.com"}
    )


@pytest.mark.asyncio
async def test_logout_blacklists_token(valid_token):
    """POST /api/auth/logout should blacklist the JWT in Redis."""
    with patch("app.auth.router.blacklist_token", new_callable=AsyncMock) as mock_blacklist:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Mock the blacklist check to not block this token yet
            with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
                resp = await client.post(
                    "/api/auth/logout",
                    headers={"Authorization": f"Bearer {valid_token}"},
                )

        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"
        mock_blacklist.assert_called_once()
        call_args = mock_blacklist.call_args
        assert call_args[0][1] > 0  # TTL should be positive


@pytest.mark.asyncio
async def test_blacklisted_token_rejected(valid_token):
    """A blacklisted token should be rejected with 401."""
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=True):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {valid_token}"},
            )

        assert resp.status_code == 401
        assert "revoked" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_non_blacklisted_token_works(valid_token):
    """A valid non-blacklisted token should work normally."""
    with patch("app.auth.dependencies.is_token_blacklisted", return_value=False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {valid_token}"},
            )

        assert resp.status_code == 200
        assert resp.json()["user_id"] == "test-user-id"
