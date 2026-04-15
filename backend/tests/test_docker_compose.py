"""Tests for Docker Compose configuration."""

from pathlib import Path

import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
COMPOSE_FILE = ROOT_DIR / "docker-compose.yml"


@pytest.fixture
def compose_config() -> dict:
    assert COMPOSE_FILE.exists(), "docker-compose.yml must exist in project root"
    return yaml.safe_load(COMPOSE_FILE.read_text())


def test_compose_file_exists() -> None:
    assert COMPOSE_FILE.exists(), "docker-compose.yml must exist in project root"


def test_required_services_present(compose_config: dict) -> None:
    services = compose_config.get("services", {})
    for svc in ["backend", "frontend", "postgres", "redis"]:
        assert svc in services, f"Service '{svc}' must be defined"


def test_postgres_healthcheck(compose_config: dict) -> None:
    pg = compose_config["services"]["postgres"]
    hc = pg.get("healthcheck", {})
    test_cmd = hc.get("test", "")
    # Should use pg_isready
    if isinstance(test_cmd, list):
        test_cmd = " ".join(test_cmd)
    assert "pg_isready" in test_cmd, "Postgres healthcheck must use pg_isready"


def test_redis_healthcheck(compose_config: dict) -> None:
    redis = compose_config["services"]["redis"]
    hc = redis.get("healthcheck", {})
    test_cmd = hc.get("test", "")
    if isinstance(test_cmd, list):
        test_cmd = " ".join(test_cmd)
    assert "redis-cli" in test_cmd or "ping" in test_cmd, (
        "Redis healthcheck must use redis-cli ping"
    )


def test_backend_depends_on_postgres(compose_config: dict) -> None:
    backend = compose_config["services"]["backend"]
    depends = backend.get("depends_on", {})
    assert "postgres" in depends, "Backend must depend on postgres"
    if isinstance(depends, dict):
        pg_dep = depends["postgres"]
        assert pg_dep.get("condition") == "service_healthy", (
            "Backend should wait for postgres to be healthy"
        )


def test_backend_depends_on_redis(compose_config: dict) -> None:
    backend = compose_config["services"]["backend"]
    depends = backend.get("depends_on", {})
    assert "redis" in depends, "Backend must depend on redis"


def test_backend_dockerfile_exists() -> None:
    dockerfile = ROOT_DIR / "backend" / "Dockerfile"
    assert dockerfile.exists(), "backend/Dockerfile must exist"


def test_frontend_dockerfile_exists() -> None:
    dockerfile = ROOT_DIR / "frontend" / "Dockerfile"
    assert dockerfile.exists(), "frontend/Dockerfile must exist"
