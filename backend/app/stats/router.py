"""Stats, Comms Log, and Analytics routes."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_token
from app.courses.models import Course
from app.courses.router import _require_admin
from app.database import get_db
from app.evaluation.models import CommsLog, Submission
from app.quests.models import Quest, QuestState

router = APIRouter(tags=["stats"])


# --- Comms Log ---


@router.get("/api/courses/{course_id}/comms-log")
async def get_comms_log(
    course_id: uuid.UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
    quest_id: uuid.UUID | None = Query(None),
    message_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> dict:
    """Get comms log for current user in a course. Paginated, filterable."""
    user_id = uuid.UUID(token_data["sub"])

    query = (
        select(CommsLog)
        .where(CommsLog.user_id == user_id, CommsLog.course_id == course_id)
        .order_by(CommsLog.created_at.desc())
    )

    if quest_id:
        query = query.where(CommsLog.quest_id == quest_id)
    if message_type:
        query = query.where(CommsLog.message_type == message_type)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    entries = result.scalars().all()

    return {
        "items": [
            {
                "id": str(e.id),
                "quest_id": str(e.quest_id) if e.quest_id else None,
                "message_type": e.message_type,
                "content": e.content,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# --- User Stats ---


@router.get("/api/users/me/stats")
async def get_user_stats(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current user's statistics across all courses."""
    user_id = uuid.UUID(token_data["sub"])

    # Quest states
    qs_result = await db.execute(
        select(QuestState).where(QuestState.user_id == user_id)
    )
    quest_states = qs_result.scalars().all()

    total_quests = len(quest_states)
    completed = sum(1 for qs in quest_states if qs.state == "COMPLETED")
    in_progress = sum(1 for qs in quest_states if qs.state == "IN_PROGRESS")
    total_attempts = sum(qs.attempts for qs in quest_states)
    total_hints = sum(qs.hints_used for qs in quest_states)

    # Quality scores from submissions
    score_result = await db.execute(
        select(Submission.quality_scores)
        .where(Submission.user_id == user_id, Submission.status == "passed", Submission.quality_scores.isnot(None))
    )
    scores = [s for (s,) in score_result.all() if s]

    avg_scores = None
    if scores:
        dims = ["completeness", "understanding", "efficiency", "creativity"]
        avg_scores = {}
        for dim in dims:
            vals = [s.get(dim, 0) for s in scores if dim in s]
            avg_scores[dim] = round(sum(vals) / len(vals), 1) if vals else 0

    # Streak (days with activity)
    activity_result = await db.execute(
        select(func.distinct(func.date(Submission.created_at)))
        .where(Submission.user_id == user_id)
        .order_by(func.date(Submission.created_at).desc())
        .limit(30)
    )
    active_dates = [d for (d,) in activity_result.all()]
    streak = 0
    if active_dates:
        from datetime import date, timedelta
        today = date.today()
        for i, d in enumerate(active_dates):
            if d == today - timedelta(days=i):
                streak += 1
            else:
                break

    return {
        "total_quests": total_quests,
        "completed": completed,
        "in_progress": in_progress,
        "progress_pct": round(completed / total_quests * 100, 1) if total_quests > 0 else 0,
        "total_attempts": total_attempts,
        "total_hints_used": total_hints,
        "quality_scores": avg_scores,
        "streak_days": streak,
    }


# --- Admin Analytics ---


@router.get("/api/admin/analytics/{course_id}")
async def get_course_analytics(
    course_id: uuid.UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get course analytics for admin."""
    _require_admin(token_data)

    # Completion funnel
    qs_result = await db.execute(
        select(QuestState.state, func.count())
        .join(Quest, QuestState.quest_id == Quest.id)
        .where(Quest.course_id == course_id)
        .group_by(QuestState.state)
    )
    state_counts = dict(qs_result.all())

    # Avg attempts per quest
    avg_result = await db.execute(
        select(func.avg(QuestState.attempts))
        .join(Quest, QuestState.quest_id == Quest.id)
        .where(Quest.course_id == course_id, QuestState.state == "COMPLETED")
    )
    avg_attempts = round(float(avg_result.scalar() or 0), 1)

    # Hint usage
    hint_result = await db.execute(
        select(func.sum(QuestState.hints_used))
        .join(Quest, QuestState.quest_id == Quest.id)
        .where(Quest.course_id == course_id)
    )
    total_hints = int(hint_result.scalar() or 0)

    # Submission count
    sub_result = await db.execute(
        select(func.count())
        .select_from(Submission)
        .join(Quest, Submission.quest_id == Quest.id)
        .where(Quest.course_id == course_id)
    )
    total_submissions = int(sub_result.scalar() or 0)

    return {
        "course_id": str(course_id),
        "state_distribution": state_counts,
        "avg_attempts_to_complete": avg_attempts,
        "total_hints_used": total_hints,
        "total_submissions": total_submissions,
    }
