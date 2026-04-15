"""Pydantic schemas for evaluation endpoints."""

import uuid

from pydantic import BaseModel, Field


class TextAnswerPayload(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)


class UrlCheckPayload(BaseModel):
    url: str = Field(..., min_length=1, max_length=500, pattern=r"^https?://")


class QuizPayload(BaseModel):
    selected_option_id: str = Field(..., min_length=1, max_length=100)


class CommandOutputPayload(BaseModel):
    command: str = Field(..., min_length=1, max_length=500)
    output: str = Field(..., min_length=1, max_length=10000)


class SubmitRequest(BaseModel):
    type: str = Field(..., pattern="^(text_answer|url_check|quiz|command_output)$")
    payload: dict


class HintRequest(BaseModel):
    context: str = Field("", max_length=2000)


class EvaluationResponse(BaseModel):
    passed: bool
    narrative_response: str
    quality_scores: dict | None = None
    matched_failure: str | None = None
    execution_time_ms: int | None = None
    submission_id: str | None = None


class HintResponse(BaseModel):
    hint: str
    hints_used: int
    hints_remaining: int
