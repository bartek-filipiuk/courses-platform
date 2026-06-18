"""Single-use magic-link token consumption (sales-bridge auth)."""

from app.auth.jwt import decode_token
from app.redis import blacklist_token, is_token_blacklisted

MAGIC_USED_TTL = 15 * 60  # seconds — matches the magic token lifetime


class MagicError(Exception):
    """Raised when a magic token is invalid, expired, wrong-type, or replayed."""


async def consume_magic_token(token: str) -> dict:
    """Validate a single-use magic token.

    Returns ``{"sub", "email"}`` on success and marks the token's ``jti`` used
    in Redis so it cannot be replayed. Raises :class:`MagicError` on any
    invalid / expired / wrong-type / already-used token.
    """
    try:
        payload = decode_token(token, "magic")
    except Exception as e:  # TokenError + any decode failure
        msg = "invalid or expired magic token"
        raise MagicError(msg) from e

    if payload.get("type") != "magic":
        msg = "not a magic token"
        raise MagicError(msg)

    jti = payload.get("jti")
    if not jti or await is_token_blacklisted(jti):
        msg = "magic token already used"
        raise MagicError(msg)

    await blacklist_token(jti, MAGIC_USED_TTL)
    return {"sub": payload["sub"], "email": payload.get("email", "")}
