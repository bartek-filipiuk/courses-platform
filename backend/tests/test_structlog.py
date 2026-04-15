"""Tests for structlog setup — JSON logging, correlation ID middleware."""

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


class TestStructlogSetup:
    def test_logging_module_exists(self) -> None:
        from app.logging import setup_logging

        assert setup_logging is not None

    def test_get_logger_returns_bound_logger(self) -> None:
        import structlog

        from app.logging import setup_logging

        setup_logging()
        logger = structlog.get_logger()
        assert logger is not None


class TestCorrelationId:
    @pytest.mark.asyncio
    async def test_response_has_correlation_id_header(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert "x-correlation-id" in response.headers

    @pytest.mark.asyncio
    async def test_correlation_id_is_valid_uuid(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        correlation_id = response.headers.get("x-correlation-id")
        assert correlation_id is not None
        # Should be a valid UUID
        uuid.UUID(correlation_id)

    @pytest.mark.asyncio
    async def test_forwarded_correlation_id_is_preserved(self, client: AsyncClient) -> None:
        custom_id = str(uuid.uuid4())
        response = await client.get(
            "/api/health",
            headers={"X-Correlation-ID": custom_id},
        )
        assert response.headers.get("x-correlation-id") == custom_id
