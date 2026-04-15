"""Tests for S9: Error message hardening — production hides details, dev shows them."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings


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

    token = create_access_token(
        data={"sub": str(uuid.uuid4()), "role": "student", "email": "test@example.com"}
    )
    return {"Authorization": f"Bearer {token}"}


class TestProductionErrorHardening:
    """In production, errors must never leak internal details."""

    @pytest.mark.asyncio
    async def test_500_returns_generic_message(self, client: AsyncClient) -> None:
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            response = await client.get("/api/health/error-test")
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Internal server error"
            assert "traceback" not in data
            assert "RuntimeError" not in response.text
        finally:
            settings.ENVIRONMENT = original

    @pytest.mark.asyncio
    async def test_500_includes_correlation_id(self, client: AsyncClient) -> None:
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            response = await client.get("/api/health/error-test")
            assert "x-correlation-id" in response.headers
        finally:
            settings.ENVIRONMENT = original

    @pytest.mark.asyncio
    async def test_validation_error_hides_internal_field_paths(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """In production, validation errors should not reveal Pydantic model internals."""
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            response = await client.post(
                "/api/auth/api-key/generate",
                json={"name": 12345},  # wrong type
                headers=auth_headers,
            )
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            body_text = response.text.lower()
            # Should not reveal internal model class names or DB schemas
            assert "sqlalchemy" not in body_text
            assert "postgresql" not in body_text
            assert "basemodel" not in body_text
        finally:
            settings.ENVIRONMENT = original

    @pytest.mark.asyncio
    async def test_validation_error_production_has_clean_structure(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """Production validation errors should return a clean, user-friendly structure."""
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            response = await client.post(
                "/api/auth/api-key/generate",
                json={},
                headers=auth_headers,
            )
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            # Each error should have field + message, not raw Pydantic ctx/url
            if isinstance(data["detail"], list):
                for error in data["detail"]:
                    assert "field" in error
                    assert "message" in error
                    # Should NOT contain raw Pydantic internals
                    assert "ctx" not in error
                    assert "url" not in error
                    assert "input" not in error
        finally:
            settings.ENVIRONMENT = original


class TestDevelopmentErrorDetails:
    """In development, errors should include useful debugging info."""

    @pytest.mark.asyncio
    async def test_500_shows_traceback(self, client: AsyncClient) -> None:
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "development"
        try:
            response = await client.get("/api/health/error-test")
            assert response.status_code == 500
            data = response.json()
            assert "traceback" in data
            assert "detail" in data
        finally:
            settings.ENVIRONMENT = original

    @pytest.mark.asyncio
    async def test_validation_error_shows_full_details(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        """In development, validation errors should include full Pydantic details for debugging."""
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "development"
        try:
            response = await client.post(
                "/api/auth/api-key/generate",
                json={},
                headers=auth_headers,
            )
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            # In dev, we get the raw Pydantic validation error details
            assert isinstance(data["detail"], list)
        finally:
            settings.ENVIRONMENT = original
