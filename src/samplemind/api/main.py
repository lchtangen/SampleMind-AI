"""
api/main.py — FastAPI application factory for SampleMind AI

Start with:
    uv run samplemind api              # default host/port from Settings
    uv run uvicorn samplemind.api.main:app --reload   # dev

OpenAPI docs available at:
    http://localhost:8000/api/docs
    http://localhost:8000/api/redoc
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from samplemind.api import __version__
from samplemind.api.routes import auth as auth_router
from samplemind.core.auth import configure_jwt
from samplemind.core.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application startup / teardown."""
    settings = get_settings()
    logger.info("🚀 SampleMind AI API v%s starting…", __version__)

    # ── ORM tables ────────────────────────────────────────────────────────────
    from samplemind.data.orm import init_orm

    init_orm()
    logger.info("✓ SQLModel tables ready (%s)", settings.database_url)

    # ── JWT configuration ─────────────────────────────────────────────────────
    configure_jwt(
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        access_expire_minutes=settings.access_token_expire_minutes,
        refresh_expire_days=settings.refresh_token_expire_days,
    )
    logger.info(
        "✓ JWT configured (alg=%s, expire=%dm)",
        settings.algorithm,
        settings.access_token_expire_minutes,
    )

    logger.info("✅ Ready — docs at /api/docs")
    yield

    logger.info("👋 SampleMind AI API shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="SampleMind AI API",
        description=(
            "REST API for the SampleMind AI audio sample library manager.\n\n"
            "Authenticate via **POST /api/v1/auth/login** to receive a Bearer token, "
            "then use it in the `Authorization: Bearer <token>` header."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router.router, prefix="/api/v1")

    # ── Health ────────────────────────────────────────────────────────────────
    @app.get("/api/v1/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    # ── Root ──────────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse({"name": "SampleMind AI API", "docs": "/api/docs"})

    return app


# Module-level app instance (required by uvicorn)
app = create_app()


def run_server(
    host: str | None = None, port: int | None = None, reload: bool = False
) -> None:
    """Start the FastAPI server (called from the CLI command)."""
    settings = get_settings()
    uvicorn.run(
        "samplemind.api.main:app",
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=reload,
        log_level="info",
    )
