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

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from samplemind.api import __version__
from samplemind.api.routes import auth as auth_router
from samplemind.core.auth import configure_jwt
from samplemind.core.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup / teardown."""
    settings = get_settings()
    logger.info("🚀 SampleMind AI API v%s starting…", __version__)

    # ── ORM tables ────────────────────────────────────────────────────────────
    from samplemind.data.orm import init_orm

    init_orm()
    logger.info("✓ SQLModel tables ready (%s)", settings.database_url)

    # ── Legacy sqlite3 database ───────────────────────────────────────────────
    from samplemind.data.database import init_db

    init_db()
    logger.info("✓ Legacy samples table ready")

    # ── JWT configuration ─────────────────────────────────────────────────────
    configure_jwt(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        access_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    logger.info("✓ JWT configured (alg=%s, expire=%dm)", settings.ALGORITHM, settings.ACCESS_TOKEN_EXPIRE_MINUTES)

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
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router.router, prefix="/api/v1")

    # ── Health ────────────────────────────────────────────────────────────────
    @app.get("/api/v1/health", tags=["Health"])
    async def health():
        return {"status": "ok", "version": __version__}

    # ── Root ──────────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse({"name": "SampleMind AI API", "docs": "/api/docs"})

    return app


# Module-level app instance (required by uvicorn)
app = create_app()


def run_server(host: str | None = None, port: int | None = None, reload: bool = False) -> None:
    """Start the FastAPI server (called from the CLI command)."""
    settings = get_settings()
    uvicorn.run(
        "samplemind.api.main:app",
        host=host or settings.API_HOST,
        port=port or settings.API_PORT,
        reload=reload,
        log_level="info",
    )

