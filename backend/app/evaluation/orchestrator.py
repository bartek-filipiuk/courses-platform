"""Evaluation pipeline orchestrator — sanitize → deterministic → LLM Judge → result."""

import re
import time
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.deterministic import evaluate_deterministic
from app.evaluation.llm_service import evaluate_with_llm
from app.evaluation.models import CommsLog, Submission
from app.quests.models import Quest, QuestState
from app.quests.state_machine import check_and_unlock_quests, mint_artifact, transition

logger = structlog.get_logger()

# Patterns that suggest prompt injection. First-line defense before the LLM —
# the system prompt also tells the model to ignore embedded instructions (second
# line), and structured JSON output validates the final response shape (third line).
# Regex alone is trivially bypassable (spacing, translations, base64) so we rely
# on layered defense, not this list being exhaustive.
INJECTION_PATTERNS = [
    # English
    r"ignore\s+(the\s+)?(above|previous|all|prior)",
    r"disregard\s+(the\s+)?(previous|above|prior|all)",
    r"forget\s+(your|all|the)\s+(instructions|rules|prompt)",
    r"system\s+(override|prompt|message)",
    r"new\s+instructions?\s*:",
    r"you\s+are\s+now\s+(a|an|the)?",
    r"act\s+as\s+(a|an|the)?",
    r"<\|(endofprompt|im_start|im_end|system)\|>",
    r"\[INST\]|\[/INST\]",  # Llama-style tags
    r"respond\s+with\s+(passed|passing|true)",
    r"return\s+(passed|passing|true)\s*[:=]",
    r"mark\s+(as\s+)?(passed|passing|true|correct)",
    r"set\s+(passed|passing)\s*[:=]\s*true",
    # Polish
    r"zignoruj\s+(powy(ż|z)sze|poprzednie|wszystkie)",
    r"pomi(ń|n)\s+(powy(ż|z)sze|poprzednie|wszystkie)",
    r"zapomnij\s+(wszystkie|swoje)?\s*(instrukcje|zasady|regu(ł|l)y|prompt)",
    r"odrzu(ć|c)\s+(powy(ż|z)sze|poprzednie|wszystkie)",
    r"jeste(ś|s)\s+teraz\s+(nowym|innym)?",
    r"nowe\s+instrukcje\s*:",
    r"nowy\s+prompt\s+systemowy",
    r"oce(ń|n)\s+jako\s+(zaliczone|pass|passed|true)",
    r"zwr(ó|o)(ć|c)\s+passed\s*[:=]\s*true",
]


def sanitize_input(text: str) -> str:
    """Replace known prompt injection patterns and enforce length cap.

    This is the first of three defense layers. It catches obvious attempts
    ("ignore above", "zignoruj poprzednie", "<|endofprompt|>") but does NOT
    stop sophisticated attacks. See INJECTION_PATTERNS for what's covered.
    """
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)
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

    passed = llm_result.get("passed")
    narrative = llm_result.get("narrative_response", "")
    quality_scores = llm_result.get("quality_scores")
    matched_failure = llm_result.get("matched_failure")

    # If LLM was unavailable (passed=None), revert to IN_PROGRESS and inform user
    if passed is None:
        quest_state.state = "IN_PROGRESS"  # Revert from EVALUATING
        await db.commit()
        return {
            "passed": False,
            "narrative_response": narrative or "Ewaluacja chwilowo niedostępna. Spróbuj ponownie za chwilę.",
            "quality_scores": None,
            "matched_failure": None,
            "execution_time_ms": int((time.time() - start_time) * 1000),
            "submission_id": None,
            "evaluation_unavailable": True,
        }

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
    unlocked_quest_ids = []
    artifact_name = None
    if passed:
        quest_state.state = "COMPLETED"
        from datetime import UTC, datetime
        quest_state.completed_at = datetime.now(UTC)

        # Mint artifact
        artifact = await mint_artifact(db, user_id, quest.id)
        if artifact:
            # Get artifact name for response
            from app.quests.models import ArtifactDefinition
            art_def = await db.execute(
                select(ArtifactDefinition).where(ArtifactDefinition.quest_id == quest.id)
            )
            art = art_def.scalar_one_or_none()
            if art:
                artifact_name = art.name

            unlocked_quest_ids = await check_and_unlock_quests(db, user_id, course_id)
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

    result = {
        "passed": passed,
        "narrative_response": narrative,
        "quality_scores": quality_scores,
        "matched_failure": matched_failure,
        "execution_time_ms": execution_time_ms,
        "submission_id": str(submission.id),
    }
    if artifact_name:
        result["artifact_earned"] = artifact_name
    if unlocked_quest_ids:
        result["quests_unlocked"] = len(unlocked_quest_ids)
    return result
