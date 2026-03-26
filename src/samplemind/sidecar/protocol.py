"""Length-prefixed JSON message schema for the JUCE sidecar protocol (v2).

Wire format (both directions):
  [4-byte big-endian uint32: payload length in bytes]
  [payload length bytes: UTF-8 JSON]

Supported actions: ping, search, analyze, batch_analyze

Version history:
  v1 — original (no version field)
  v2 — added required "version" field; max message size 4 MB
"""

from __future__ import annotations

import asyncio
import json
import struct
from typing import Any, TypedDict

PROTOCOL_VERSION: int = 2
MAX_MESSAGE_BYTES: int = 4 * 1024 * 1024  # 4 MB hard cap


class SidecarRequest(TypedDict, total=False):
    """Shape of a request sent by the JUCE plugin to the Python sidecar."""

    version: int       # required: must equal PROTOCOL_VERSION
    action: str        # required: "ping" | "search" | "analyze" | "batch_analyze"
    id: str | None     # optional: client correlation ID, echoed verbatim in response
    payload: dict[str, Any]  # action-specific parameters


class SidecarResponse(TypedDict):
    """Shape of every response from the Python sidecar."""

    version: int
    action: str
    id: str | None
    ok: bool
    data: Any
    error: str | None


def encode_message(obj: dict[str, Any]) -> bytes:
    """Serialize *obj* to the wire format: 4-byte big-endian length + UTF-8 JSON.

    Raises:
        ValueError: If the serialized payload exceeds MAX_MESSAGE_BYTES.
    """
    body = json.dumps(obj, default=str).encode("utf-8")
    if len(body) > MAX_MESSAGE_BYTES:
        raise ValueError(
            f"Message too large: {len(body):,} bytes (max {MAX_MESSAGE_BYTES:,})"
        )
    return struct.pack(">I", len(body)) + body


async def read_message(reader: asyncio.StreamReader) -> dict[str, Any]:
    """Read one framed message from *reader*.

    Reads the 4-byte length header, then exactly that many bytes of JSON body,
    and returns the decoded dict.

    Raises:
        asyncio.IncompleteReadError: If the connection closes mid-read.
        ValueError:                  If the announced length exceeds MAX_MESSAGE_BYTES.
        json.JSONDecodeError:        If the body is not valid JSON.
    """
    header = await reader.readexactly(4)
    length = struct.unpack(">I", header)[0]
    if length > MAX_MESSAGE_BYTES:
        raise ValueError(
            f"Incoming message overflow: {length:,} bytes (max {MAX_MESSAGE_BYTES:,})"
        )
    body = await reader.readexactly(length)
    return json.loads(body)


async def write_message(writer: asyncio.StreamWriter, obj: dict[str, Any]) -> None:
    """Write one framed message to *writer* and drain the buffer."""
    writer.write(encode_message(obj))
    await writer.drain()
