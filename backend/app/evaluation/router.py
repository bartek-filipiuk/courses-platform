"""Evaluation routes — submit, hint."""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_token
from app.courses.models import Course
from app.database import get_db
from app.evaluation.models import CommsLog
from app.evaluation.openrouter_client import call_llm
from app.evaluation.orchestrator import evaluate_submission
from app.evaluation.schemas import (
    CommandOutputPayload,
    EvaluationResponse,
    HintRequest,
    HintResponse,
    QuizPayload,
    SubmitRequest,
    TextAnswerPayload,
    UrlCheckPayload,
)
from app.quests.models import Quest, QuestState
from app.rate_limit import limiter

router = APIRouter(tags=["evaluation"])

SUBMIT_RATE_LIMIT = "10/hour"  # per-user per-quest (see _get_user_quest_key)
HINT_RATE_LIMIT = "10/hour"    # per-user globally (max_hints per quest already enforced)

# Payload validators per type
PAYLOAD_VALIDATORS = {
    "text_answer": TextAnswerPayload,
    "url_check": UrlCheckPayload,
    "quiz": QuizPayload,
    "command_output": CommandOutputPayload,
}


def _get_user_id_or_ip(request: Request) -> str:
    from app.auth.jwt import TokenError, decode_token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = decode_token(auth.split(" ", 1)[1])
            return payload.get("sub", request.client.host if request.client else "unknown")
        except TokenError:
            pass
    return request.client.host if request.client else "unknown"


def _get_user_quest_key(request: Request) -> str:
    """Rate-limit scope: same user + same quest. Lets a student work on
    multiple quests in parallel without one quest's retries eating budget
    for another."""
    user = _get_user_id_or_ip(request)
    quest_id = request.path_params.get("quest_id", "global")
    return f"{user}:{quest_id}"


@router.post("/api/quests/{quest_id}/submit", response_model=EvaluationResponse)
@limiter.limit(SUBMIT_RATE_LIMIT, key_func=_get_user_quest_key)
async def submit_answer(
    request: Request,
    quest_id: uuid.UUID,
    body: SubmitRequest,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit an answer for evaluation."""
    user_id = uuid.UUID(token_data["sub"])

    # Validate payload per type
    validator = PAYLOAD_VALIDATORS.get(body.type)
    if validator:
        validator(**body.payload)

    # Get quest
    quest_result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = quest_result.scalar_one_or_none()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    # Check quest type matches
    if quest.evaluation_type != body.type:
        raise HTTPException(status_code=400, detail=f"Quest expects {quest.evaluation_type}, got {body.type}")

    # Get quest state
    qs_result = await db.execute(
        select(QuestState).where(QuestState.user_id == user_id, QuestState.quest_id == quest_id)
    )
    quest_state = qs_result.scalar_one_or_none()
    if not quest_state or quest_state.state not in ("IN_PROGRESS", "FAILED_ATTEMPT"):
        raise HTTPException(status_code=400, detail="Quest is not in a submittable state")

    # Set to EVALUATING
    quest_state.state = "EVALUATING"
    quest_state.attempts += 1
    await db.commit()

    # Get course info for Game Master
    course_result = await db.execute(select(Course).where(Course.id == quest.course_id))
    course = course_result.scalar_one_or_none()

    result = await evaluate_submission(
        db=db,
        user_id=user_id,
        quest=quest,
        quest_state=quest_state,
        payload=body.payload,
        course_persona_prompt=course.persona_prompt if course else None,
        course_persona_name=course.persona_name if course else None,
        course_global_context=course.global_context if course else None,
        course_model_id=course.model_id if course else None,
    )
    return result


MAX_UPLOAD_BYTES = 100 * 1024  # 100 KB
ALLOWED_UPLOAD_EXT = {".md", ".txt"}


@router.post("/api/quests/{quest_id}/submit/file", response_model=EvaluationResponse)
@limiter.limit(SUBMIT_RATE_LIMIT, key_func=_get_user_quest_key)
async def submit_answer_from_file(
    request: Request,
    quest_id: uuid.UUID,
    file: UploadFile = File(...),
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Submit a text_answer by uploading a .md or .txt file.

    Payload gets read into the standard text_answer pipeline. Only works for
    quests whose evaluation_type is text_answer. For command_output, inline
    the output in JSON — files there would obscure the command/output split.
    """
    user_id = uuid.UUID(token_data["sub"])

    # Filename extension whitelist. MIME alone is spoofable (curl -F defaults to
    # application/octet-stream for unknown types) so we gate on extension.
    filename = (file.filename or "").lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_UPLOAD_EXT):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_UPLOAD_EXT)}",
        )

    # Size guard (read up to limit+1 to detect overflow without loading full file first)
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_BYTES} bytes")

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded") from e

    # Get quest and confirm it accepts text_answer
    quest_result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = quest_result.scalar_one_or_none()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")
    if quest.evaluation_type != "text_answer":
        raise HTTPException(
            status_code=400,
            detail=f"File upload only supports text_answer quests, this is {quest.evaluation_type}",
        )

    # Reuse validator to enforce length bounds
    TextAnswerPayload(answer=content)

    # Reuse the same state/FSM path as JSON submit
    qs_result = await db.execute(
        select(QuestState).where(QuestState.user_id == user_id, QuestState.quest_id == quest_id)
    )
    quest_state = qs_result.scalar_one_or_none()
    if not quest_state or quest_state.state not in ("IN_PROGRESS", "FAILED_ATTEMPT"):
        raise HTTPException(status_code=400, detail="Quest is not in a submittable state")

    quest_state.state = "EVALUATING"
    quest_state.attempts += 1
    await db.commit()

    course_result = await db.execute(select(Course).where(Course.id == quest.course_id))
    course = course_result.scalar_one_or_none()

    return await evaluate_submission(
        db=db,
        user_id=user_id,
        quest=quest,
        quest_state=quest_state,
        payload={"answer": content, "source_filename": filename},
        course_persona_prompt=course.persona_prompt if course else None,
        course_persona_name=course.persona_name if course else None,
        course_global_context=course.global_context if course else None,
        course_model_id=course.model_id if course else None,
    )


