import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

app = FastAPI(
    title="NDQS Backend",
    description="Narrative-Driven Quest Sandbox — API",
    version="0.1.0",
)

# CORS — restrictive allowlist
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):  # noqa: ANN001
    try:
        return await call_next(request)
    except Exception as exc:
        if settings.ENVIRONMENT == "production":
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "traceback": traceback.format_exc(),
            },
        )


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "ndqs-backend"}


@app.get("/api/health/error-test")
async def error_test() -> None:
    msg = "Test error for exception handler verification"
    raise RuntimeError(msg)
