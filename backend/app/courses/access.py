"""Enrollment access guards.

Central place for "is this user allowed to touch this course/quest?" checks.
An active enrollment is required to access quest content (briefing/status/
active-quest) and evaluation (submit/hint). Without these guards any logged-in
user could consume any published course's quest/eval endpoints for free.

An "active" enrollment is one whose `revoked_at IS NULL`. A revoked enrollment
(refund/chargeback, Task 8) is excluded from both queries below, so it 403s
exactly like never having enrolled.
"""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.courses.models import Enrollment
from app.quests.models import Quest


async def require_active_enrollment_for_course(
    db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID
) -> None:
    """Raise 403 unless `user_id` has an enrollment in `course_id`."""
    row = (
        await db.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
                Enrollment.revoked_at.is_(None),
            )
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")


async def require_active_enrollment_for_quest(
    db: AsyncSession, user_id: uuid.UUID, quest_id: uuid.UUID
) -> None:
    """Raise 403 unless `user_id` is enrolled in the course the quest belongs to."""
    row = (
        await db.execute(
            select(Enrollment.user_id)
            .join(Quest, Quest.course_id == Enrollment.course_id)
            .where(
                Quest.id == quest_id,
                Enrollment.user_id == user_id,
                Enrollment.revoked_at.is_(None),
            )
        )
    ).first()
    if row is None:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")
