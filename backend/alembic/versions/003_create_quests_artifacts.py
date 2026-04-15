"""create quests, quest_states, artifact_definitions, user_artifacts tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Quests
    op.create_table(
        "quests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("skills", JSONB, server_default="[]"),
        sa.Column("briefing", sa.Text, nullable=False),
        sa.Column("success_response", sa.Text, nullable=True),
        sa.Column("evaluation_type", sa.String(30), nullable=False),
        sa.Column("evaluation_criteria", JSONB, server_default="{}"),
        sa.Column("failure_states", JSONB, server_default="[]"),
        sa.Column("max_hints", sa.Integer, server_default="3"),
        sa.Column("required_artifact_ids", JSONB, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_quests_course_id", "quests", ["course_id"])

    # Artifact definitions (template per quest, 1:1)
    op.create_table(
        "artifact_definitions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("icon_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Quest states (FSM state per user per quest)
    op.create_table(
        "quest_states",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(20), server_default="LOCKED", nullable=False),
        sa.Column("hints_used", sa.Integer, server_default="0"),
        sa.Column("attempts", sa.Integer, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "quest_id", name="uq_quest_states_user_quest"),
    )
    op.create_index("ix_quest_states_user_id", "quest_states", ["user_id"])
    op.create_index("ix_quest_states_quest_id", "quest_states", ["quest_id"])

    # User artifacts (awarded after quest completion)
    op.create_table(
        "user_artifacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_definition_id", UUID(as_uuid=True), sa.ForeignKey("artifact_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signature", sa.String(255), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "artifact_definition_id", name="uq_user_artifacts_user_artifact"),
    )
    op.create_index("ix_user_artifacts_user_id", "user_artifacts", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_artifacts")
    op.drop_table("quest_states")
    op.drop_table("artifact_definitions")
    op.drop_table("quests")
