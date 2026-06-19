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
from app.evaluation.models import record_email_failure
from app.quests.state_machine import initialize_quest_states

logger = logging.getLogger(__name__)


async def enroll_user_by_email(
    db: AsyncSession, email: str, course_id: uuid.UUID
) -> dict:
    """Upsert a user by email, enroll them in a course, init quest states, send welcome link.

    ATOMIC: the user upsert, the enrollment grant, and the quest-state init all
    commit together in ONE transaction (a single ``db.commit()`` at the end). This
    closes a partial-failure hole: previously the user, the enrollment, and the
    quest states each committed separately, so a crash AFTER the enrollment commit
    but BEFORE quest-init left an enrolled buyer with zero quests — and a webhook
    retry, seeing the enrollment already present, SKIPPED quest-init, stranding the
    buyer permanently.

    Idempotent and self-repairing:
      * no enrollment row    -> create it, then ensure quest states.
      * revoked enrollment   -> clear revoked_at (re-purchase after refund/
        chargeback RESTORES access). Quest states already exist from the original
        enroll; leave them.
      * active enrollment     -> ENSURE quest states (idempotent). This is the
        repair: a partial-failure survivor (enrollment present, states missing)
        gets its states backfilled on retry. ``initialize_quest_states`` only adds
        states for quests the user lacks one for, so this never duplicates.
    The welcome magic-link is always (re)sent, best-effort, AFTER the commit.
    """
    # 1. Upsert user by email (mirror oauth.upsert_user; provider="stripe").
    #    FLUSH (not commit) so user.id is assigned within this single transaction.
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
        await db.flush()
        created_user = True

    # 2. Load course, 404 if missing.
    res = await db.execute(select(Course).where(Course.id == course_id))
    course = res.scalar_one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    # 3. Grant access + ensure quest states, all in this same transaction.
    #    initialize_quest_states is called with commit=False so the SINGLE commit
    #    below is authoritative over the enrollment AND the quest states together.
    res = await db.execute(
        select(Enrollment).where(
            Enrollment.user_id == user.id,
            Enrollment.course_id == course_id,
        )
    )
    enrollment = res.scalar_one_or_none()
    if enrollment is None:
        # Truly new enrollment: insert the row, then ensure quest states.
        db.add(Enrollment(user_id=user.id, course_id=course_id))
        await db.flush()
        await initialize_quest_states(db, user.id, course_id, commit=False)
    elif enrollment.revoked_at is not None:
        # Re-purchase after refund/chargeback: restore access. Quest states
        # already exist from the original enroll, so do not touch them.
        enrollment.revoked_at = None
    else:
        # Active enrollment: REPAIR path. Ensure quest states exist (idempotent);
        # backfills a partial-failure survivor whose states never got created.
        await initialize_quest_states(db, user.id, course_id, commit=False)

    # Single authoritative commit for the whole unit-of-work.
    await db.commit()

    # 4. Always mint a magic token and build the welcome link. The SEND is
    #    best-effort (spec §7): a transient Brevo failure (e.g. on a re-delivered
    #    webhook) must never fail an already-successful enrollment.
    token = create_magic_token(str(user.id), user.email)
    link = f"{settings.FRONTEND_URL}/auth/magic?token={token}"
    try:
        await send_magic_link_email(user.email, link)
    except Exception as exc:
        logger.warning(
            "welcome email failed for %s (course %s); enrollment already granted",
            user.email,
            course_id,
            exc_info=True,
        )
        await record_email_failure(db, user.email, "welcome", str(exc), user_id=user.id)

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
