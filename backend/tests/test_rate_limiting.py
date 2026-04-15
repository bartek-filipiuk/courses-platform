"""Tests for S8: Rate limiting — login attempts and API key generation."""

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


class TestLoginRateLimiting:
    @pytest.mark.asyncio
    async def test_11th_login_attempt_returns_429(self, client: AsyncClient) -> None:
        """After 10 login attempts, the 11th should be rate limited."""
        from app.rate_limit import limiter

        # Reset rate limiter state between tests
        limiter.reset()

        for _ in range(10):
            await client.get("/api/auth/github/login", follow_redirects=False)

        response = await client.get("/api/auth/github/login", follow_redirects=False)
        assert response.status_code == 429


class TestApiKeyGenerationRateLimiting:
    @pytest.mark.asyncio
    async def test_4th_api_key_generation_returns_429(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """After 3 API key generations, the 4th should be rate limited."""
        from app.rate_limit import limiter

        limiter.reset()

        for i in range(3):
            await client.post(
                "/api/auth/api-key/generate",
                json={"name": f"key-{i}"},
                headers=auth_headers,
            )

        response = await client.post(
            "/api/auth/api-key/generate",
            json={"name": "key-overflow"},
            headers=auth_headers,
        )
        assert response.status_code == 429
