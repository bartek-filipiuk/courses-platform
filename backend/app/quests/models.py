"""Quest, QuestState, ArtifactDefinition, UserArtifact models."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    skills: Mapped[list] = mapped_column(JSONB, server_default="[]")
    briefing: Mapped[str] = mapped_column(Text, nullable=False)
    success_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_type: Mapped[str] = mapped_column(
        Enum("text_answer", "url_check", "quiz", "command_output", name="evaluation_type", create_type=False),
        nullable=False,
    )
    evaluation_criteria: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    failure_states: Mapped[list] = mapped_column(JSONB, server_default="[]")
    max_hints: Mapped[int] = mapped_column(Integer, server_default="3")
    required_artifact_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ArtifactDefinition(Base):
    __tablename__ = "artifact_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class QuestState(Base):
    __tablename__ = "quest_states"
    __table_args__ = (
        UniqueConstraint("user_id", "quest_id", name="uq_quest_states_user_quest"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quests.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[str] = mapped_column(
        Enum("LOCKED", "AVAILABLE", "IN_PROGRESS", "EVALUATING", "COMPLETED", "FAILED_ATTEMPT",
             name="quest_state", create_type=False),
        server_default="LOCKED",
        nullable=False,
    )
    hints_used: Mapped[int] = mapped_column(Integer, server_default="0")
    attempts: Mapped[int] = mapped_column(Integer, server_default="0")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserArtifact(Base):
    __tablename__ = "user_artifacts"
    __table_args__ = (
        UniqueConstraint("user_id", "artifact_definition_id", name="uq_user_artifacts_user_artifact"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    artifact_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_definitions.id", ondelete="CASCADE"), nullable=False
    )
    signature: Mapped[str] = mapped_column(String(255), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
