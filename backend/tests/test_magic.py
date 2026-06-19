"""Tests for single-use magic-token mint + verify (sales-bridge auth)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_magic_token
from app.auth.magic import MagicError, consume_magic_token
from app.database import get_db
from app.main import app


def _override_db(db):
    async def _f():
        yield db

    return _f


@pytest.mark.asyncio
async def test_consume_valid_token_returns_identity() -> None:
    tok = create_magic_token("user-1", "a@b.pl")
    with (
        patch("app.auth.magic.is_token_blacklisted", AsyncMock(return_value=False)),
        patch("app.auth.magic.blacklist_token", AsyncMock()) as bl,
    ):
        out = await consume_magic_token(tok)
    assert out == {"sub": "user-1", "email": "a@b.pl"}
    bl.assert_awaited_once()


@pytest.mark.asyncio
async def test_replayed_token_rejected() -> None:
    tok = create_magic_token("user-1", "a@b.pl")
    with (
        patch("app.auth.magic.is_token_blacklisted", AsyncMock(return_value=True)),
        pytest.raises(MagicError),
    ):
        await consume_magic_token(tok)


@pytest.mark.asyncio
async def test_garbage_token_rejected() -> None:
    with pytest.raises(MagicError):
        await consume_magic_token("not-a-jwt")


@pytest.mark.asyncio
async def test_magic_token_signed_with_magic_secret_roundtrips() -> None:
    """A magic token minted by create_magic_token verifies + consumes cleanly."""
    tok = create_magic_token("user-7", "round@trip.pl")
    with (
        patch("app.auth.magic.is_token_blacklisted", AsyncMock(return_value=False)),
        patch("app.auth.magic.blacklist_token", AsyncMock()),
    ):
        out = await consume_magic_token(tok)
    assert out == {"sub": "user-7", "email": "round@trip.pl"}


def test_magic_token_uses_dedicated_secret_not_refresh() -> None:
    """The magic token must be signed with MAGIC_SECRET, not the refresh secret.

    A token forged with the OLD scheme (signed with JWT_REFRESH_SECRET) must NOT
    decode as a magic token once they are decoupled.
    """
    import jwt as pyjwt

    from app.auth.jwt import TokenError, decode_token
    from app.config import settings

    # Token minted the OLD way: type=magic but signed with the REFRESH secret.
    legacy = pyjwt.encode(
        {"sub": "u", "email": "e@x.pl", "type": "magic", "jti": "j1"},
        settings.JWT_REFRESH_SECRET,
        algorithm="HS256",
    )
    with pytest.raises(TokenError):
        decode_token(legacy, "magic")

    # And the new token (signed with MAGIC_SECRET) decodes fine as magic.
    fresh = create_magic_token("u", "e@x.pl")
    assert decode_token(fresh, "magic")["type"] == "magic"


def test_access_and_refresh_paths_unchanged() -> None:
    """Decoupling magic must not touch the access/refresh secret selection."""
    from app.auth.jwt import (
        TokenError,
        create_access_token,
        create_refresh_token,
        decode_token,
    )

    acc = create_access_token({"sub": "u", "email": "e@x.pl"})
    ref = create_refresh_token({"sub": "u", "email": "e@x.pl"})
    assert decode_token(acc, "access")["type"] == "access"
    assert decode_token(ref, "refresh")["type"] == "refresh"
    # Cross-secret: an access token must not validate under the refresh secret.
    with pytest.raises(TokenError):
        decode_token(acc, "refresh")
    with pytest.raises(TokenError):
        decode_token(ref, "access")


@pytest.mark.asyncio
async def test_access_token_rejected_as_magic() -> None:
    """A non-magic token (wrong type claim) must not be consumable as magic."""
    from app.auth.jwt import create_access_token

    tok = create_access_token({"sub": "user-1", "email": "a@b.pl"})
    with (
        patch("app.auth.magic.is_token_blacklisted", AsyncMock(return_value=False)),
        patch("app.auth.magic.blacklist_token", AsyncMock()),
        pytest.raises(MagicError),
    ):
        await consume_magic_token(tok)


# --- Endpoint tests: magic-link request + verify router ---


@pytest.mark.asyncio
async def test_request_unknown_email_still_200_no_send():
    db = AsyncMock()
    res = MagicMock()
    res.scalar_one_or_none.return_value = None
    db.execute.return_value = res
    app.dependency_overrides[get_db] = _override_db(db)
    with patch("app.auth.magic_router.send_magic_link_email", AsyncMock()) as send:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post("/api/auth/magic/request", json={"email": "ghost@x.pl"})
        assert r.status_code == 200 and r.json() == {"sent": True}
        send.assert_not_awaited()
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_request_known_email_sends_link():
    db = AsyncMock()
    user = MagicMock()
    user.id = uuid4()
    user.email = "buyer@x.pl"
    res = MagicMock()
    res.scalar_one_or_none.return_value = user
    db.execute.return_value = res
    app.dependency_overrides[get_db] = _override_db(db)
    with patch("app.auth.magic_router.send_magic_link_email", AsyncMock()) as send:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post("/api/auth/magic/request", json={"email": "buyer@x.pl"})
        assert r.status_code == 200
        send.assert_awaited_once()
        assert "/auth/magic?token=" in send.await_args.args[1]
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_request_known_email_send_failure_still_200():
    """A Brevo send failure must NOT 500 — that would leak email existence
    (known email → send attempted → 500; unknown email → no send → 200)."""
    db = AsyncMock()
    user = MagicMock()
    user.id = uuid4()
    user.email = "buyer@x.pl"
    res = MagicMock()
    res.scalar_one_or_none.return_value = user
    db.execute.return_value = res
    app.dependency_overrides[get_db] = _override_db(db)
    with patch(
        "app.auth.magic_router.send_magic_link_email",
        AsyncMock(side_effect=RuntimeError("brevo 500")),
    ) as send:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            r = await c.post("/api/auth/magic/request", json={"email": "buyer@x.pl"})
        assert r.status_code == 200 and r.json() == {"sent": True}
        send.assert_awaited_once()
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_verify_bad_token_400():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/auth/magic/verify", params={"token": "garbage"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_magic_verify_returns_refresh_token(monkeypatch):
    """magic/verify must return a non-empty refresh_token alongside the access_token (B4)."""
    from app.rate_limit import limiter

    limiter.reset()
    ident = {"sub": str(uuid4()), "email": "a@b.c"}
    monkeypatch.setattr("app.auth.magic_router.consume_magic_token", AsyncMock(return_value=ident))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/auth/magic/verify?token=ok")
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["access_token"]
    assert "refresh_token" in body
    assert body["refresh_token"]
