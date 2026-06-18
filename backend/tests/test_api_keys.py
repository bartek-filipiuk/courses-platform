"""Tests for API Key system — model, generate, revoke, list, auth via API Key."""

import inspect
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

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

    user_id = str(uuid.uuid4())
    token = create_access_token(
        data={"sub": user_id, "role": "student", "email": "test@example.com"}
    )
    return {"Authorization": f"Bearer {token}"}


def _fake_db_for_store() -> AsyncMock:
    """An AsyncMock session that captures `add`ed ApiKey rows and serves them back.

    Resolves `db.execute(select(ApiKey).where(...))` against the in-test row list,
    matching the literal value(s) in the WHERE clause against each row's
    `key_hash` (validate), `id` (revoke), or `user_id` (list).
    """
    rows: list = []
    db = AsyncMock()
    db.add = MagicMock(side_effect=rows.append)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    async def _execute(stmt):
        wanted: set = set()
        for crit in getattr(stmt.whereclause, "clauses", [stmt.whereclause]):
            val = getattr(getattr(crit, "right", None), "value", None)
            if val is not None:
                wanted.add(str(val))

        def _hit(row: object) -> bool:
            return any(
                str(getattr(row, attr, None)) in wanted
                for attr in ("key_hash", "id", "user_id")
            )

        matched = [r for r in rows if _hit(r)]
        result = MagicMock()
        result.scalar_one_or_none.return_value = matched[0] if matched else None
        scalars = MagicMock()
        scalars.all.return_value = matched
        result.scalars.return_value = scalars
        return result

    db.execute = AsyncMock(side_effect=_execute)
    db._rows = rows  # noqa: SLF001  (test introspection)
    return db


@pytest.fixture
def mock_db():
    """Override the get_db dependency with an in-memory fake session for the app."""
    from app.database import get_db
    from app.main import app

    db = _fake_db_for_store()

    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    yield db
    app.dependency_overrides.pop(get_db, None)


class TestApiKeyModel:
    def test_api_key_model_exists(self) -> None:
        from app.auth.models import ApiKey

        assert ApiKey is not None

    def test_api_key_has_required_columns(self) -> None:
        from app.auth.models import ApiKey

        column_names = {c.name for c in ApiKey.__table__.columns}
        required = {
            "id",
            "user_id",
            "key_hash",
            "key_prefix",
            "name",
            "expires_at",
            "created_at",
            "is_active",
        }
        assert required.issubset(column_names), f"Missing columns: {required - column_names}"

    def test_api_key_table_name(self) -> None:
        from app.auth.models import ApiKey

        assert ApiKey.__tablename__ == "api_keys"


class TestApiKeyEndpoints:
    @pytest.mark.asyncio
    async def test_generate_without_auth_returns_401(
        self, client: AsyncClient, mock_db: AsyncMock
    ) -> None:
        response = await client.post("/api/auth/api-key/generate")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_returns_key(
        self, client: AsyncClient, auth_headers: dict, mock_db: AsyncMock
    ) -> None:
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
    async def test_list_without_auth_returns_401(
        self, client: AsyncClient, mock_db: AsyncMock
    ) -> None:
        response = await client.get("/api/auth/api-key/list")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_returns_masked_keys(
        self, client: AsyncClient, auth_headers: dict, mock_db: AsyncMock
    ) -> None:
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
    async def test_revoke_without_auth_returns_401(
        self, client: AsyncClient, mock_db: AsyncMock
    ) -> None:
        response = await client.delete(f"/api/auth/api-key/revoke/{uuid.uuid4()}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoke_returns_success(
        self, client: AsyncClient, auth_headers: dict, mock_db: AsyncMock
    ) -> None:
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
    async def test_auth_via_api_key(
        self, client: AsyncClient, auth_headers: dict, mock_db: AsyncMock
    ) -> None:
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
    async def test_auth_via_invalid_api_key_returns_401(
        self, client: AsyncClient, mock_db: AsyncMock
    ) -> None:
        response = await client.get(
            "/api/auth/me",
            headers={"X-API-Key": "ndqs_invalid_key_here"},
        )
        assert response.status_code == 401


class TestApiKeyDbStore:
    """DB-backed, async API-key store (no in-memory dict)."""

    def test_generate_and_validate_are_async(self) -> None:
        from app.auth.api_keys import generate_api_key, validate_api_key

        assert inspect.iscoroutinefunction(generate_api_key)
        assert inspect.iscoroutinefunction(validate_api_key)

    def test_no_in_memory_store(self) -> None:
        import app.auth.api_keys as mod

        assert not hasattr(mod, "_api_key_store"), "in-memory store must be gone"

    @pytest.mark.asyncio
    async def test_generated_key_validates(self) -> None:
        from app.auth.api_keys import generate_api_key, validate_api_key

        db = _fake_db_for_store()
        user_id = str(uuid.uuid4())

        result = await generate_api_key(db, user_id=user_id, name="cli")
        assert result["key"].startswith("ndqs_")
        assert len(result["key_prefix"]) == 12
        assert db.add.called
        assert db.commit.called

        info = await validate_api_key(db, result["key"])
        assert info is not None
        assert info["user_id"] == user_id
        assert info["key_id"] == result["id"]
        assert info["key_name"] == "cli"

    @pytest.mark.asyncio
    async def test_key_stored_as_sha256_hash(self) -> None:
        import hashlib

        from app.auth.api_keys import generate_api_key

        db = _fake_db_for_store()
        result = await generate_api_key(db, user_id=str(uuid.uuid4()), name="cli")
        stored = db._rows[0]  # noqa: SLF001
        assert stored.key_hash == hashlib.sha256(result["key"].encode()).hexdigest()
        assert result["key"] not in str({c: getattr(stored, c, None) for c in ("key_hash", "key_prefix", "name")})

    @pytest.mark.asyncio
    async def test_revoked_key_does_not_validate(self) -> None:
        from app.auth.api_keys import generate_api_key, validate_api_key

        db = _fake_db_for_store()
        user_id = str(uuid.uuid4())
        result = await generate_api_key(db, user_id=user_id, name="cli")

        # Revoke flips is_active on the stored row.
        stored = db._rows[0]  # noqa: SLF001
        stored.is_active = False

        assert await validate_api_key(db, result["key"]) is None

    @pytest.mark.asyncio
    async def test_expired_key_does_not_validate(self) -> None:
        from app.auth.api_keys import generate_api_key, validate_api_key

        db = _fake_db_for_store()
        result = await generate_api_key(
            db,
            user_id=str(uuid.uuid4()),
            name="cli",
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert await validate_api_key(db, result["key"]) is None

    @pytest.mark.asyncio
    async def test_unknown_key_returns_none(self) -> None:
        from app.auth.api_keys import validate_api_key

        db = _fake_db_for_store()
        assert await validate_api_key(db, "ndqs_nope") is None
