"""sqlite-vec vector index for nearest-neighbour audio/text search.

Phase 11 — Semantic Search.
VectorIndex stores float32 embeddings in two virtual tables inside a SQLite
database (the same library DB by default):
  vec_audio_embeddings(sample_id INT, embedding FLOAT[10])
  vec_text_embeddings(sample_id INT, embedding FLOAT[384])

Uses the sqlite-vec extension (already a core dependency).
"""

from __future__ import annotations

from pathlib import Path
import sqlite3

import numpy as np
import sqlite_vec

from samplemind.search.embeddings import AUDIO_DIM, CLAP_DIM, TEXT_DIM


class VectorIndex:
    """sqlite-vec wrapper for audio and text embedding storage and KNN search."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Open (or create) the vector index database.

        Args:
            db_path: Path to the SQLite file. Defaults to the library database
                     resolved via get_settings().database_url. Pass ':memory:'
                     or a tmp_path for testing.
        """
        if db_path is None:
            from samplemind.core.config import get_settings

            url = get_settings().database_url  # "sqlite:///path/to/db"
            db_path = Path(url.removeprefix("sqlite:///"))

        self._db_path = str(db_path)
        self._conn = self._open_connection()

    def _open_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return conn

    # ── Table setup ───────────────────────────────────────────────────────────

    def ensure_tables(self) -> None:
        """Create virtual tables if they do not already exist."""
        self._conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_audio_embeddings "
            f"USING vec0(sample_id INTEGER PRIMARY KEY, embedding FLOAT[{AUDIO_DIM}])"
        )
        self._conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_text_embeddings "
            f"USING vec0(sample_id INTEGER PRIMARY KEY, embedding FLOAT[{TEXT_DIM}])"
        )
        self._conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_clap_embeddings "
            f"USING vec0(sample_id INTEGER PRIMARY KEY, embedding FLOAT[{CLAP_DIM}])"
        )
        self._conn.commit()

    # ── Upsert ────────────────────────────────────────────────────────────────

    def upsert_audio(self, sample_id: int, embedding: np.ndarray) -> None:
        """Insert or replace an audio embedding for sample_id."""
        blob = sqlite_vec.serialize_float32(embedding.tolist())
        self._conn.execute(
            "INSERT OR REPLACE INTO vec_audio_embeddings(sample_id, embedding) VALUES (?, ?)",
            (sample_id, blob),
        )
        self._conn.commit()

    def upsert_text(self, sample_id: int, embedding: np.ndarray) -> None:
        """Insert or replace a text embedding for sample_id."""
        blob = sqlite_vec.serialize_float32(embedding.tolist())
        self._conn.execute(
            "INSERT OR REPLACE INTO vec_text_embeddings(sample_id, embedding) VALUES (?, ?)",
            (sample_id, blob),
        )
        self._conn.commit()

    # ── Search ────────────────────────────────────────────────────────────────

    def search_audio(self, query_vec: np.ndarray, k: int = 10) -> list[int]:
        """Return the k nearest audio neighbours (sample_ids, ascending distance).

        Args:
            query_vec: float32 array of shape (AUDIO_DIM,).
            k: Number of results.

        Returns:
            List of sample_ids sorted by ascending distance.
        """
        blob = sqlite_vec.serialize_float32(query_vec.tolist())
        rows = self._conn.execute(
            "SELECT sample_id FROM vec_audio_embeddings "
            "WHERE embedding MATCH ? "
            "ORDER BY distance LIMIT ?",
            (blob, k),
        ).fetchall()
        return [int(r[0]) for r in rows]

    def search_text(self, query_vec: np.ndarray, k: int = 10) -> list[int]:
        """Return the k nearest text neighbours (sample_ids, ascending distance).

        Args:
            query_vec: float32 array of shape (TEXT_DIM,).
            k: Number of results.

        Returns:
            List of sample_ids sorted by ascending distance.
        """
        blob = sqlite_vec.serialize_float32(query_vec.tolist())
        rows = self._conn.execute(
            "SELECT sample_id FROM vec_text_embeddings "
            "WHERE embedding MATCH ? "
            "ORDER BY distance LIMIT ?",
            (blob, k),
        ).fetchall()
        return [int(r[0]) for r in rows]

    def upsert_clap(self, sample_id: int, embedding: np.ndarray) -> None:
        """Insert or replace a CLAP audio embedding for sample_id."""
        blob = sqlite_vec.serialize_float32(embedding.tolist())
        self._conn.execute(
            "INSERT OR REPLACE INTO vec_clap_embeddings(sample_id, embedding) VALUES (?, ?)",
            (sample_id, blob),
        )
        self._conn.commit()

    def search_clap(self, query_vec: np.ndarray, k: int = 10) -> list[int]:
        """Return k nearest CLAP neighbours (sample_ids, ascending distance).

        Args:
            query_vec: L2-normalized float32 array of shape (CLAP_DIM,).
            k: Number of results.

        Returns:
            List of sample_ids sorted by ascending distance.
        """
        blob = sqlite_vec.serialize_float32(query_vec.tolist())
        rows = self._conn.execute(
            "SELECT sample_id FROM vec_clap_embeddings "
            "WHERE embedding MATCH ? "
            "ORDER BY distance LIMIT ?",
            (blob, k),
        ).fetchall()
        return [int(r[0]) for r in rows]

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, sample_id: int) -> None:
        """Remove all embeddings for sample_id (audio, text, and CLAP)."""
        self._conn.execute(
            "DELETE FROM vec_audio_embeddings WHERE sample_id = ?", (sample_id,)
        )
        self._conn.execute(
            "DELETE FROM vec_text_embeddings WHERE sample_id = ?", (sample_id,)
        )
        self._conn.execute(
            "DELETE FROM vec_clap_embeddings WHERE sample_id = ?", (sample_id,)
        )
        self._conn.commit()

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()

    def __enter__(self) -> VectorIndex:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
