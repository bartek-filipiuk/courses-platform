"""Auth routes — OAuth login, refresh, logout, me."""

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.auth.dependencies import get_current_user_token
from app.auth.jwt import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/github/login")
async def github_login() -> RedirectResponse:
    params = urlencode({
        "client_id": settings.GITHUB_CLIENT_ID,
        "scope": "read:user user:email",
    })
    return RedirectResponse(
        url=f"https://github.com/login/oauth/authorize?{params}",
        status_code=302,
    )


@router.get("/github/callback")
async def github_callback(code: str) -> dict:
    # TODO: Exchange code for token, fetch user info, upsert user
    # For now return placeholder — will be completed with DB integration
    return {"message": "OAuth callback received", "code": code}


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

    # Issue new token pair (rotation: old refresh is implicitly invalidated)
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
