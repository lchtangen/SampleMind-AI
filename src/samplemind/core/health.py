"""
core/health.py — health check aggregator for SampleMind-AI.

Each check is a callable returning a HealthResult NamedTuple.
The overall status is 'ok' only if ALL checks pass; otherwise 'degraded'.

Usage:
    from samplemind.core.health import run_all_checks
    result = run_all_checks()
    # {"status": "ok", "version": "0.2.0", "checks": [...]}

FastAPI endpoint (registered in api/main.py):
    @router.get("/api/v1/health")
    async def health() -> dict:
        return run_all_checks()
"""

from __future__ import annotations

import importlib.metadata
import sqlite3
import time
from typing import NamedTuple

from samplemind.core.config import get_settings


class HealthResult(NamedTuple):
    """Result from a single health check."""

    name: str
    ok: bool
    detail: str
    latency_ms: float


def check_database() -> HealthResult:
    """Verify that the SQLite samples table is accessible."""
    start = time.perf_counter()
    try:
        settings = get_settings()
        db_url = settings.database_url
        # Strip the SQLAlchemy scheme prefix to get the raw filesystem path
        db_path = db_url.removeprefix("sqlite:///")
        conn = sqlite3.connect(db_path, timeout=2.0)
        conn.execute("SELECT COUNT(*) FROM samples").fetchone()
        conn.close()
        ok, detail = True, f"samples table accessible at {db_path}"
    except Exception as exc:
        ok, detail = False, str(exc)
    return HealthResult("database", ok, detail, (time.perf_counter() - start) * 1000)


def check_audio_libraries() -> HealthResult:
    """Verify that librosa, soundfile, and numpy are importable."""
    start = time.perf_counter()
    try:
        import librosa  # noqa: F401
        import numpy  # noqa: F401
        import soundfile  # noqa: F401

        librosa_version = importlib.metadata.version("librosa")
        ok, detail = True, f"librosa {librosa_version}"
    except ImportError as exc:
        ok, detail = False, str(exc)
    return HealthResult("audio_libs", ok, detail, (time.perf_counter() - start) * 1000)


def run_all_checks() -> dict:
    """Run all health checks and return an aggregated status dict.

    Returns:
        {
            "status": "ok" | "degraded",
            "version": "<package version>",
            "checks": [{"name": ..., "ok": ..., "detail": ..., "latency_ms": ...}, ...]
        }
    """
    checks = [check_database(), check_audio_libraries()]
    all_ok = all(c.ok for c in checks)
    try:
        version = importlib.metadata.version("samplemind")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    return {
        "status": "ok" if all_ok else "degraded",
        "version": version,
        "checks": [
            {
                "name": c.name,
                "ok": c.ok,
                "detail": c.detail,
                "latency_ms": round(c.latency_ms, 1),
            }
            for c in checks
        ],
    }

