"""Tests for S5: Security access control — 401 for unauthenticated/invalid access."""

import uuid
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture()
async def client():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as ac:
        yield ac


class TestUnauthorizedAccess:
    """All protected endpoints must return 401 without valid credentials."""

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_expired_jwt_returns_401(self, client: AsyncClient) -> None:
        from app.auth.jwt import create_access_token

        token = create_access_token(
            data={"sub": str(uuid.uuid4()), "role": "student"},
            expires_delta=timedelta(seconds=-1),
        )
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_api_key_returns_401(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/auth/me",
            headers={"X-API-Key": "ndqs_invalid_key_here"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_malformed_bearer_returns_401(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_empty_bearer_returns_401(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_expired_token_returns_401(self, client: AsyncClient) -> None:
        from app.auth.jwt import create_refresh_token

        token = create_refresh_token(
            data={"sub": str(uuid.uuid4())},
            expires_delta=timedelta(seconds=-1),
        )
        response = await client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_key_generate_without_auth_returns_401(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "test"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_key_list_without_auth_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/api-key/list")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_api_key_revoke_without_auth_returns_401(self, client: AsyncClient) -> None:
        response = await client.delete(f"/api/auth/api-key/revoke/{uuid.uuid4()}")
        assert response.status_code == 401
