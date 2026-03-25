"""
core/config.py — application settings for SampleMind AI

Load order (later overrides earlier):
  1. Hardcoded defaults below
  2. .env file in project root        (dev convenience)
  3. Environment variables            (CI / production)

All env vars use the SAMPLEMIND_ prefix (e.g. SAMPLEMIND_SECRET_KEY).
Provides a single Settings instance via get_settings() (lru_cache).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal
import warnings

from platformdirs import user_data_dir
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Paths ─────────────────────────────────────────────────────────────────────
APP_NAME = "SampleMind"
APP_DIR = Path(user_data_dir(APP_NAME, roaming=False))
DB_PATH = APP_DIR / "samplemind.db"
LEGACY_DB_PATH = Path.home() / ".samplemind" / "library.db"


def _default_database_url() -> str:
    """Return DB URL, preferring legacy path if it already exists on disk."""
    if LEGACY_DB_PATH.exists() and not DB_PATH.exists():
        return f"sqlite:///{LEGACY_DB_PATH}"
    APP_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DB_PATH}"


class Settings(BaseSettings):
    """Application settings — loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_prefix="SAMPLEMIND_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default_factory=_default_database_url,
        description="SQLAlchemy connection string. Use 'sqlite://' for in-memory testing.",
    )

    # ── Authentication ────────────────────────────────────────────────────────
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-use-secrets-token-hex-32",
        description='JWT signing key. Generate: python -c "import secrets; print(secrets.token_hex(32))"',
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ── Flask session ─────────────────────────────────────────────────────────
    # Empty string means "use secret_key" — resolved in _set_derived_defaults.
    flask_secret_key: str = Field(default="")
    flask_host: str = "127.0.0.1"
    flask_port: int = 5000

    # ── FastAPI server ────────────────────────────────────────────────────────
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:5174",  # Tauri dev
        "http://localhost:5000",  # Flask dev
        "http://localhost:8000",  # FastAPI dev
        "tauri://localhost",      # Tauri production
    ]

    # ── Audio import ──────────────────────────────────────────────────────────
    supported_extensions: tuple[str, ...] = (".wav", ".aif", ".aiff", ".flac")
    # Max file size in bytes — files larger than this are skipped. Default: 500 MB.
    max_audio_file_bytes: int = 500 * 1024 * 1024
    # Number of worker processes for parallel batch analysis. 0 = os.cpu_count().
    batch_workers: int = 0

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    log_format: Literal["console", "json"] = "console"

    # ── Environment ───────────────────────────────────────────────────────────
    environment: str = "development"

    # ── Optional integrations ─────────────────────────────────────────────────
    sentry_dsn: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    @field_validator("secret_key")
    @classmethod
    def warn_insecure_secret(cls, v: str) -> str:
        if v.startswith("CHANGE-ME"):
            warnings.warn(
                "SAMPLEMIND_SECRET_KEY is using the insecure default. "
                "Set it to a random 32-byte hex string in production.",
                UserWarning,
                stacklevel=2,
            )
        return v

    @model_validator(mode="after")
    def _set_derived_defaults(self) -> Settings:
        """Resolve fields that depend on other fields after full validation."""
        # flask_secret_key defaults to secret_key when not explicitly set
        if not self.flask_secret_key:
            object.__setattr__(self, "flask_secret_key", self.secret_key)

        # Ensure the SQLite DB directory exists (skip for in-memory / test URLs)
        if self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.removeprefix("sqlite:///"))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        return self

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    return Settings()


def override_settings(**kwargs: object) -> Settings:
    """Test helper — returns a new Settings with overrides, does not touch global."""
    return Settings(**kwargs)  # type: ignore[arg-type]
