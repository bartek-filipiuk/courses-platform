"""Auth dependencies — extract and validate current user from JWT or API Key."""

from fastapi import HTTPException, Request

from app.auth.jwt import TokenError, decode_token


async def get_current_user_token(request: Request) -> dict:
    """Extract and validate JWT access token from Authorization header.

    Returns the decoded token payload dict with at minimum 'sub' (user_id).
    Raises 401 if token is missing, invalid, or expired.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token, token_type="access")
    except TokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload
