"""Tests for auth backend — JWT, OAuth callback, refresh rotation, logout."""

import uuid
from datetime import timedelta

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


class TestJWTUtils:
    def test_create_access_token(self) -> None:
        from app.auth.jwt import create_access_token

        token = create_access_token(data={"sub": str(uuid.uuid4()), "role": "student"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self) -> None:
        from app.auth.jwt import create_refresh_token

        token = create_refresh_token(data={"sub": str(uuid.uuid4())})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self) -> None:
        from app.auth.jwt import create_access_token, decode_token

        user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": user_id, "role": "student"})
        payload = decode_token(token, token_type="access")
        assert payload["sub"] == user_id
        assert payload["role"] == "student"

    def test_decode_refresh_token(self) -> None:
        from app.auth.jwt import create_refresh_token, decode_token

        user_id = str(uuid.uuid4())
        token = create_refresh_token(data={"sub": user_id})
        payload = decode_token(token, token_type="refresh")
        assert payload["sub"] == user_id

    def test_access_token_has_expiry(self) -> None:
        from app.auth.jwt import create_access_token, decode_token

        token = create_access_token(data={"sub": str(uuid.uuid4()), "role": "student"})
        payload = decode_token(token, token_type="access")
        assert "exp" in payload

    def test_expired_token_raises(self) -> None:
        from app.auth.jwt import TokenError, create_access_token, decode_token

        token = create_access_token(
            data={"sub": str(uuid.uuid4()), "role": "student"},
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(TokenError):
            decode_token(token, token_type="access")

    def test_invalid_token_raises(self) -> None:
        from app.auth.jwt import TokenError, decode_token

        with pytest.raises(TokenError):
            decode_token("invalid.token.here", token_type="access")


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_github_login_redirects(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/github/login", follow_redirects=False)
        assert response.status_code in (302, 307)
        location = response.headers.get("location", "")
        assert "github.com" in location

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_valid_token_returns_user(self, client: AsyncClient) -> None:
        from app.auth.jwt import create_access_token

        user_id = str(uuid.uuid4())
        token = create_access_token(
            data={"sub": user_id, "role": "student", "email": "test@example.com"}
        )
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_refresh_without_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/refresh")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_without_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.post("/api/auth/logout")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_valid_token_returns_new_tokens(self, client: AsyncClient) -> None:
        from app.auth.jwt import create_refresh_token

        user_id = str(uuid.uuid4())
        refresh = create_refresh_token(data={"sub": user_id})
        response = await client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different
        assert data["refresh_token"] != refresh

    @pytest.mark.asyncio
    async def test_logout_with_valid_token_returns_ok(self, client: AsyncClient) -> None:
        from app.auth.jwt import create_access_token

        user_id = str(uuid.uuid4())
        token = create_access_token(
            data={"sub": user_id, "role": "student", "email": "test@example.com"}
        )
        response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
