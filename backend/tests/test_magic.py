"""Tests for single-use magic-token mint + verify (sales-bridge auth)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.auth.jwt import create_magic_token
from app.auth.magic import MagicError, consume_magic_token


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
