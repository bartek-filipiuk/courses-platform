"""Admin router — service-token-gated operations for the sales bridge."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.deps import require_service_token
from app.admin.service import enroll_user_by_email, revoke_enrollment
from app.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


class EnrollBody(BaseModel):
    email: EmailStr
    course_id: uuid.UUID


@router.post(
    "/enroll-by-email",
    status_code=201,
    dependencies=[Depends(require_service_token)],
)
async def enroll_by_email(
    body: EnrollBody, db: AsyncSession = Depends(get_db)
) -> dict:
    return await enroll_user_by_email(db, str(body.email), body.course_id)


@router.post(
    "/revoke-enrollment",
    dependencies=[Depends(require_service_token)],
)
async def revoke_enrollment_endpoint(
    body: EnrollBody, db: AsyncSession = Depends(get_db)
) -> dict:
    return await revoke_enrollment(db, str(body.email), body.course_id)
