"""Custom ASGI middleware for correlation ID tracking and CSRF origin validation."""

import uuid

import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import settings


class CorrelationIdMiddleware:
    """Pure ASGI middleware that adds correlation ID to requests and responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract or generate correlation ID from request headers
        headers = dict(scope.get("headers", []))
        correlation_id = (
            headers.get(b"x-correlation-id", b"").decode()
            or str(uuid.uuid4())
        )

        # Bind to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Store in scope for access in exception handlers
        scope["state"] = {**scope.get("state", {}), "correlation_id": correlation_id}

        async def send_with_correlation_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-correlation-id", correlation_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_correlation_id)


_UNSAFE_METHODS = {b"POST", b"PUT", b"PATCH", b"DELETE"}


class OriginCheckMiddleware:
    """Reject state-changing requests from unknown origins (CSRF mitigation)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.allowed_origins = {settings.FRONTEND_URL, settings.BACKEND_URL}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").encode()
        if method not in _UNSAFE_METHODS:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin", b"").decode()

        # No Origin header → server-to-server or non-browser client, allow
        if not origin:
            await self.app(scope, receive, send)
            return

        if origin not in self.allowed_origins:
            response_headers = [
                (b"content-type", b"application/json"),
            ]
            await send({
                "type": "http.response.start",
                "status": 403,
                "headers": response_headers,
            })
            await send({
                "type": "http.response.body",
                "body": b'{"detail":"Origin not allowed"}',
            })
            return

        await self.app(scope, receive, send)
