import pytest
from unittest.mock import AsyncMock, patch
from app.config import settings
from app.email import send_magic_link_email


@pytest.mark.asyncio
async def test_posts_to_brevo_with_link(monkeypatch):
    monkeypatch.setattr(settings, "BREVO_API_KEY", "key")
    mock_resp = AsyncMock(); mock_resp.status_code = 201
    with patch("app.email.httpx.AsyncClient") as Client:
        inst = Client.return_value.__aenter__.return_value
        inst.post = AsyncMock(return_value=mock_resp)
        await send_magic_link_email("buyer@x.pl", "https://learn.devince.dev/auth/magic?token=abc")
        args, kwargs = inst.post.call_args
        assert "api.brevo.com" in args[0]
        assert "abc" in str(kwargs["json"])
        assert kwargs["json"]["sender"]["email"]


@pytest.mark.asyncio
async def test_noop_when_no_key(monkeypatch):
    monkeypatch.setattr(settings, "BREVO_API_KEY", "")
    # must not raise even though no HTTP client is patched
    await send_magic_link_email("buyer@x.pl", "https://x/y")
