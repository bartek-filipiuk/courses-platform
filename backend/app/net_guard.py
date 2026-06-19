"""SSRF guard — reject non-public URLs before the server fetches them.

A learner submits the URL that ``url_check`` quests fetch, so the target host
is attacker-controlled. Without a guard the backend can be pointed at internal
services (``redis``/``db``), the host loopback, or cloud metadata
(``169.254.169.254``). ``assert_public_url`` enforces an http(s) scheme and
resolves *every* address the host maps to, rejecting any that is non-public.
"""

import ipaddress
import socket
from urllib.parse import urlparse

_ALLOWED_SCHEMES = {"http", "https"}


def _is_non_public(ip: ipaddress._BaseAddress) -> bool:
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


async def assert_public_url(url: str, *, require_https: bool = False) -> str:
    """Validate ``url`` is safe to fetch server-side and RETURN the pinned IP.

    Rejects non-http(s) schemes and any host that resolves to a private,
    loopback, link-local, reserved, multicast, or unspecified address.

    Returns the first validated (public) IP literal. Callers MUST connect to
    this exact IP — re-resolving the hostname at fetch time reopens a TOCTOU
    DNS-rebinding window (a low-TTL host can validate public then rebind to an
    internal address). See ``_evaluate_url_check`` for the IP-pinned fetch.
    """
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Disallowed scheme: {parsed.scheme!r}")
    if require_https and parsed.scheme != "https":
        raise ValueError("HTTPS required")
    host = parsed.hostname
    if not host:
        raise ValueError("No host in URL")
    # Resolve ALL addresses; reject if ANY is non-public, then pin the first.
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as e:
        raise ValueError(f"DNS resolution failed: {e}") from e
    if not infos:
        raise ValueError("DNS resolution returned no addresses")
    pinned: str | None = None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if _is_non_public(ip):
            raise ValueError(f"Non-public address blocked: {ip}")
        if pinned is None:
            pinned = info[4][0]
    assert pinned is not None  # guaranteed: infos non-empty and none rejected
    return pinned
