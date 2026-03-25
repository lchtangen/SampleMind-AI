"""
core/config.py — application settings for SampleMind AI

Reads from environment variables or .env file.
Provides a single Settings instance via get_settings() (cached).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from platformdirs import user_data_dir

# ── Paths ─────────────────────────────────────────────────────────────────────
APP_NAME = "SampleMind"
APP_DIR = Path(user_data_dir(APP_NAME, roaming=False))
DB_PATH = APP_DIR / "samplemind.db"
LEGACY_DB_PATH = Path.home() / ".samplemind" / "library.db"


class Settings:
    """Application settings — loaded once at import time."""

    # ── Database ─────────────────────────────────────────────────────────────
    # Use the canonical platformdirs path; fall back to legacy path if it exists.
    @property
    def database_url(self) -> str:
        legacy = LEGACY_DB_PATH
        if legacy.exists() and not DB_PATH.exists():
            return f"sqlite:///{legacy}"
        APP_DIR.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{DB_PATH}"

    # ── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv(
        "SAMPLEMIND_SECRET_KEY",
        # Insecure default — always override via environment in production
        "change-me-before-deployment-use-a-long-random-string",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ── Flask session ────────────────────────────────────────────────────────
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", SECRET_KEY)

    # ── OAuth providers (optional — leave empty to disable) ──────────────────
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")

    # ── Server ────────────────────────────────────────────────────────────────
    API_HOST: str = os.getenv("SAMPLEMIND_API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("SAMPLEMIND_API_PORT", "8000"))

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = [
        "http://localhost:5174",  # Tauri dev
        "http://localhost:5000",  # Flask dev
        "http://localhost:8000",  # FastAPI dev
        "tauri://localhost",      # Tauri production
    ]

    # ── Audio import ──────────────────────────────────────────────────────────
    # File extensions recognised as importable audio files.
    # Used by the import command and web upload validation.
    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".wav", ".aif", ".aiff", ".flac")

    # Maximum file size in bytes to attempt analysis.
    # Files larger than this are skipped with a warning to avoid OOM on librosa.
    # Default: 500 MB.  Override via SAMPLEMIND_MAX_AUDIO_BYTES env var.
    MAX_AUDIO_FILE_BYTES: int = int(
        os.getenv("SAMPLEMIND_MAX_AUDIO_BYTES", str(500 * 1024 * 1024))
    )

    # ── Batch processing ──────────────────────────────────────────────────────
    # Number of worker processes for parallel batch analysis.
    # 0 means os.cpu_count() — auto-detected at runtime.
    # Override via SAMPLEMIND_BATCH_WORKERS env var.
    BATCH_WORKERS: int = int(os.getenv("SAMPLEMIND_BATCH_WORKERS", "0"))

    # ── Environment ───────────────────────────────────────────────────────────
    ENVIRONMENT: str = os.getenv("SAMPLEMIND_ENV", "development")

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    return Settings()

