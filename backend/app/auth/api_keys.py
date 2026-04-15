"""API Key generation, validation, and management.

Uses an in-memory store for MVP/testing. Will be replaced with DB queries
when PostgreSQL is running.
"""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

# In-memory store: key_hash -> {id, user_id, key_prefix, name, is_active, expires_at, created_at}
_api_key_store: dict[str, dict] = {}

KEY_PREFIX = "ndqs_"


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key(user_id: str, name: str, expires_at: datetime | None = None) -> dict:
    """Generate a new API key for a user. Returns the raw key (shown only once)."""
    raw_key = f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"
    key_hash = _hash_key(raw_key)
    key_id = str(uuid.uuid4())
    key_prefix = raw_key[:12]

    _api_key_store[key_hash] = {
        "id": key_id,
        "user_id": user_id,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "name": name,
        "is_active": True,
        "expires_at": expires_at,
        "created_at": datetime.now(UTC),
    }

    return {
        "id": key_id,
        "key": raw_key,
        "key_prefix": key_prefix,
        "name": name,
    }


def list_user_keys(user_id: str) -> list[dict]:
    """List all API keys for a user (masked — no raw key or hash)."""
    return [
        {
            "id": info["id"],
            "key_prefix": info["key_prefix"],
            "name": info["name"],
            "is_active": info["is_active"],
            "expires_at": info["expires_at"],
            "created_at": info["created_at"].isoformat() if info["created_at"] else None,
        }
        for info in _api_key_store.values()
        if info["user_id"] == user_id
    ]


def revoke_key(key_id: str, user_id: str) -> bool:
    """Revoke an API key. Returns True if found and revoked."""
    for info in _api_key_store.values():
        if info["id"] == key_id and info["user_id"] == user_id:
            info["is_active"] = False
            return True
    return False


def validate_api_key(raw_key: str) -> dict | None:
    """Validate a raw API key. Returns user info if valid, None otherwise."""
    key_hash = _hash_key(raw_key)
    info = _api_key_store.get(key_hash)

    if info is None:
        return None

    if not info["is_active"]:
        return None

    if info["expires_at"] and info["expires_at"] < datetime.now(UTC):
        return None

    return {
        "user_id": info["user_id"],
        "key_id": info["id"],
        "key_name": info["name"],
    }
