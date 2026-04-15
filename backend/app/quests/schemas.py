"""Pydantic schemas for Quest endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class QuestBriefingResponse(BaseModel):
    id: uuid.UUID
    title: str
    briefing: str
    evaluation_type: str
    max_hints: int
    skills: list[str]

    model_config = {"from_attributes": True}


class QuestStatusResponse(BaseModel):
    quest_id: uuid.UUID
    state: str
    hints_used: int
    attempts: int
    started_at: datetime | None
    completed_at: datetime | None


class QuestListItem(BaseModel):
    id: uuid.UUID
    title: str
    sort_order: int
    evaluation_type: str
    skills: list[str]
    state: str
    has_artifact: bool


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    icon_url: str | None
    quest_title: str
    acquired_at: datetime


class QuestCreate(BaseModel):
    course_id: uuid.UUID
    sort_order: int = Field(..., ge=0)
    title: str = Field(..., min_length=1, max_length=255)
    briefing: str = Field(..., min_length=1, max_length=10000)
    evaluation_type: str = Field(..., pattern="^(text_answer|url_check|quiz|command_output)$")
    skills: list[str] = []
    success_response: str | None = None
    evaluation_criteria: dict = {}
    failure_states: list[dict] = []
    max_hints: int = Field(3, ge=0, le=10)
    required_artifact_ids: list[uuid.UUID] = []
    # Artifact reward
    artifact_name: str | None = Field(None, max_length=255)
    artifact_description: str | None = None


class QuestUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    briefing: str | None = Field(None, min_length=1, max_length=10000)
    evaluation_type: str | None = Field(None, pattern="^(text_answer|url_check|quiz|command_output)$")
    skills: list[str] | None = None
    success_response: str | None = None
    evaluation_criteria: dict | None = None
    failure_states: list[dict] | None = None
    max_hints: int | None = Field(None, ge=0, le=10)
    sort_order: int | None = Field(None, ge=0)