@router.post("/api/quests/{quest_id}/hint", response_model=HintResponse)
@limiter.limit(HINT_RATE_LIMIT, key_func=_get_user_id_or_ip)
async def request_hint(
    request: Request,
    quest_id: uuid.UUID,
    body: HintRequest,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Request a Socratic hint from the Game Master."""
    user_id = uuid.UUID(token_data["sub"])

    # Get quest and state
    quest_result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = quest_result.scalar_one_or_none()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    qs_result = await db.execute(
        select(QuestState).where(QuestState.user_id == user_id, QuestState.quest_id == quest_id)
    )
    quest_state = qs_result.scalar_one_or_none()
    if not quest_state or quest_state.state not in ("IN_PROGRESS", "FAILED_ATTEMPT"):
        raise HTTPException(status_code=400, detail="Quest is not in a hintable state")

    # Check hint limit
    if quest_state.hints_used >= quest.max_hints:
        raise HTTPException(status_code=429, detail=f"Hint limit reached ({quest.max_hints})")

    # Get course for persona
    course_result = await db.execute(select(Course).where(Course.id == quest.course_id))
    course = course_result.scalar_one_or_none()

    persona_name = course.persona_name if course else "Game Master"
    system_prompt = f"""You are {persona_name}. A student is stuck on a quest and is asking for help.
Use the Socratic method — ask guiding questions that lead them to the answer.
NEVER give the direct answer. Be concise (2-3 sentences max).
Stay in character."""

    user_prompt = f"""Quest: {quest.title}
Briefing: {quest.briefing}
Student's context: {body.context or 'No specific context provided.'}

Give a Socratic hint. Ask a question that guides them toward the solution."""

    llm_result = await call_llm(
        system_prompt, user_prompt,
        model=course.model_id if course else None,
    )
    hint_text = llm_result.get("narrative_response", llm_result.get("hint", "Think about what the briefing is asking you to do."))

    # Update hint count
    quest_state.hints_used += 1
    await db.commit()

    # Log to comms
    comms = CommsLog(
        user_id=user_id,
        course_id=quest.course_id,
        quest_id=quest_id,
        message_type="hint",
        content=hint_text,
    )
    db.add(comms)
    await db.commit()

    return {
        "hint": hint_text,
        "hints_used": quest_state.hints_used,
        "hints_remaining": quest.max_hints - quest_state.hints_used,
    }
