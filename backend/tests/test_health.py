"""Tests for backend scaffolding — health endpoint, CORS, exception handling."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app


@pytest.fixture()
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as ac:
        yield ac


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_returns_status_ok(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_returns_service_name(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        data = response.json()
        assert data["service"] == "ndqs-backend"


class TestCORS:
    @pytest.mark.asyncio
    async def test_cors_allows_configured_origin(self, client: AsyncClient) -> None:
        response = await client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_cors_rejects_unknown_origin(self, client: AsyncClient) -> None:
        response = await client.options(
            "/api/health",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") != "http://evil.com"


class TestExceptionHandling:
    @pytest.mark.asyncio
    async def test_production_500_hides_details(self, client: AsyncClient) -> None:
        """In production, 500 errors should return generic message."""
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            response = await client.get("/api/health/error-test")
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Internal server error"
            assert "traceback" not in data
        finally:
            settings.ENVIRONMENT = original

    @pytest.mark.asyncio
    async def test_development_500_shows_details(self, client: AsyncClient) -> None:
        """In development, 500 errors should include stack trace."""
        original = settings.ENVIRONMENT
        settings.ENVIRONMENT = "development"
        try:
            response = await client.get("/api/health/error-test")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "traceback" in data
        finally:
            settings.ENVIRONMENT = original


class TestDirectoryStructure:
    def test_app_package_exists(self) -> None:
        from pathlib import Path

        app_dir = Path(__file__).resolve().parent.parent / "app"
        assert app_dir.is_dir()

    def test_domain_packages_exist(self) -> None:
        from pathlib import Path

        app_dir = Path(__file__).resolve().parent.parent / "app"
        for domain in ["auth", "courses", "quests", "evaluation"]:
            assert (app_dir / domain).is_dir(), f"Missing domain package: {domain}"
            assert (app_dir / domain / "__init__.py").exists(), f"Missing __init__.py in {domain}"
