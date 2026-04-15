"""Tests for S6: CSRF protection — Origin validation on state-changing requests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict:
    from app.auth.jwt import create_access_token

    token = create_access_token(
        data={"sub": str(uuid.uuid4()), "role": "student", "email": "test@example.com"}
    )
    return {"Authorization": f"Bearer {token}"}


class TestCSRFProtection:
    @pytest.mark.asyncio
    async def test_post_with_wrong_origin_rejected(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """POST from unknown origin should be rejected with 403."""
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "csrf-test"},
            headers={**auth_headers, "Origin": "http://evil.com"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_post_with_valid_origin_accepted(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """POST from allowed origin should succeed."""
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "csrf-test"},
            headers={**auth_headers, "Origin": "http://localhost:3000"},
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_post_without_origin_accepted(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """POST without Origin header is accepted (server-to-server / API key usage)."""
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "csrf-test"},
            headers=auth_headers,
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_get_with_wrong_origin_accepted(self, client: AsyncClient) -> None:
        """GET requests are safe methods — origin check should not apply."""
        response = await client.get(
            "/api/health",
            headers={"Origin": "http://evil.com"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_with_wrong_origin_rejected(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """DELETE from unknown origin should be rejected."""
        response = await client.delete(
            f"/api/auth/api-key/revoke/{uuid.uuid4()}",
            headers={**auth_headers, "Origin": "http://evil.com"},
        )
        assert response.status_code == 403
