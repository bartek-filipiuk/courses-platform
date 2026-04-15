import traceback
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.auth.router import router as auth_router
from app.config import settings
from app.logging import setup_logging
from app.middleware import CorrelationIdMiddleware, OriginCheckMiddleware, SecurityHeadersMiddleware
from app.rate_limit import limiter

# Initialize structured logging
setup_logging()

logger = structlog.get_logger()

app = FastAPI(
    title="NDQS Backend",
    description="Narrative-Driven Quest Sandbox — API",
    version="0.1.0",
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Sanitize validation errors in production to avoid leaking internal details."""
    if settings.ENVIRONMENT == "production":
        clean_errors = []
        for error in exc.errors():
            loc = error.get("loc", ())
            field = ".".join(str(part) for part in loc if part != "body")
            clean_errors.append({
                "field": field or "unknown",
                "message": error.get("msg", "Invalid value"),
            })
        return JSONResponse(status_code=422, content={"detail": clean_errors})

    # In development, return full Pydantic error details for debugging
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


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
