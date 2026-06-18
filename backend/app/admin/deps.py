import hmac
from fastapi import Header, HTTPException
from app.config import settings


def require_service_token(x_service_token: str | None = Header(default=None)) -> None:
    """Gate service-to-service endpoints. Constant-time compare against env."""
    expected = settings.NDQS_SERVICE_TOKEN
    if not expected or not x_service_token or not hmac.compare_digest(x_service_token, expected):
        raise HTTPException(status_code=401, detail="Invalid service token")
