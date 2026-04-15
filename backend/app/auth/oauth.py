"""GitHub OAuth — exchange code for token, fetch user profile, upsert in DB."""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.config import settings

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class OAuthError(Exception):
    """Raised when OAuth flow fails."""


async def exchange_code_for_token(code: str) -> str:
    """Exchange GitHub authorization code for access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
    if resp.status_code != 200:
        raise OAuthError(f"GitHub token exchange failed: {resp.status_code}")

    data = resp.json()
    token = data.get("access_token")
    if not token:
        error = data.get("error_description", data.get("error", "Unknown error"))
        raise OAuthError(f"GitHub token exchange failed: {error}")
    return token


async def fetch_github_profile(access_token: str) -> dict:
    """Fetch GitHub user profile and primary email."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

        user_resp = await client.get(GITHUB_USER_URL, headers=headers, timeout=10)
        if user_resp.status_code != 200:
            raise OAuthError(f"GitHub user fetch failed: {user_resp.status_code}")
        user_data = user_resp.json()

        email = user_data.get("email")
        if not email:
            emails_resp = await client.get(GITHUB_EMAILS_URL, headers=headers, timeout=10)
            if emails_resp.status_code == 200:
                for e in emails_resp.json():
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break

        if not email:
            raise OAuthError("No verified email found on GitHub account")

    return {
        "provider_id": str(user_data["id"]),
        "email": email,
        "display_name": user_data.get("name") or user_data.get("login", ""),
        "avatar_url": user_data.get("avatar_url"),
    }


async def upsert_user(db: AsyncSession, profile: dict) -> User:
    """Create or update user from OAuth profile."""
    stmt = select(User).where(
        User.provider == "github",
        User.provider_id == profile["provider_id"],
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        # Check if email already exists (different provider)
        email_stmt = select(User).where(User.email == profile["email"])
        email_result = await db.execute(email_stmt)
        existing = email_result.scalar_one_or_none()
        if existing:
            # Update existing user with GitHub provider
            existing.provider = "github"
            existing.provider_id = profile["provider_id"]
            existing.avatar_url = profile.get("avatar_url")
            await db.commit()
            await db.refresh(existing)
            return existing

        user = User(
            email=profile["email"],
            display_name=profile["display_name"],
            avatar_url=profile.get("avatar_url"),
            provider="github",
            provider_id=profile["provider_id"],
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.email = profile["email"]
        user.display_name = profile["display_name"]
        user.avatar_url = profile.get("avatar_url")
        await db.commit()
        await db.refresh(user)

    return user
