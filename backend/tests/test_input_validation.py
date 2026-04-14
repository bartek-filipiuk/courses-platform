"""Tests for S1: Input validation — Pydantic schemas on auth endpoints, reject malformed requests."""

import uuid

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


@pytest.fixture()
def auth_headers() -> dict:
    from app.auth.jwt import create_access_token

    user_id = str(uuid.uuid4())
    token = create_access_token(
        data={"sub": user_id, "role": "student", "email": "test@example.com"}
    )
    return {"Authorization": f"Bearer {token}"}


class TestApiKeyGenerateValidation:
    """POST /api/auth/api-key/generate — name field validation."""

    @pytest.mark.asyncio
    async def test_empty_name_rejected(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_name_too_long_rejected(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "a" * 256},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_name_rejected(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_name_whitespace_only_rejected(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "   "},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_name_accepted(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "My CLI Key"},
            headers=auth_headers,
        )
        assert response.status_code == 201


class TestApiKeyRevokeValidation:
    """DELETE /api/auth/api-key/revoke/{key_id} — key_id must be valid UUID."""

    @pytest.mark.asyncio
    async def test_invalid_key_id_rejected(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.delete(
            "/api/auth/api-key/revoke/not-a-uuid",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_uuid_key_id_accepted(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Valid UUID key_id should return 404 (not found) not 422 (validation error)."""
        response = await client.delete(
            f"/api/auth/api-key/revoke/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGithubCallbackValidation:
    """GET /api/auth/github/callback — code param validation."""

    @pytest.mark.asyncio
    async def test_missing_code_rejected(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/github/callback")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_code_rejected(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/github/callback?code=")
        assert response.status_code == 422


class TestValidationErrorFormat:
    """Validation errors should return structured JSON without DB schema leaks."""

    @pytest.mark.asyncio
    async def test_validation_error_returns_json(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_validation_error_does_not_leak_internals(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Validation errors should not reveal database table names or column details."""
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422
        body = response.text.lower()
        assert "sqlalchemy" not in body
        assert "postgresql" not in body
        assert "table" not in body
