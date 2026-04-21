"""Quest Finite State Machine — manages quest state transitions and artifact-based unlocking."""

import hashlib
import hmac
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.quests.models import ArtifactDefinition, Quest, QuestState, UserArtifact

# Valid FSM transitions
TRANSITIONS: dict[str, list[str]] = {
    "LOCKED": ["AVAILABLE"],
    "AVAILABLE": ["IN_PROGRESS"],
    "IN_PROGRESS": ["EVALUATING"],
    "EVALUATING": ["COMPLETED", "FAILED_ATTEMPT"],
    "FAILED_ATTEMPT": ["IN_PROGRESS"],
    "COMPLETED": [],
}


class FSMError(Exception):
    """Invalid state transition."""


def can_transition(from_state: str, to_state: str) -> bool:
    return to_state in TRANSITIONS.get(from_state, [])


async def transition(db: AsyncSession, quest_state: QuestState, to_state: str) -> QuestState:
    """Execute a state transition with validation."""
    if not can_transition(quest_state.state, to_state):
        raise FSMError(f"Cannot transition from {quest_state.state} to {to_state}")

    quest_state.state = to_state

    if to_state == "IN_PROGRESS" and quest_state.started_at is None:
        quest_state.started_at = datetime.now(UTC)
    elif to_state == "EVALUATING":
        quest_state.attempts += 1
    elif to_state == "COMPLETED":
        quest_state.completed_at = datetime.now(UTC)
    elif to_state == "FAILED_ATTEMPT":
        pass  # Auto-transitions back to IN_PROGRESS on next attempt

    await db.commit()
    await db.refresh(quest_state)
    return quest_state


async def initialize_quest_states(db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID) -> None:
    """Initialize quest states for a user enrolling in a course.

    First quest (no required_artifacts) → AVAILABLE, rest → LOCKED.
    """
    result = await db.execute(
        select(Quest).where(Quest.course_id == course_id).order_by(Quest.sort_order)
    )
    quests = result.scalars().all()

    for quest in quests:
        has_requirements = quest.required_artifact_ids and len(quest.required_artifact_ids) > 0
        initial_state = "LOCKED" if has_requirements else "AVAILABLE"

        qs = QuestState(
            user_id=user_id,
            quest_id=quest.id,
            state=initial_state,
        )
        db.add(qs)

    await db.commit()


def _sign_artifact(user_id: uuid.UUID, artifact_id: uuid.UUID) -> str:
    """Create HMAC SHA256 signature for an artifact."""
    message = f"{user_id}:{artifact_id}"
    return hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


async def mint_artifact(
    db: AsyncSession, user_id: uuid.UUID, quest_id: uuid.UUID
) -> UserArtifact | None:
    """Mint an artifact for a user after completing a quest. Returns None if quest has no artifact."""
    result = await db.execute(
        select(ArtifactDefinition).where(ArtifactDefinition.quest_id == quest_id)
    )
    artifact_def = result.scalar_one_or_none()
    if artifact_def is None:
        return None

    # Check if already minted
    existing = await db.execute(
        select(UserArtifact).where(
            UserArtifact.user_id == user_id,
            UserArtifact.artifact_definition_id == artifact_def.id,
        )
    )
    if existing.scalar_one_or_none():
        return None

    signature = _sign_artifact(user_id, artifact_def.id)
    user_artifact = UserArtifact(
        user_id=user_id,
        artifact_definition_id=artifact_def.id,
        signature=signature,
    )
    db.add(user_artifact)
    await db.commit()
    await db.refresh(user_artifact)
    return user_artifact


async def check_and_unlock_quests(db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID) -> list[uuid.UUID]:
    """After minting an artifact, check if any LOCKED quests can be unlocked.

    Returns list of newly unlocked quest IDs.
    """
    # Get user's artifact definition IDs as strings (required_artifact_ids comes from
    # JSONB as a list of strings, while UserArtifact.artifact_definition_id is a UUID — compare as strings).
    artifact_result = await db.execute(
        select(UserArtifact.artifact_definition_id).where(UserArtifact.user_id == user_id)
    )
    user_artifact_def_ids = {str(aid) for aid in artifact_result.scalars().all()}

    # Get all LOCKED quest states for this user in this course
    locked_result = await db.execute(
        select(QuestState, Quest)
        .join(Quest, QuestState.quest_id == Quest.id)
        .where(
            QuestState.user_id == user_id,
            QuestState.state == "LOCKED",
            Quest.course_id == course_id,
        )
    )
    locked_pairs = locked_result.all()

    unlocked_ids = []
    for quest_state, quest in locked_pairs:
        required = {str(rid) for rid in (quest.required_artifact_ids or [])}
        if required and required.issubset(user_artifact_def_ids):
            quest_state.state = "AVAILABLE"
            unlocked_ids.append(quest.id)

    if unlocked_ids:
        await db.commit()

    return unlocked_ids
