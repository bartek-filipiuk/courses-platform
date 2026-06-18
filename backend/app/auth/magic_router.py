"""Magic-link auth router (sales-bridge).

POST /api/auth/magic/request — always 200 {"sent": True}, never leaks whether
the email exists. Rate-limited to throttle email-spam abuse.
GET  /api/auth/magic/verify  — exchange a single-use magic token for an access
JWT; 400 on any invalid/expired/replayed token.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token, create_magic_token
from app.auth.magic import MagicError, consume_magic_token
from app.auth.models import User
from app.config import settings
from app.database import get_db
from app.email import send_magic_link_email
from app.rate_limit import LOGIN_RATE_LIMIT, _get_user_id_or_ip, limiter

router = APIRouter(prefix="/api/auth/magic", tags=["auth-magic"])


class MagicRequest(BaseModel):
    email: EmailStr


@router.post("/request")
@limiter.limit(LOGIN_RATE_LIMIT, key_func=_get_user_id_or_ip)
async def magic_request(
    request: Request,
    body: MagicRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(User).where(User.email == str(body.email)))
    user = result.scalar_one_or_none()
    if user:  # silent for unknown emails — never leak existence
        token = create_magic_token(str(user.id), user.email)
        link = f"{settings.FRONTEND_URL}/auth/magic?token={token}"
        await send_magic_link_email(user.email, link)
    return {"sent": True}


@router.get("/verify")
async def magic_verify(token: str) -> JSONResponse:
    try:
        ident = await consume_magic_token(token)
    except MagicError:
        return JSONResponse(status_code=400, content={"detail": "Link invalid or expired"})
    access = create_access_token(
        data={"sub": ident["sub"], "role": "student", "email": ident["email"]}
    )
    return JSONResponse(
        {"access_token": access, "token_type": "bearer", "user_id": ident["sub"]}
    )
