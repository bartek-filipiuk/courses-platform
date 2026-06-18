"""API Key generation, validation, and management — backed by Postgres.

Keys are stored as SHA-256 hashes in the `api_keys` table (see
`app.auth.models.ApiKey`). The raw key is shown to the user exactly once at
generation time and is never persisted.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import ApiKey

KEY_PREFIX = "ndqs_"


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def generate_api_key(
    db: AsyncSession,
    user_id: str,
    name: str,
    expires_at: datetime | None = None,
) -> dict:
    """Generate and persist a new API key for a user.

    Returns the raw key (shown only once) plus its public metadata.
    """
    raw_key = f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)
    key_id = uuid.uuid4()
    key_prefix = raw_key[:12]

    api_key = ApiKey(
        id=key_id,
        user_id=uuid.UUID(str(user_id)),
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()

    return {
        "id": str(key_id),
        "key": raw_key,
        "key_prefix": key_prefix,
        "name": name,
    }


async def list_user_keys(db: AsyncSession, user_id: str) -> list[dict]:
    """List all API keys for a user (masked — no raw key or hash)."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == uuid.UUID(str(user_id)))
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        {
            "id": str(key.id),
            "key_prefix": key.key_prefix,
            "name": key.name,
            "is_active": key.is_active,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "created_at": key.created_at.isoformat() if key.created_at else None,
        }
        for key in keys
    ]


async def revoke_key(db: AsyncSession, key_id: str, user_id: str) -> bool:
    """Revoke (deactivate) an API key. Returns True if found and revoked."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == uuid.UUID(str(key_id)),
            ApiKey.user_id == uuid.UUID(str(user_id)),
        )
    )
    key = result.scalar_one_or_none()
    if key is None:
        return False

    key.is_active = False
    await db.commit()
    return True


async def validate_api_key(db: AsyncSession, raw_key: str) -> dict | None:
    """Validate a raw API key. Returns user info if valid, None otherwise."""
    key_hash = _hash_key(raw_key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    key = result.scalar_one_or_none()

    if key is None:
        return None

    if not key.is_active:
        return None

    if key.expires_at and key.expires_at < datetime.now(UTC):
        return None

    return {
        "user_id": str(key.user_id),
        "key_id": str(key.id),
        "key_name": key.name,
    }
