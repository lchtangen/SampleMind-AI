"""Batch index rebuild pipeline: iterate library, embed, store in VectorIndex.

Phase 11 — Semantic Search.
build_index() reads all Sample rows from SampleRepository, calls embed_audio()
on each file path, and upserts the result into the VectorIndex.

Incremental strategy: we track a per-sample embedding_hash (SHA-256 of the
first 64 KB of audio, matching the fingerprinting hash in audio_analysis).
If the stored hash matches the current file, the sample is skipped.
If force=True, all samples are re-embedded regardless.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from pathlib import Path

from samplemind.data.repositories.sample_repository import SampleRepository
from samplemind.search.embeddings import embed_audio
from samplemind.search.vector_index import VectorIndex

logger = logging.getLogger(__name__)

_HASH_CHUNK = 65536  # 64 KB — same as fingerprint_file() convention


def _file_hash(path: Path) -> str:
    """SHA-256 hex digest of the first 64 KB — fast change detection."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(_HASH_CHUNK))
    return h.hexdigest()


def build_index(
    force: bool = False,
    progress_cb: Callable[[int, int], None] | None = None,
    db_path: Path | None = None,
) -> dict[str, int]:
    """Embed all library samples into the VectorIndex.

    Args:
        force: If True, re-embed all samples even if hash is unchanged.
        progress_cb: Optional callback called with (current, total) for each sample.
        db_path: Override database path (used in tests).

    Returns:
        Dict with keys "indexed", "skipped", "errors".
    """
    samples = SampleRepository.get_all()
    total = len(samples)
    indexed = 0
    skipped = 0
    errors = 0

    index = VectorIndex(db_path=db_path)
    index.ensure_tables()

    # Load existing hashes from the index to detect unchanged samples
    # We store them in a lightweight in-memory dict: sample_id -> hash
    existing_hashes: dict[int, str] = _load_hash_store(db_path)

    for i, sample in enumerate(samples):
        if progress_cb:
            progress_cb(i + 1, total)

        if sample.id is None or not sample.path:
            errors += 1
            continue

        file_path = Path(sample.path)
        if not file_path.exists():
            logger.debug("Skipping missing file: %s", sample.path)
            errors += 1
            continue

        current_hash = _file_hash(file_path)

        if not force and existing_hashes.get(sample.id) == current_hash:
            skipped += 1
            continue

        try:
            vec = embed_audio(file_path)
            index.upsert_audio(sample.id, vec)
            _save_hash(db_path, sample.id, current_hash)
            indexed += 1
            logger.debug("Indexed sample %d: %s", sample.id, sample.filename)
        except Exception as exc:
            logger.warning("Failed to embed sample %d (%s): %s", sample.id, sample.filename, exc)
            errors += 1

    index.close()
    return {"indexed": indexed, "skipped": skipped, "errors": errors}


# ── Hash persistence (lightweight key-value table) ────────────────────────────

_HASH_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS vec_embedding_hashes (
    sample_id INTEGER PRIMARY KEY,
    hash TEXT NOT NULL
)
"""


def _get_hash_conn(db_path: Path | None) -> object:
    """Return a raw sqlite3 connection to the hash store (same DB as vectors)."""
    import sqlite3  # noqa: PLC0415

    if db_path is None:
        from samplemind.core.config import get_settings  # noqa: PLC0415

        url = get_settings().database_url
        db_path = Path(url.removeprefix("sqlite:///"))

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute(_HASH_TABLE_SQL)
    conn.commit()
    return conn


def _load_hash_store(db_path: Path | None) -> dict[int, str]:
    import contextlib  # noqa: PLC0415

    conn = _get_hash_conn(db_path)
    with contextlib.closing(conn):
        rows = conn.execute("SELECT sample_id, hash FROM vec_embedding_hashes").fetchall()
    return {int(r[0]): r[1] for r in rows}


def _save_hash(db_path: Path | None, sample_id: int, file_hash: str) -> None:
    import contextlib  # noqa: PLC0415

    conn = _get_hash_conn(db_path)
    with contextlib.closing(conn):
        conn.execute(
            "INSERT OR REPLACE INTO vec_embedding_hashes(sample_id, hash) VALUES (?, ?)",
            (sample_id, file_hash),
        )
        conn.commit()
