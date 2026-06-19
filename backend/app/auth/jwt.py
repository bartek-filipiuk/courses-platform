"""JWT token creation and verification utilities."""

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAGIC_TOKEN_EXPIRE_MINUTES = 15


class TokenError(Exception):
    """Raised when a token is invalid or expired."""


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def create_refresh_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta is not None else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm="HS256")


def create_magic_token(user_id: str, email: str) -> str:
    """Mint a single-use magic-link token (type="magic", 15-min expiry, jti).

    Signed with the dedicated ``MAGIC_SECRET`` (NOT the refresh secret) so a
    refresh-secret leak cannot forge passwordless-login tokens. ``decode_token``
    selects the verification secret by token "type", so it verifies magic tokens
    with the same ``MAGIC_SECRET``.
    """
    expire = datetime.now(UTC) + timedelta(minutes=MAGIC_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "email": email,
        "type": "magic",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(to_encode, settings.MAGIC_SECRET, algorithm="HS256")


# Per-token-type signing/verification secret. Each token class gets its own
# secret so a leak of one cannot forge the others (access vs refresh vs magic).
_SECRET_BY_TYPE = {
    "access": "JWT_SECRET_KEY",
    "refresh": "JWT_REFRESH_SECRET",
    "magic": "MAGIC_SECRET",
}


def decode_token(token: str, token_type: str = "access") -> dict:
    secret_attr = _SECRET_BY_TYPE.get(token_type)
    if secret_attr is None:
        raise TokenError(f"Unknown token type: {token_type}")
    secret = getattr(settings, secret_attr)
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise TokenError(str(e)) from e

    if payload.get("type") != token_type:
        msg = f"Expected {token_type} token, got {payload.get('type')}"
        raise TokenError(msg)

    return payload
