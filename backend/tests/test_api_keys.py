"""Tests for API Key system — model, generate, revoke, list, auth via API Key."""

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


class TestApiKeyModel:
    def test_api_key_model_exists(self) -> None:
        from app.auth.models import ApiKey

        assert ApiKey is not None

    def test_api_key_has_required_columns(self) -> None:
        from app.auth.models import ApiKey

        column_names = {c.name for c in ApiKey.__table__.columns}
        required = {"id", "user_id", "key_hash", "key_prefix", "name", "expires_at", "created_at", "is_active"}
        assert required.issubset(column_names), f"Missing columns: {required - column_names}"

    def test_api_key_table_name(self) -> None:
        from app.auth.models import ApiKey

        assert ApiKey.__tablename__ == "api_keys"


class TestApiKeyEndpoints:
    @pytest.mark.asyncio
    async def test_generate_without_auth_returns_401(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/api-key/generate")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_returns_key(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "My CLI Key"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "key" in data
        assert data["key"].startswith("ndqs_")
        assert "key_prefix" in data

    @pytest.mark.asyncio
    async def test_list_without_auth_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/api-key/list")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_returns_masked_keys(self, client: AsyncClient, auth_headers: dict) -> None:
        # Generate a key first
        await client.post(
            "/api/auth/api-key/generate",
            json={"name": "Test Key"},
            headers=auth_headers,
        )
        response = await client.get("/api/auth/api-key/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Key should be masked (only prefix visible)
        for key_info in data:
            assert "key_prefix" in key_info
            assert "key_hash" not in key_info
            assert "key" not in key_info

    @pytest.mark.asyncio
    async def test_revoke_without_auth_returns_401(self, client: AsyncClient) -> None:
        response = await client.delete(f"/api/auth/api-key/revoke/{uuid.uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_returns_success(self, client: AsyncClient, auth_headers: dict) -> None:
        # Generate a key first
        gen_response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "To Revoke"},
            headers=auth_headers,
        )
        key_id = gen_response.json()["id"]
        # Revoke it
        response = await client.delete(
            f"/api/auth/api-key/revoke/{key_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_via_api_key(self, client: AsyncClient, auth_headers: dict) -> None:
        """Test that /api/auth/me works with API key in X-API-Key header."""
        # Generate a key
        gen_response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "Auth Test Key"},
            headers=auth_headers,
        )
        raw_key = gen_response.json()["key"]
        # Use it to authenticate
        response = await client.get(
            "/api/auth/me",
            headers={"X-API-Key": raw_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_auth_via_invalid_api_key_returns_401(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/auth/me",
            headers={"X-API-Key": "ndqs_invalid_key_here"},
        )
        assert response.status_code == 401
