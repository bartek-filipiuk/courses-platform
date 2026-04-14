import traceback
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.config import settings
from app.logging import setup_logging
from app.middleware import CorrelationIdMiddleware, OriginCheckMiddleware, SecurityHeadersMiddleware

# Initialize structured logging
setup_logging()

logger = structlog.get_logger()

app = FastAPI(
    title="NDQS Backend",
    description="Narrative-Driven Quest Sandbox — API",
    version="0.1.0",
)

# Middleware order: outermost first in add_middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(OriginCheckMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    logger.error("unhandled_exception", error=str(exc), correlation_id=correlation_id)

    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"X-Correlation-ID": correlation_id},
        )
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "traceback": traceback.format_exc(),
        },
        headers={"X-Correlation-ID": correlation_id},
    )


app.include_router(auth_router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "ndqs-backend"}


@app.get("/api/health/error-test")
async def error_test() -> None:
    msg = "Test error for exception handler verification"
    raise RuntimeError(msg)
