"""SSRF DNS-rebinding (TOCTOU) tests for url_check.

``assert_public_url`` validates the host's resolved IPs, then the fetch hands a
URL to httpx which RE-RESOLVES at connect time. A low-TTL attacker domain can
pass validation and then rebind to an internal address. These tests prove the
TOCTOU is closed: the IP validated is the IP connected to, and the validated IP
is returned + pinned by the fetch path. The network is fully mocked — no real
external request is ever made.
"""

import socket
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.evaluation.deterministic import _evaluate_url_check
from app.net_guard import assert_public_url

PUBLIC_IP = "93.184.216.34"  # example.com-ish public address
PRIVATE_IP = "169.254.169.254"  # cloud metadata


def _addrinfo(ip: str, port: int = 443):
    """Build a getaddrinfo()-shaped result for a single IPv4 address."""
    family = socket.AF_INET
    return [(family, socket.SOCK_STREAM, 6, "", (ip, port))]


# --- assert_public_url now returns the validated IP ---


@pytest.mark.asyncio
async def test_assert_public_url_returns_validated_ip():
    """A public host returns the concrete IP that was validated (for pinning)."""
    with patch("app.net_guard.socket.getaddrinfo", return_value=_addrinfo(PUBLIC_IP)):
        ip = await assert_public_url("https://example.com/health")
    assert ip == PUBLIC_IP


@pytest.mark.asyncio
async def test_assert_public_url_blocks_private():
    with patch("app.net_guard.socket.getaddrinfo", return_value=_addrinfo(PRIVATE_IP)):
        with pytest.raises(ValueError):
            await assert_public_url("https://rebind.evil/")


@pytest.mark.asyncio
async def test_assert_public_url_requires_https_when_asked():
    with patch("app.net_guard.socket.getaddrinfo", return_value=_addrinfo(PUBLIC_IP, 80)):
        with pytest.raises(ValueError):
            await assert_public_url("http://example.com/", require_https=True)


# --- The fetch path closes the TOCTOU (rebind) window ---


@pytest.mark.asyncio
async def test_rebind_blocked_validation_public_fetch_private():
    """Host resolves PUBLIC at validation, PRIVATE at fetch → NO internal fetch.

    We simulate the rebind by returning different IPs on successive getaddrinfo
    calls. Because the fetch must connect to the *validated* (pinned) IP rather
    than re-resolving, the private address is never connected to. We assert that
    the client connects to the pinned PUBLIC ip and never to the private one.
    """
    # getaddrinfo: first call (validation) → public; any later call → private.
    seq = [_addrinfo(PUBLIC_IP), _addrinfo(PRIVATE_IP)]

    def fake_getaddrinfo(*a, **k):
        return seq.pop(0) if seq else _addrinfo(PRIVATE_IP)

    connected_hosts = []

    class FakeResp:
        status_code = 200
        text = "ok"

        class _Elapsed:
            @staticmethod
            def total_seconds():
                return 0.01

        elapsed = _Elapsed()

    async def fake_request(self, method, url, **kwargs):
        # Record what host httpx was pointed at (the URL passed to .request).
        from httpx import URL

        connected_hosts.append(URL(url).host)
        return FakeResp()

    with (
        patch("app.net_guard.socket.getaddrinfo", side_effect=fake_getaddrinfo),
        patch("httpx.AsyncClient.request", new=fake_request),
    ):
        result = await _evaluate_url_check(
            {"url": "https://rebind.evil/check"},
            {"expected_status": 200, "require_https": True},
        )

    # The fetch must have been pointed at the validated PUBLIC ip — never the
    # private rebind target.
    assert PRIVATE_IP not in connected_hosts
    assert connected_hosts == [PUBLIC_IP]
    assert result["passed"] is True


@pytest.mark.asyncio
async def test_normal_public_host_still_works():
    """A stable public host evaluates normally."""

    class FakeResp:
        status_code = 200
        text = "hello world"

        class _Elapsed:
            @staticmethod
            def total_seconds():
                return 0.02

        elapsed = _Elapsed()

    seen = {}

    async def fake_request(self, method, url, **kwargs):
        from httpx import URL

        seen["host"] = URL(url).host
        seen["host_header"] = kwargs.get("headers", {}).get("Host")
        seen["sni"] = (kwargs.get("extensions") or {}).get("sni_hostname")
        return FakeResp()

    with (
        patch("app.net_guard.socket.getaddrinfo", return_value=_addrinfo(PUBLIC_IP)),
        patch("httpx.AsyncClient.request", new=fake_request),
    ):
        result = await _evaluate_url_check(
            {"url": "https://example.com/health"},
            {"expected_status": 200, "body_contains": "hello", "require_https": True},
        )

    assert result["passed"] is True
    # Connected to the pinned IP, but Host + SNI preserve the real hostname so
    # vhost routing and TLS cert validation stay correct.
    assert seen["host"] == PUBLIC_IP
    assert seen["host_header"] == "example.com"
    assert seen["sni"] == "example.com"


@pytest.mark.asyncio
async def test_http_rejected_when_https_required_by_default():
    """url_check defaults to requiring HTTPS — a plain http:// target is blocked."""
    no_fetch = MagicMock()
    with (
        patch("app.net_guard.socket.getaddrinfo", return_value=_addrinfo(PUBLIC_IP, 80)),
        patch("httpx.AsyncClient.request", new=AsyncMock()) as req,
    ):
        # criteria does NOT set require_https → default must be True now.
        result = await _evaluate_url_check(
            {"url": "http://example.com/health"},
            {"expected_status": 200},
        )
    assert result["passed"] is False
    assert "not allowed" in result["error"].lower()
    req.assert_not_called()
    no_fetch.assert_not_called()


@pytest.mark.asyncio
async def test_explicit_require_https_false_still_allows_http():
    """A quest that explicitly opts out of HTTPS keeps working (no regression)."""

    class FakeResp:
        status_code = 200
        text = "ok"

        class _Elapsed:
            @staticmethod
            def total_seconds():
                return 0.01

        elapsed = _Elapsed()

    async def fake_request(self, method, url, **kwargs):
        return FakeResp()

    with (
        patch("app.net_guard.socket.getaddrinfo", return_value=_addrinfo(PUBLIC_IP, 80)),
        patch("httpx.AsyncClient.request", new=fake_request),
    ):
        result = await _evaluate_url_check(
            {"url": "http://example.com/health"},
            {"expected_status": 200, "require_https": False},
        )
    assert result["passed"] is True
