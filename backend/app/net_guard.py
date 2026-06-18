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


async def assert_public_url(url: str, *, require_https: bool = False) -> None:
    """Raise ``ValueError`` if ``url`` is unsafe to fetch server-side.

    Rejects non-http(s) schemes and any host that resolves to a private,
    loopback, link-local, reserved, multicast, or unspecified address.
    """
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Disallowed scheme: {parsed.scheme!r}")
    if require_https and parsed.scheme != "https":
        raise ValueError("HTTPS required")
    host = parsed.hostname
    if not host:
        raise ValueError("No host in URL")
    # Resolve ALL addresses; reject if any is non-public (DNS-rebind safe-ish).
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as e:
        raise ValueError(f"DNS resolution failed: {e}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError(f"Non-public address blocked: {ip}")
