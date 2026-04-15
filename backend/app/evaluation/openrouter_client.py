"""OpenRouter API client — LLM gateway for Game Master responses."""

import json
import asyncio

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-4-6"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

FALLBACK_RESPONSE = {
    "passed": None,  # None = evaluation unavailable, don't change quest state
    "narrative_response": "Ewaluacja trwa dłużej niż zwykle. Spróbuj ponownie za chwilę.",
    "quality_scores": None,
    "matched_failure": None,
}


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> dict:
    """Call OpenRouter API with retry and structured JSON output.

    Returns parsed JSON dict with keys: passed, narrative_response, quality_scores, matched_failure.
    """
    model = model or DEFAULT_MODEL

    if not settings.OPENROUTER_API_KEY:
        logger.warning("openrouter_api_key_missing", model=model)
        return FALLBACK_RESPONSE

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                resp = await client.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                        "temperature": 0.7,
                        "max_tokens": 2000,
                    },
                )

            if resp.status_code != 200:
                logger.warning("openrouter_error", status=resp.status_code, attempt=attempt)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(2 ** (attempt - 1))
                    continue
                return FALLBACK_RESPONSE

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            # Validate required fields
            if "passed" not in parsed or "narrative_response" not in parsed:
                logger.warning("openrouter_malformed_response", parsed_keys=list(parsed.keys()))
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(2 ** (attempt - 1))
                    continue
                return FALLBACK_RESPONSE

            return parsed

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning("openrouter_timeout", error=str(e), attempt=attempt)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** (attempt - 1))
                continue
            return FALLBACK_RESPONSE

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning("openrouter_parse_error", error=str(e), attempt=attempt)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** (attempt - 1))
                continue
            return FALLBACK_RESPONSE

    return FALLBACK_RESPONSE
