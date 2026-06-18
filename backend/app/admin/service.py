"""Admin service-to-service operations — enroll a buyer by email."""

import logging
import uuid
from datetime import datetime, timezone

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
    only initialized when a NEW enrollment is created. A previously-REVOKED
    enrollment (refund/chargeback) is RE-GRANTED by clearing revoked_at, so a
    re-purchase via this canonical paid path restores access. The welcome
    magic-link is always (re)sent.
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

    # 3. Grant access. Three cases, all idempotent:
    #    a) no enrollment row  -> create it + init quest states (truly new).
    #    b) revoked enrollment -> clear revoked_at (re-purchase after refund/
    #       chargeback RESTORES access). Quest states already exist from the
    #       original enroll, so do NOT re-run initialize_quest_states — it is
    #       not idempotent (would violate uq_quest_states_user_quest).
    #    c) active enrollment   -> nothing to do (plain idempotent re-enroll).
    res = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
        )
    )
    enrollment = res.scalar_one_or_none()
    if enrollment is None:
        db.add(Enrollment(user_id=user.id, course_id=course_id))
        await db.commit()
        await initialize_quest_states(db, user.id, course_id)
    elif enrollment.revoked_at is not None:
        enrollment.revoked_at = None
        await db.commit()

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


async def revoke_enrollment(
    db: AsyncSession, email: str, course_id: uuid.UUID
) -> dict:
    """Revoke a buyer's course access (refund/chargeback).

    Finds the user by email and the enrollment by (user_id, course_id), stamps
    `revoked_at = now()`, and commits. Idempotent: a missing user / missing
    enrollment returns {"status": "not_found"} rather than raising, and a
    re-revoke simply re-stamps revoked_at. After this, the enrollment guards in
    `app/courses/access.py` (which require `revoked_at IS NULL`) 403 the user.
    """
    # 1. Find the user by email; absent -> not_found (idempotent, no crash).
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if user is None:
        return {"email": email, "course_id": str(course_id), "status": "not_found"}

    # 2. Find the enrollment by (user_id, course_id); absent -> not_found.
    res = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
        )
    )
    enrollment = res.scalar_one_or_none()
    if enrollment is None:
        return {"email": email, "course_id": str(course_id), "status": "not_found"}

    # 3. Stamp revoked_at and commit.
    enrollment.revoked_at = datetime.now(timezone.utc)
    await db.commit()

    return {"email": email, "course_id": str(course_id), "status": "revoked"}
