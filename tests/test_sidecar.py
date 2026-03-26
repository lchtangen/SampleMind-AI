"""Tests for the JUCE Python sidecar IPC server (Phase 8).

Covers:
  - encode_message() / read_message() round-trip
  - encode_message() overflow guard
  - _dispatch() for ping, search, analyze, batch_analyze
  - Protocol version enforcement
  - Unknown action handling
  - Full server startup + real Unix socket ping (integration)
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import struct

import pytest

from samplemind.sidecar.protocol import (
    MAX_MESSAGE_BYTES,
    PROTOCOL_VERSION,
    encode_message,
    read_message,
    write_message,
)
from samplemind.sidecar.server import _dispatch, run_server

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_reader(data: bytes) -> asyncio.StreamReader:
    """Wrap raw bytes in a StreamReader for testing read_message()."""
    reader = asyncio.StreamReader()
    reader.feed_data(data)
    reader.feed_eof()
    return reader


def _ping_req(req_id: str = "test-1") -> dict:
    return {"version": PROTOCOL_VERSION, "action": "ping", "id": req_id, "payload": {}}


# ── encode_message / read_message round-trip ─────────────────────────────────


@pytest.mark.asyncio
async def test_encode_decode_roundtrip() -> None:
    obj = {"version": 2, "action": "ping", "id": "abc", "payload": {}}
    raw = encode_message(obj)
    reader = _make_reader(raw)
    decoded = await read_message(reader)
    assert decoded == obj


@pytest.mark.asyncio
async def test_encode_message_has_4byte_header() -> None:
    raw = encode_message({"x": 1})
    length = struct.unpack(">I", raw[:4])[0]
    assert length == len(raw) - 4


def test_encode_message_too_large_raises() -> None:
    """A dict that serialises to > 4 MB must raise ValueError."""
    # Build a payload that is just over MAX_MESSAGE_BYTES when JSON-encoded
    big = {"data": "x" * (MAX_MESSAGE_BYTES + 1)}
    with pytest.raises(ValueError, match="too large"):
        encode_message(big)


@pytest.mark.asyncio
async def test_read_message_overflow_raises() -> None:
    """A message announcing a length > MAX_MESSAGE_BYTES must raise ValueError."""
    # Write a header claiming MAX_MESSAGE_BYTES + 1 bytes but no body
    header = struct.pack(">I", MAX_MESSAGE_BYTES + 1)
    reader = _make_reader(header)
    with pytest.raises(ValueError, match="overflow"):
        await read_message(reader)


# ── write_message ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_write_message_roundtrip(tmp_path: Path) -> None:
    """write_message() → read_message() over a real Unix socket must match."""
    obj = {"version": 2, "action": "pong", "ok": True}
    sock_path = str(tmp_path / "wm_test.sock")
    received: list[dict] = []

    async def _echo(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        msg = await read_message(reader)
        received.append(msg)
        writer.close()

    server = await asyncio.start_unix_server(_echo, path=sock_path)
    async with server:
        _c_reader, c_writer = await asyncio.open_unix_connection(sock_path)
        await write_message(c_writer, obj)
        await asyncio.sleep(0.05)  # let server coroutine complete
        c_writer.close()
        await c_writer.wait_closed()

    assert received == [obj]


# ── _dispatch — ping ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_ping(orm_engine) -> None:
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    resp = await _dispatch(_ping_req("p1"))
    assert resp["ok"] is True
    assert resp["action"] == "ping"
    assert resp["id"] == "p1"
    assert resp["data"]["status"] == "ok"
    assert resp["data"]["version"] == PROTOCOL_VERSION
    assert resp["error"] is None


# ── _dispatch — search ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_search_returns_list(orm_engine) -> None:
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    resp = await _dispatch({
        "version": PROTOCOL_VERSION,
        "action": "search",
        "id": "s1",
        "payload": {"query": "kick", "limit": 5},
    })
    assert resp["ok"] is True
    assert isinstance(resp["data"], list)


@pytest.mark.asyncio
async def test_dispatch_search_with_seeded_sample(orm_engine) -> None:
    """Seeded sample should appear in search results."""
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    from samplemind.core.models.sample import SampleCreate
    from samplemind.data.repositories.sample_repository import SampleRepository
    SampleRepository.upsert(SampleCreate(
        filename="dark_kick.wav",
        path="/tmp/dark_kick.wav",
        energy="high",
        instrument="kick",
    ))

    resp = await _dispatch({
        "version": PROTOCOL_VERSION,
        "action": "search",
        "id": "s2",
        "payload": {"instrument": "kick", "limit": 10},
    })
    assert resp["ok"] is True
    assert len(resp["data"]) >= 1
    assert resp["data"][0]["filename"] == "dark_kick.wav"


# ── _dispatch — analyze ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_analyze_missing_path(orm_engine) -> None:
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    resp = await _dispatch({
        "version": PROTOCOL_VERSION,
        "action": "analyze",
        "id": "a1",
        "payload": {},  # no 'path'
    })
    assert resp["ok"] is False
    assert "path" in resp["error"].lower()


@pytest.mark.asyncio
async def test_dispatch_analyze_with_mock(orm_engine, silent_wav: Path) -> None:
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    resp = await _dispatch({
        "version": PROTOCOL_VERSION,
        "action": "analyze",
        "id": "a2",
        "payload": {"path": str(silent_wav)},
    })
    # silent_wav is a real WAV — analyze_file should succeed
    assert resp["ok"] is True
    assert "bpm" in resp["data"]


# ── _dispatch — batch_analyze ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_batch_analyze(orm_engine, silent_wav: Path) -> None:
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    resp = await _dispatch({
        "version": PROTOCOL_VERSION,
        "action": "batch_analyze",
        "id": "b1",
        "payload": {"paths": [str(silent_wav)]},
    })
    assert resp["ok"] is True
    assert len(resp["data"]) == 1


# ── _dispatch — unknown action ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_unknown_action(orm_engine) -> None:
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    resp = await _dispatch({
        "version": PROTOCOL_VERSION,
        "action": "noop",
        "id": "u1",
        "payload": {},
    })
    assert resp["ok"] is False
    assert "Unknown action" in resp["error"]


# ── _dispatch — protocol version enforcement ──────────────────────────────────


@pytest.mark.asyncio
async def test_dispatch_wrong_protocol_version(orm_engine) -> None:
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    resp = await _dispatch({
        "version": 1,  # old version
        "action": "ping",
        "id": "v1",
        "payload": {},
    })
    assert resp["ok"] is False
    assert "version" in resp["error"].lower()


# ── Full server startup + real Unix socket ping ───────────────────────────────


@pytest.mark.asyncio
async def test_server_startup_and_ping(tmp_path: Path, orm_engine) -> None:
    """Start a real sidecar server on a temp socket, send ping, assert ok response."""
    import samplemind.data.orm as orm_module
    orm_module._engine = orm_engine

    sock_path = str(tmp_path / "test_sidecar.sock")

    # Run server in a background task
    server_task = asyncio.create_task(run_server(socket_path=sock_path))

    # Give the server a moment to bind and print its ready signal
    await asyncio.sleep(0.1)

    try:
        reader, writer = await asyncio.open_unix_connection(sock_path)
        try:
            req = _ping_req("integration-1")
            await write_message(writer, req)
            resp = await asyncio.wait_for(read_message(reader), timeout=5.0)

            assert resp["ok"] is True
            assert resp["action"] == "ping"
            assert resp["id"] == "integration-1"
            assert resp["data"]["status"] == "ok"
        finally:
            writer.close()
            await writer.wait_closed()
    finally:
        import contextlib
        server_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await server_task
