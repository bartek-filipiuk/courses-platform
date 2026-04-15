"""Evaluation pipeline orchestrator — sanitize → deterministic → LLM Judge → result."""

import re
import time
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.deterministic import evaluate_deterministic
from app.evaluation.llm_service import evaluate_with_llm
from app.evaluation.models import CommsLog, Submission
from app.quests.models import Quest, QuestState
from app.quests.state_machine import check_and_unlock_quests, mint_artifact, transition

logger = structlog.get_logger()

# Patterns that suggest prompt injection
INJECTION_PATTERNS = [
    r"ignore\s+(above|previous|all)",
    r"system\s+override",
    r"<\|endofprompt\|>",
    r"forget\s+(your|all)\s+(instructions|rules)",
    r"you\s+are\s+now",
    r"new\s+instructions?:",
    r"disregard\s+(previous|above)",
]


def sanitize_input(text: str) -> str:
    """Remove potential prompt injection patterns from user input."""
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)
    # Limit length
    return sanitized[:10000]


async def evaluate_submission(
    db: AsyncSession,
    user_id: uuid.UUID,
    quest: Quest,
    quest_state: QuestState,
    payload: dict,
    course_persona_prompt: str | None = None,
    course_persona_name: str | None = None,
    course_global_context: str | None = None,
    course_model_id: str | None = None,
) -> dict:
    """Run the full evaluation pipeline and return result."""
    start_time = time.time()

    eval_type = quest.evaluation_type
    sanitized_payload = {k: sanitize_input(str(v)) if isinstance(v, str) else v for k, v in payload.items()}

    # Step 1: Deterministic checks (if applicable)
    deterministic_result = None
    if eval_type in ("quiz", "url_check", "command_output"):
        deterministic_result = await evaluate_deterministic(eval_type, sanitized_payload, quest.evaluation_criteria)

        # Quiz is deterministic-only — no LLM needed
        if eval_type == "quiz":
            passed = deterministic_result.get("passed", False)
            narrative = quest.success_response if passed else "Incorrect answer. Try again."
            return await _finalize(
                db, user_id, quest, quest_state, payload, passed, narrative,
                deterministic_result, None, None, start_time,
                course_id=quest.course_id,
            )

    # Step 2: LLM Judge
    llm_result = await evaluate_with_llm(
        quest=quest,
        student_answer=sanitized_payload,
        deterministic_results=deterministic_result,
        persona_prompt=course_persona_prompt,
        persona_name=course_persona_name,
        global_context=course_global_context,
        model_id=course_model_id,
    )

    passed = llm_result.get("passed", False)
    narrative = llm_result.get("narrative_response", "")
    quality_scores = llm_result.get("quality_scores")
    matched_failure = llm_result.get("matched_failure")

    return await _finalize(
        db, user_id, quest, quest_state, payload, passed, narrative,
        deterministic_result, quality_scores, matched_failure, start_time,
        course_id=quest.course_id,
    )


async def _finalize(
    db: AsyncSession,
    user_id: uuid.UUID,
    quest: Quest,
    quest_state: QuestState,
    payload: dict,
    passed: bool,
    narrative: str,
    test_results: dict | None,
    quality_scores: dict | None,
    matched_failure: str | None,
    start_time: float,
    course_id: uuid.UUID,
) -> dict:
    """Save submission, update FSM, mint artifact if passed, log to comms."""
    execution_time_ms = int((time.time() - start_time) * 1000)

    # Save submission
    submission = Submission(
        user_id=user_id,
        quest_id=quest.id,
        evaluation_type=quest.evaluation_type,
        payload=payload,
        status="passed" if passed else "failed",
        test_results=test_results,
        llm_response=narrative,
        quality_scores=quality_scores,
        matched_failure=matched_failure,
        execution_time_ms=execution_time_ms,
    )
    db.add(submission)

    # Update FSM
    if passed:
        quest_state.state = "COMPLETED"
        from datetime import UTC, datetime
        quest_state.completed_at = datetime.now(UTC)

        # Mint artifact
        artifact = await mint_artifact(db, user_id, quest.id)
        if artifact:
            await check_and_unlock_quests(db, user_id, course_id)
    else:
        quest_state.state = "FAILED_ATTEMPT"

    # Log to comms
    comms = CommsLog(
        user_id=user_id,
        course_id=course_id,
        quest_id=quest.id,
        message_type="evaluation",
        content=narrative,
    )
    db.add(comms)

    await db.commit()

    return {
        "passed": passed,
        "narrative_response": narrative,
        "quality_scores": quality_scores,
        "matched_failure": matched_failure,
        "execution_time_ms": execution_time_ms,
        "submission_id": str(submission.id),
    }
