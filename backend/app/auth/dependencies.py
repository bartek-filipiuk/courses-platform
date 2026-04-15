"""Auth dependencies — extract and validate current user from JWT or API Key."""

from fastapi import HTTPException, Request

from app.auth.api_keys import validate_api_key
from app.auth.jwt import TokenError, decode_token
from app.redis import is_token_blacklisted


async def get_current_user_token(request: Request) -> dict:
    """Extract and validate auth from JWT (Authorization header) or API Key (X-API-Key header).

    Returns a dict with at minimum 'sub' (user_id).
    Raises 401 if neither is present or valid.
    """
    # Try API Key first
    api_key = request.headers.get("X-API-Key")
    if api_key:
        key_info = validate_api_key(api_key)
        if key_info is None:
            raise HTTPException(status_code=401, detail="Invalid or expired API key")
        return {
            "sub": key_info["user_id"],
            "auth_method": "api_key",
            "key_name": key_info["key_name"],
        }

    # Try JWT
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token, token_type="access")
    except TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

    # Check token blacklist (logout)
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    payload["auth_method"] = "jwt"
    return payload
