"""Tests for S7: CSP + security headers on backend API responses."""

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


class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_x_frame_options_deny(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_x_content_type_options_nosniff(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    @pytest.mark.asyncio
    async def test_referrer_policy(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.headers.get("referrer-policy") == "strict-origin"

    @pytest.mark.asyncio
    async def test_content_security_policy(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        csp = response.headers.get("content-security-policy")
        assert csp is not None
        assert "default-src" in csp

    @pytest.mark.asyncio
    async def test_x_permitted_cross_domain_policies(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.headers.get("x-permitted-cross-domain-policies") == "none"
