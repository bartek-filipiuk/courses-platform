"""Admin service-to-service operations — enroll a buyer by email."""

import logging
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_magic_token
from app.auth.models import User
from app.config import settings
from app.courses.models import Course, Enrollment
from app.email import send_magic_link_email
from app.quests.state_machine import initialize_quest_states

logger = logging.getLogger(__name__)


async def enroll_user_by_email(
    db: AsyncSession, email: str, course_id: uuid.UUID
) -> dict:
    """Upsert a user by email, enroll them in a course, init quest states, send welcome link.

    Idempotent: a pre-existing enrollment is not duplicated and quest states are
    only initialized when a NEW enrollment is created. The welcome magic-link is
    always (re)sent.
    """
    # 1. Upsert user by email (mirror oauth.upsert_user; provider="stripe").
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    created_user = False
    if user is None:
        user = User(
            email=email,
            display_name=email.split("@")[0],
            provider="stripe",
            provider_id=email,
            role="student",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        created_user = True

    # 2. Load course, 404 if missing.
    res = await db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    # 3. Create enrollment only if absent; init quest states only for new enrollment.
    res = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
        )
    )
    if res.scalar_one_or_none() is None:
        db.add(Enrollment(user_id=user.id, course_id=course_id))
        await db.commit()
        await initialize_quest_states(db, user.id, course_id)

    # 4. Always mint a magic token and build the welcome link. The SEND is
    #    best-effort (spec §7): a transient Brevo failure (e.g. on a re-delivered
    #    webhook) must never fail an already-successful enrollment.
    token = create_magic_token(str(user.id), user.email)
    link = f"{settings.FRONTEND_URL}/auth/magic?token={token}"
    try:
        await send_magic_link_email(user.email, link)
    except Exception:
        logger.warning(
            "welcome email failed for %s (course %s); enrollment already granted",
            user.email,
            course_id,
            exc_info=True,
        )

    # 5. Return outcome.
    return {
        "user_id": str(user.id),
        "course_id": str(course_id),
        "status": "enrolled",
        "created_user": created_user,
    }
