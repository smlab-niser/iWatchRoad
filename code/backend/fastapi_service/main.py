"""
iWatchRoad — FastAPI Internal Service
======================================
Runs on Unix socket: /run/fastapi-iwatchroad/fastapi.sock
NEVER exposed via Nginx. Called ONLY by Django internally.

Start command (managed by systemd):
    uvicorn fastapi_service.main:app \\
        --uds /run/fastapi-iwatchroad/fastapi.sock \\
        --workers 2 \\
        --log-level info \\
        --no-access-log
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fastapi_service.routers import analytics, postprocess, validate

logger = logging.getLogger("fastapi_service")


# ── Lifespan: startup / shutdown hooks ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("iWatchRoad FastAPI service starting on Unix socket")
    yield
    logger.info("iWatchRoad FastAPI service shutting down")


# ── App factory ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="iWatchRoad Internal API",
    description=(
        "Internal FastAPI service for ML result validation, "
        "post-processing, and analytics aggregation. "
        "Not publicly accessible — Unix socket only."
    ),
    version="1.0.0",
    docs_url=None,       # Disable Swagger UI (internal service — no public docs)
    redoc_url=None,      # Disable ReDoc
    openapi_url=None,    # Disable OpenAPI schema endpoint
    lifespan=lifespan,
)


# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(validate.router, tags=["validation"])
app.include_router(postprocess.router, tags=["postprocessing"])
app.include_router(analytics.router, tags=["analytics"])


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    """
    Liveness probe used by:
      - systemd (via ExecStartPost if needed)
      - Django (to check FastAPI is up before calling it)
      - Manual: curl --unix-socket /run/fastapi-iwatchroad/fastapi.sock http://localhost/health
    """
    return {"status": "ok", "service": "fastapi-iwatchroad"}


# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler so FastAPI never returns an unstructured 500.
    Django's client checks for non-2xx and triggers fallback logic.
    """
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal FastAPI error", "path": str(request.url.path)},
    )
