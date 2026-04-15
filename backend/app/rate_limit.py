"""Rate limiting configuration using slowapi.

Provides per-endpoint rate limits:
- Auth login endpoints: 10 requests per IP per 5 minutes
- API key generation: 3 requests per user per hour
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


def _get_user_id_or_ip(request: Request) -> str:
    """Extract user_id from JWT for authenticated rate limiting, fallback to IP."""
    from app.auth.jwt import TokenError, decode_token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token, token_type="access")
            return payload.get("sub", get_remote_address(request))
        except TokenError:
            pass
    return get_remote_address(request)


_storage_uri = settings.REDIS_URL if settings.ENVIRONMENT == "production" else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage_uri,
    strategy="fixed-window",
)

# Rate limit strings
LOGIN_RATE_LIMIT = "10/5minutes"
API_KEY_GENERATE_RATE_LIMIT = "3/hour"
