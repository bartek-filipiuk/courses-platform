"""Pydantic schemas for Course and Enrollment endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    narrative_title: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=5000)
    global_context: str | None = Field(None, max_length=10000)
    persona_name: str | None = Field(None, max_length=100)
    persona_prompt: str | None = Field(None, max_length=10000)
    cover_image_url: str | None = Field(None, max_length=500)
    model_id: str | None = Field(None, max_length=100)
    is_published: bool = False

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            msg = "Title must not be blank"
            raise ValueError(msg)
        return v.strip()


class CourseUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    narrative_title: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=5000)
    global_context: str | None = Field(None, max_length=10000)
    persona_name: str | None = Field(None, max_length=100)
    persona_prompt: str | None = Field(None, max_length=10000)
    cover_image_url: str | None = Field(None, max_length=500)
    model_id: str | None = Field(None, max_length=100)
    is_published: bool | None = None


class CourseResponse(BaseModel):
    id: uuid.UUID
    creator_id: uuid.UUID | None
    title: str
    narrative_title: str | None
    description: str | None
    persona_name: str | None
    cover_image_url: str | None
    model_id: str | None
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseDetailResponse(CourseResponse):
    global_context: str | None
    persona_prompt: str | None
    updated_at: datetime


class EnrollmentResponse(BaseModel):
    user_id: uuid.UUID
    course_id: uuid.UUID
    enrolled_at: datetime

    model_config = {"from_attributes": True}
