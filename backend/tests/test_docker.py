"""Tests for Docker Compose configuration."""

from pathlib import Path

import pytest
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


@pytest.fixture()
def compose_path() -> Path:
    return ROOT_DIR / "docker-compose.yml"


@pytest.fixture()
def compose_config(compose_path: Path) -> dict:
    assert compose_path.exists(), "docker-compose.yml must exist in project root"
    return yaml.safe_load(compose_path.read_text())


class TestDockerCompose:
    def test_file_exists(self, compose_path: Path) -> None:
        assert compose_path.exists()

    def test_has_backend_service(self, compose_config: dict) -> None:
        assert "backend" in compose_config["services"]

    def test_has_frontend_service(self, compose_config: dict) -> None:
        assert "frontend" in compose_config["services"]

    def test_has_postgres_service(self, compose_config: dict) -> None:
        assert "postgres" in compose_config["services"]

    def test_has_redis_service(self, compose_config: dict) -> None:
        assert "redis" in compose_config["services"]

    def test_postgres_has_healthcheck(self, compose_config: dict) -> None:
        pg = compose_config["services"]["postgres"]
        assert "healthcheck" in pg
        assert "pg_isready" in pg["healthcheck"]["test"][-1]

    def test_redis_has_healthcheck(self, compose_config: dict) -> None:
        redis = compose_config["services"]["redis"]
        assert "healthcheck" in redis
        assert "redis-cli" in redis["healthcheck"]["test"][-1]

    def test_backend_depends_on_postgres_healthy(self, compose_config: dict) -> None:
        backend = compose_config["services"]["backend"]
        assert "depends_on" in backend
        pg_dep = backend["depends_on"]["postgres"]
        assert pg_dep["condition"] == "service_healthy"

    def test_backend_depends_on_redis_healthy(self, compose_config: dict) -> None:
        backend = compose_config["services"]["backend"]
        redis_dep = backend["depends_on"]["redis"]
        assert redis_dep["condition"] == "service_healthy"

    def test_backend_uses_env_file(self, compose_config: dict) -> None:
        backend = compose_config["services"]["backend"]
        env_file = backend.get("env_file")
        assert env_file is not None

    def test_frontend_depends_on_backend(self, compose_config: dict) -> None:
        frontend = compose_config["services"]["frontend"]
        assert "depends_on" in frontend
        assert "backend" in frontend["depends_on"]


class TestDockerfiles:
    def test_backend_dockerfile_exists(self) -> None:
        assert (ROOT_DIR / "backend" / "Dockerfile").exists()

    def test_frontend_dockerfile_exists(self) -> None:
        assert (ROOT_DIR / "frontend" / "Dockerfile").exists()
