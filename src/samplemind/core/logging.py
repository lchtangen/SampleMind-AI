"""
core/logging.py — structured logging configuration for SampleMind-AI.

Uses structlog with two renderers:
  - Development: rich-colored human-readable output  (to stderr)
  - Production:  JSON lines, one log entry per line   (to stderr)

Machine-parseable JSON output goes to stdout for IPC consumers (Tauri/Rust).

Usage:
    from samplemind.core.logging import configure_logging, get_logger

    configure_logging()          # call once at startup
    log = get_logger(__name__)
    log.info("analyzing", path="/tmp/kick.wav", bpm=128.0)

Environment variables:
    SAMPLEMIND_LOG_LEVEL=debug   # debug / info / warning / error  (default: info)
    SAMPLEMIND_LOG_FORMAT=json   # json (prod) / console (dev)      (default: console)
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging() -> None:
    """Configure structlog for the current environment.

    Call once at application startup before any other imports that use logging.
    Safe to call multiple times — subsequent calls reconfigure structlog.
    """
    from samplemind.core.config import get_settings

    settings = get_settings()

    shared_processors: list[structlog.types.Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_format == "json":
        # Production: JSON lines — pipe to log aggregator (Sentry, Datadog, Grafana)
        processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: colored Rich console output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Map SAMPLEMIND_LOG_LEVEL string to stdlib logging level integer
    numeric_level: int = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a bound structlog logger for the given module name.

    Example:
        log = get_logger(__name__)
        log.info("sample imported", path="/tmp/kick.wav", bpm=128.0)
    """
    return structlog.get_logger(name)

