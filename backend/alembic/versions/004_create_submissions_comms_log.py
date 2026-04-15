"""create submissions and comms_log tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evaluation_type", sa.String(30), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("test_results", JSONB, nullable=True),
        sa.Column("llm_response", sa.Text, nullable=True),
        sa.Column("quality_scores", JSONB, nullable=True),
        sa.Column("matched_failure", sa.String(100), nullable=True),
        sa.Column("execution_time_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_submissions_user_quest", "submissions", ["user_id", "quest_id"])
    op.create_index("ix_submissions_created_at", "submissions", ["created_at"])

    op.create_table(
        "comms_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("message_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_comms_log_user_course", "comms_log", ["user_id", "course_id"])
    op.create_index("ix_comms_log_created_at", "comms_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("comms_log")
    op.drop_table("submissions")
