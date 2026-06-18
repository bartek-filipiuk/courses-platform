"""Tests for the per-user daily OpenRouter LLM-call cap (Redis-backed)."""

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.evaluation.openrouter_client import call_llm


@pytest.mark.asyncio
async def test_call_llm_blocks_over_daily_cap(monkeypatch):
    """When the per-user daily counter exceeds the cap, call_llm raises 429."""
    fake = AsyncMock()
    fake.incr.return_value = 201  # over default cap of 200
    monkeypatch.setattr(
        "app.evaluation.openrouter_client.get_redis", AsyncMock(return_value=fake)
    )
    with pytest.raises(HTTPException) as ei:
        await call_llm("s", "u", user_id=uuid.uuid4())
    assert ei.value.status_code == 429


@pytest.mark.asyncio
async def test_call_llm_allows_under_cap(monkeypatch):
    """Under the cap, call_llm proceeds and sets the 24h TTL on the first call."""
    fake = AsyncMock()
    fake.incr.return_value = 1
    monkeypatch.setattr(
        "app.evaluation.openrouter_client.get_redis", AsyncMock(return_value=fake)
    )
    monkeypatch.setattr(
        "app.evaluation.openrouter_client._http_post_llm",
        AsyncMock(return_value={"passed": True, "narrative_response": "ok"}),
    )
    out = await call_llm("s", "u", user_id=uuid.uuid4())
    assert out == {"passed": True, "narrative_response": "ok"}
    fake.expire.assert_awaited()  # TTL set on first call
