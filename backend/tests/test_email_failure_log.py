"""Tests for record_email_failure helper (Task B2)."""

from unittest.mock import AsyncMock

import pytest

from app.evaluation.models import record_email_failure


@pytest.mark.asyncio
async def test_record_email_failure_inserts_row():
    db = AsyncMock()
    await record_email_failure(db, "a@b.c", "welcome", "boom", user_id=None)
    assert db.add.called
    assert db.commit.await_count == 1


@pytest.mark.asyncio
async def test_record_email_failure_never_raises():
    db = AsyncMock()
    db.commit.side_effect = RuntimeError("db down")
    await record_email_failure(db, "a@b.c", "magic", "boom")  # must not raise
