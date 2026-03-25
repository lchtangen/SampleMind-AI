"""
cli/commands/api.py — ``samplemind api`` command

Starts the FastAPI server (uvicorn).  By default the server listens on
127.0.0.1:8000; override with --host / --port.

    uv run samplemind api
    uv run samplemind api --port 9000 --reload
"""

from __future__ import annotations

import sys


def serve_api(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Start the FastAPI server via uvicorn."""
    from samplemind.api.main import run_server

    print(f"🚀 SampleMind AI API → http://{host}:{port}", file=sys.stderr)
    print(f"   OpenAPI docs   → http://{host}:{port}/api/docs", file=sys.stderr)
    run_server(host=host, port=port, reload=reload)
