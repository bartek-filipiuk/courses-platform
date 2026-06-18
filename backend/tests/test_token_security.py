"""Tests for S4: JWT TTLs, token rotation, API key hashing."""

import hashlib
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


def _fake_db() -> AsyncMock:
    """AsyncMock session that records `add`ed ApiKey rows and serves them back."""
    rows: list = []
    db = AsyncMock()
    db.add = MagicMock(side_effect=rows.append)
    db.commit = AsyncMock()

    async def _execute(stmt):
        wanted: set = set()
        for crit in getattr(stmt.whereclause, "clauses", [stmt.whereclause]):
            val = getattr(getattr(crit, "right", None), "value", None)
            if val is not None:
                wanted.add(val)
        matched = [
            r
            for r in rows
            if getattr(r, "key_hash", None) in wanted
            or str(getattr(r, "user_id", None)) in {str(w) for w in wanted}
        ]
        result = MagicMock()
        result.scalar_one_or_none.return_value = matched[0] if matched else None
        scalars = MagicMock()
        scalars.all.return_value = matched
        result.scalars.return_value = scalars
        return result

    db.execute = AsyncMock(side_effect=_execute)
    db._rows = rows  # noqa: SLF001
    return db


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


class TestJWTTokenTTLs:
    def test_access_token_ttl_is_15_minutes(self) -> None:
        from app.auth.jwt import ACCESS_TOKEN_EXPIRE_MINUTES

        assert ACCESS_TOKEN_EXPIRE_MINUTES == 15

    def test_refresh_token_ttl_is_7_days(self) -> None:
        from app.auth.jwt import REFRESH_TOKEN_EXPIRE_DAYS

        assert REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_access_token_has_exp_claim(self) -> None:
        from app.auth.jwt import create_access_token, decode_token

        token = create_access_token(data={"sub": "user1", "role": "student"})
        payload = decode_token(token, token_type="access")
        assert "exp" in payload

    def test_refresh_token_has_exp_claim(self) -> None:
        from app.auth.jwt import create_refresh_token, decode_token

        token = create_refresh_token(data={"sub": "user1"})
        payload = decode_token(token, token_type="refresh")
        assert "exp" in payload

    def test_access_token_has_unique_jti(self) -> None:
        from app.auth.jwt import create_access_token, decode_token

        t1 = create_access_token(data={"sub": "user1", "role": "student"})
        t2 = create_access_token(data={"sub": "user1", "role": "student"})
        p1 = decode_token(t1, token_type="access")
        p2 = decode_token(t2, token_type="access")
        assert p1["jti"] != p2["jti"]


class TestRefreshTokenRotation:
    @pytest.mark.asyncio
    async def test_refresh_returns_different_tokens(self, client: AsyncClient) -> None:
        from app.auth.jwt import create_refresh_token

        refresh = create_refresh_token(data={"sub": str(uuid.uuid4())})
        response = await client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["refresh_token"] != refresh
        assert data["access_token"] != refresh

    @pytest.mark.asyncio
    async def test_access_token_not_usable_as_refresh(self, client: AsyncClient) -> None:
        from app.auth.jwt import create_access_token

        access = create_access_token(data={"sub": str(uuid.uuid4()), "role": "student"})
        response = await client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert response.status_code == 401


class TestApiKeyHashing:
    @pytest.mark.asyncio
    async def test_api_key_stored_as_sha256_hash(self) -> None:
        from app.auth.api_keys import generate_api_key

        db = _fake_db()
        result = await generate_api_key(db, user_id=str(uuid.uuid4()), name="test")
        expected_hash = hashlib.sha256(result["key"].encode()).hexdigest()
        assert db._rows[0].key_hash == expected_hash  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_raw_key_not_stored(self) -> None:
        from app.auth.api_keys import generate_api_key

        db = _fake_db()
        result = await generate_api_key(db, user_id=str(uuid.uuid4()), name="test")
        raw_key = result["key"]
        stored = db._rows[0]  # noqa: SLF001
        for attr in ("key_hash", "key_prefix", "name"):
            assert raw_key != getattr(stored, attr)

    @pytest.mark.asyncio
    async def test_api_key_has_ndqs_prefix(self) -> None:
        from app.auth.api_keys import generate_api_key

        db = _fake_db()
        result = await generate_api_key(db, user_id=str(uuid.uuid4()), name="test")
        assert result["key"].startswith("ndqs_")

    @pytest.mark.asyncio
    async def test_list_does_not_expose_hash(self) -> None:
        """list_user_keys should not include key_hash in output."""
        from app.auth.api_keys import generate_api_key, list_user_keys

        db = _fake_db()
        user_id = str(uuid.uuid4())
        await generate_api_key(db, user_id=user_id, name="test")
        keys = await list_user_keys(db, user_id=user_id)
        assert len(keys) == 1
        for key_info in keys:
            assert "key_hash" not in key_info
