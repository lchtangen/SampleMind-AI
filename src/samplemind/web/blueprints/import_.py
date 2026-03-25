"""
Import blueprint — SSE streaming import of WAV files.

Routes:
  POST /api/import  → Server-Sent Events stream for real-time import progress
"""

from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, Response, request, stream_with_context

from samplemind.analyzer.audio_analysis import analyze_file
from samplemind.core.models.sample import SampleCreate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

import_bp = Blueprint("import_", __name__)


def _sse_event(event_type: str, data: dict) -> str:
    """Format one Server-Sent Events message.

    SSE wire format:
      event: <TYPE>\\n
      data: <JSON>\\n
      \\n       ← blank line terminates the message
    """
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@import_bp.route("/api/import", methods=["POST"])
def import_folder():
    """Import endpoint with SSE streaming.

    The client POSTs {"folder": "/abs/path/to/samples"} and keeps the
    connection open. The server streams one SSE event per file until done.
    """
    body = request.json or {}
    folder = Path(body.get("folder", ""))
    if not folder.is_dir():
        return {"error": "Folder not found"}, 400

    wav_files = list(folder.glob("**/*.wav"))

    def generate():
        """Generator that yields SSE events — one per WAV file analysed."""
        init_orm()
        total = len(wav_files)

        yield _sse_event("start", {"total": total})

        imported = 0
        for i, wav in enumerate(wav_files, 1):
            try:
                analysis = analyze_file(str(wav))
                sample_data = SampleCreate(
                    filename=wav.name,
                    path=str(wav.resolve()),
                    **analysis,
                )
                SampleRepository.upsert(sample_data)
                imported += 1
                yield _sse_event("progress", {
                    "current": i,
                    "total": total,
                    "filename": wav.name,
                    "analysis": analysis,
                })
            except Exception as e:
                yield _sse_event("error", {"filename": wav.name, "error": str(e)})

        yield _sse_event("done", {"imported": imported, "total": total})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

