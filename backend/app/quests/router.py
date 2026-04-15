"""Quest routes — briefing, status, list, admin CRUD, artifacts."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_token
from app.courses.router import _require_admin
from app.database import get_db
from app.quests.models import ArtifactDefinition, Quest, QuestState, UserArtifact
from app.quests.schemas import (
    ArtifactResponse,
    QuestBriefingResponse,
    QuestCreate,
    QuestListItem,
    QuestStatusResponse,
    QuestUpdate,
)

router = APIRouter(tags=["quests"])


# --- Student endpoints ---


@router.get("/api/quests/{quest_id}/briefing", response_model=QuestBriefingResponse)
async def get_briefing(
    quest_id: uuid.UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> Quest:
    """Get quest briefing. Only accessible if quest is AVAILABLE, IN_PROGRESS, or COMPLETED."""
    user_id = uuid.UUID(token_data["sub"])

    quest_state = await _get_quest_state(db, user_id, quest_id)
    if quest_state is None or quest_state.state == "LOCKED":
        raise HTTPException(status_code=403, detail="Quest is locked")

    result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = result.scalar_one_or_none()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Transition to IN_PROGRESS if AVAILABLE
    if quest_state.state == "AVAILABLE":
        quest_state.state = "IN_PROGRESS"
        from datetime import UTC, datetime
        quest_state.started_at = datetime.now(UTC)
        await db.commit()

    return quest


@router.get("/api/quests/{quest_id}/status", response_model=QuestStatusResponse)
async def get_quest_status(
    quest_id: uuid.UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_id = uuid.UUID(token_data["sub"])
    quest_state = await _get_quest_state(db, user_id, quest_id)
    if quest_state is None:
        raise HTTPException(status_code=404, detail="Quest state not found")
    return {
        "quest_id": quest_id,
        "state": quest_state.state,
        "hints_used": quest_state.hints_used,
        "attempts": quest_state.attempts,
        "started_at": quest_state.started_at,
        "completed_at": quest_state.completed_at,
    }


@router.get("/api/courses/{course_id}/quests", response_model=list[QuestListItem])
async def list_course_quests(
    course_id: uuid.UUID,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all quests in a course with their states for the current user."""
    user_id = uuid.UUID(token_data["sub"])

    result = await db.execute(
        select(Quest, QuestState)
        .outerjoin(QuestState, (QuestState.quest_id == Quest.id) & (QuestState.user_id == user_id))
        .where(Quest.course_id == course_id)
        .order_by(Quest.sort_order)
    )
    rows = result.all()

    # Check which quests have artifacts
    artifact_result = await db.execute(
        select(ArtifactDefinition.quest_id).where(ArtifactDefinition.course_id == course_id)
    )
    quests_with_artifacts = set(artifact_result.scalars().all())

    return [
        {
            "id": quest.id,
            "title": quest.title,
            "sort_order": quest.sort_order,
            "evaluation_type": quest.evaluation_type,
            "skills": quest.skills or [],
            "state": state.state if state else "LOCKED",
            "has_artifact": quest.id in quests_with_artifacts,
        }
        for quest, state in rows
    ]


@router.get("/api/users/me/artifacts", response_model=list[ArtifactResponse])
async def list_user_artifacts(
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all artifacts earned by the current user (Inventory)."""
    user_id = uuid.UUID(token_data["sub"])
    result = await db.execute(
        select(UserArtifact, ArtifactDefinition, Quest)
        .join(ArtifactDefinition, UserArtifact.artifact_definition_id == ArtifactDefinition.id)
        .join(Quest, ArtifactDefinition.quest_id == Quest.id)
        .where(UserArtifact.user_id == user_id)
        .order_by(UserArtifact.acquired_at)
    )
    rows = result.all()
    return [
        {
            "id": user_artifact.id,
            "name": artifact_def.name,
            "description": artifact_def.description,
            "icon_url": artifact_def.icon_url,
            "quest_title": quest.title,
            "acquired_at": user_artifact.acquired_at,
        }
        for user_artifact, artifact_def, quest in rows
    ]


# --- Admin endpoints ---


@router.post("/api/admin/quests", status_code=201)
async def create_quest(
    body: QuestCreate,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(token_data)

    quest = Quest(
        id=uuid.uuid4(),
        course_id=body.course_id,
        sort_order=body.sort_order,
        title=body.title,
        briefing=body.briefing,
        evaluation_type=body.evaluation_type,
        skills=body.skills,
        success_response=body.success_response,
        evaluation_criteria=body.evaluation_criteria,
        failure_states=body.failure_states,
        max_hints=body.max_hints,
        required_artifact_ids=body.required_artifact_ids,
    )
    db.add(quest)
    await db.flush()

    # Create artifact definition if provided
    artifact_id = None
    if body.artifact_name:
        artifact_def = ArtifactDefinition(
            id=uuid.uuid4(),
            course_id=body.course_id,
            quest_id=quest.id,
            name=body.artifact_name,
            description=body.artifact_description,
        )
        db.add(artifact_def)
        artifact_id = str(artifact_def.id)

    await db.commit()
    return {"id": str(quest.id), "title": quest.title, "artifact_id": artifact_id}


@router.put("/api/admin/quests/{quest_id}")
async def update_quest(
    quest_id: uuid.UUID,
    body: QuestUpdate,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(token_data)
    result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = result.scalar_one_or_none()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(quest, field, value)
    await db.commit()
    return {"id": str(quest.id), "title": quest.title, "updated": True}


# --- Helpers ---


async def _get_quest_state(
    db: AsyncSession, user_id: uuid.UUID, quest_id: uuid.UUID
) -> QuestState | None:
    result = await db.execute(
        select(QuestState).where(
            QuestState.user_id == user_id,
            QuestState.quest_id == quest_id,
        )
    )
    return result.scalar_one_or_none()
