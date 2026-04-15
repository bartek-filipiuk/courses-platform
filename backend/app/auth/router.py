"""Auth routes — OAuth login, refresh, logout, me, API keys."""

from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, field_validator

from app.auth.api_keys import generate_api_key, list_user_keys, revoke_key
from app.auth.dependencies import get_current_user_token
from app.auth.jwt import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings
from app.rate_limit import API_KEY_GENERATE_RATE_LIMIT, LOGIN_RATE_LIMIT, _get_user_id_or_ip, limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])


class GenerateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            msg = "Name must not be blank"
            raise ValueError(msg)
        return v.strip()


# --- OAuth ---


@router.get("/github/login")
@limiter.limit(LOGIN_RATE_LIMIT)
async def github_login(request: Request) -> RedirectResponse:
    params = urlencode({
        "client_id": settings.GITHUB_CLIENT_ID,
        "scope": "read:user user:email",
    })
    return RedirectResponse(
        url=f"https://github.com/login/oauth/authorize?{params}",
        status_code=302,
    )


@router.get("/github/callback")
async def github_callback(code: str = Query(..., min_length=1)) -> dict:
    # TODO: Exchange code for token, fetch user info, upsert user
    return {"message": "OAuth callback received", "code": code}


# --- JWT Auth ---


@router.get("/me")
async def me(token_data: dict = Depends(get_current_user_token)) -> dict:
    return {
        "user_id": token_data["sub"],
        "role": token_data.get("role"),
        "email": token_data.get("email"),
    }


@router.post("/refresh")
async def refresh_token(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing refresh token")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = decode_token(token, token_type="refresh")
    except TokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload["sub"]
    new_access = create_access_token(
        data={"sub": user_id, "role": payload.get("role", "student"), "email": payload.get("email")}
    )
    new_refresh = create_refresh_token(data={"sub": user_id})

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(token_data: dict = Depends(get_current_user_token)) -> dict:
    # TODO: Add token to Redis blacklist with TTL = remaining JWT lifetime
    return {"message": "Logged out successfully"}


# --- API Keys ---


@router.post("/api-key/generate", status_code=201)
@limiter.limit(API_KEY_GENERATE_RATE_LIMIT, key_func=_get_user_id_or_ip)
async def api_key_generate(
    request: Request,
    body: GenerateApiKeyRequest,
    token_data: dict = Depends(get_current_user_token),
) -> dict:
    result = generate_api_key(user_id=token_data["sub"], name=body.name)
    return result


@router.get("/api-key/list")
async def api_key_list(token_data: dict = Depends(get_current_user_token)) -> list[dict]:
    return list_user_keys(user_id=token_data["sub"])


@router.delete("/api-key/revoke/{key_id}")
async def api_key_revoke(
    key_id: UUID,
    token_data: dict = Depends(get_current_user_token),
) -> dict:
    success = revoke_key(key_id=str(key_id), user_id=token_data["sub"])
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked"}
