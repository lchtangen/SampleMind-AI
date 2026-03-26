"""asyncio Unix socket server — the JUCE plugin's Python IPC endpoint.

Phase 8 — VST3/AU Plugin.

Starts an asyncio server on ~/tmp/samplemind.sock (configurable via --socket)
and dispatches incoming length-prefixed JSON requests to the SampleRepository
and Audio Analyzer.

Startup signals readiness by writing one line to stdout:
    {"status": "ready", "version": 2, "socket": "<path>"}

Health pings respond with:
    {"version": 2, "action": "ping", "id": "...", "ok": true,
     "data": {"status": "ok", "version": 2}, "error": null}

Protocol versioning: requests MUST include "version": 2 or are rejected.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.analyzer.batch import analyze_batch
from samplemind.core.models.sample import Sample
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.sidecar.protocol import (
    PROTOCOL_VERSION,
    read_message,
    write_message,
)

logger = logging.getLogger(__name__)

DEFAULT_SOCKET_PATH: str = str(Path.home() / "tmp" / "samplemind.sock")


def _err(action: str, req_id: str | None, message: str) -> dict[str, Any]:
    """Build a standard error response dict."""
    return {
        "version": PROTOCOL_VERSION,
        "action": action,
        "id": req_id,
        "ok": False,
        "data": None,
        "error": message,
    }


def _sample_dict(sample: Sample) -> dict[str, Any]:
    """Convert a Sample ORM object to a JSON-serialisable dict."""
    return {
        "id": sample.id,
        "filename": sample.filename,
        "path": sample.path,
        "bpm": sample.bpm,
        "key": sample.key,
        "energy": sample.energy,
        "mood": sample.mood,
        "instrument": sample.instrument,
        "genre": sample.genre,
        "tags": sample.tags,
    }


async def _dispatch(request: dict[str, Any]) -> dict[str, Any]:
    """Route a request dict to the correct handler; return a response dict."""
    action: str = request.get("action", "")
    req_id: str | None = request.get("id")
    payload: dict[str, Any] = request.get("payload", {})
    version: int = request.get("version", 1)

    if version != PROTOCOL_VERSION:
        return _err(
            action,
            req_id,
            f"Unsupported protocol version {version} (expected {PROTOCOL_VERSION})",
        )

    try:
        data: Any

        if action == "ping":
            data = {"status": "ok", "version": PROTOCOL_VERSION}

        elif action == "search":
            results = SampleRepository.search(
                query=payload.get("query"),
                energy=payload.get("energy"),
                mood=payload.get("mood"),
                instrument=payload.get("instrument"),
                limit=int(payload.get("limit", 20)),
            )
            data = [_sample_dict(s) for s in results]

        elif action == "analyze":
            path: str = payload.get("path", "")
            if not path:
                raise ValueError("'path' is required for the analyze action")
            data = analyze_file(path)

        elif action == "batch_analyze":
            paths = [Path(p) for p in payload.get("paths", [])]
            # workers=1 keeps analysis in-process — safe inside an asyncio event loop
            data = analyze_batch(paths, workers=1)

        else:
            raise ValueError(f"Unknown action: {action!r}")

        return {
            "version": PROTOCOL_VERSION,
            "action": action,
            "id": req_id,
            "ok": True,
            "data": data,
            "error": None,
        }

    except Exception as exc:
        logger.warning("Dispatch error for action %r: %s", action, exc)
        return _err(action, req_id, str(exc))


async def _handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    """Handle one connected JUCE plugin client until it disconnects."""
    peer = writer.get_extra_info("peername", "<unix>")
    logger.debug("Client connected: %s", peer)
    try:
        while True:
            try:
                request = await read_message(reader)
            except asyncio.IncompleteReadError:
                break  # clean disconnect
            except (ValueError, json.JSONDecodeError) as exc:
                # Malformed message — send error and keep connection alive
                await write_message(
                    writer,
                    _err("", None, f"Protocol error: {exc}"),
                )
                continue

            response = await _dispatch(request)
            await write_message(writer, response)
    finally:
        import contextlib
        with contextlib.suppress(Exception):
            writer.close()
            await writer.wait_closed()
        logger.debug("Client disconnected: %s", peer)


async def run_server(socket_path: str = DEFAULT_SOCKET_PATH) -> None:
    """Start the Unix domain socket server and serve until cancelled.

    Writes a single-line JSON ready signal to stdout immediately after binding
    so that Tauri/JUCE can know the server is accepting connections:

        {"status": "ready", "version": 2, "socket": "<path>"}
    """
    sock = Path(socket_path)
    sock.parent.mkdir(parents=True, exist_ok=True)
    sock.unlink(missing_ok=True)  # remove stale socket from a previous run

    init_orm()

    server = await asyncio.start_unix_server(_handle_client, path=socket_path)

    # Signal readiness — Tauri/JUCE reads this line from stdout.
    # sys.stdout.write is used to avoid the ruff T201 "print found" lint warning,
    # since this output is part of the machine-readable IPC contract (not debug output).
    import sys
    sys.stdout.write(
        json.dumps(
            {"status": "ready", "version": PROTOCOL_VERSION, "socket": socket_path}
        )
        + "\n"
    )
    sys.stdout.flush()
    logger.info("Sidecar server listening on %s", socket_path)

    async with server:
        await server.serve_forever()


def main() -> None:
    """CLI entry point: uv run python -m samplemind.sidecar.server [--socket PATH]"""
    import argparse

    parser = argparse.ArgumentParser(description="SampleMind sidecar IPC server")
    parser.add_argument(
        "--socket",
        default=DEFAULT_SOCKET_PATH,
        help=f"Unix socket path (default: {DEFAULT_SOCKET_PATH})",
    )
    args = parser.parse_args()
    asyncio.run(run_server(args.socket))


if __name__ == "__main__":
    main()
