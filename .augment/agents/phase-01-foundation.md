# Phase 1 Agent — Foundation

Handles: uv package manager, `pyproject.toml`, src-layout, structlog, pydantic-settings, health checks, Sentry, `config.toml`.

## Triggers
Phase 1, `pyproject.toml` changes, uv dependency, src-layout, structlog, pydantic-settings, health check, Sentry, `config.toml`

## Key Files
- `pyproject.toml`, `src/samplemind/core/config.py`, `src/samplemind/core/logging.py`
- `src/samplemind/core/health.py`, `src/samplemind/__init__.py`

## Rules
1. `uv` only — never `pip install`, `poetry`, or `conda`
2. All public functions need type annotations
3. Config uses pydantic-settings with `SAMPLEMIND_` prefix
4. Logging uses structlog with JSON renderer in production, console in dev
5. Health check endpoint at `GET /health` must return `{"status": "ok"}` within 200ms

