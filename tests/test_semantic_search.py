"""Tests for audio embeddings and VectorIndex semantic search.

Phase 11 — Semantic Search.
Covers: embed_audio() shape/dtype/determinism, VectorIndex upsert+search,
k-results, index_builder full pipeline, incremental skip behaviour.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

# Import models at module level so SQLModel.metadata knows about the samples
# table before the orm_engine fixture calls SQLModel.metadata.create_all().
import samplemind.core.models.sample  # noqa: F401
from samplemind.search.embeddings import AUDIO_DIM, embed_audio
from samplemind.search.vector_index import VectorIndex


# ── embed_audio ────────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_embed_audio_shape(silent_wav: Path) -> None:
    """embed_audio() must return a float32 array of shape (AUDIO_DIM,)."""
    vec = embed_audio(silent_wav)
    assert vec.shape == (AUDIO_DIM,)
    assert vec.dtype == np.float32


@pytest.mark.slow
def test_embed_audio_deterministic(silent_wav: Path) -> None:
    """Two calls on the same file must return identical arrays."""
    v1 = embed_audio(silent_wav)
    v2 = embed_audio(silent_wav)
    np.testing.assert_array_equal(v1, v2)


@pytest.mark.slow
def test_embed_audio_different_files_differ(silent_wav: Path, kick_wav: Path) -> None:
    """Embeddings for different audio files should differ."""
    v_silent = embed_audio(silent_wav)
    v_kick = embed_audio(kick_wav)
    assert not np.array_equal(v_silent, v_kick)


# ── VectorIndex — basic ops ────────────────────────────────────────────────────


def test_vector_index_upsert_and_search(tmp_path: Path) -> None:
    """Nearest neighbour search should return the closest vector's sample_id."""
    db = tmp_path / "vec_test.db"
    idx = VectorIndex(db_path=db)
    idx.ensure_tables()

    # Insert two embeddings: one close to query, one far
    close = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    far   = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], dtype=np.float32)
    idx.upsert_audio(sample_id=1, embedding=close)
    idx.upsert_audio(sample_id=2, embedding=far)

    query = np.array([0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    results = idx.search_audio(query, k=1)

    assert results == [1]
    idx.close()


def test_vector_index_search_returns_k_results(tmp_path: Path) -> None:
    """search_audio(k=2) must return exactly 2 results when 3 are indexed."""
    db = tmp_path / "vec_k.db"
    idx = VectorIndex(db_path=db)
    idx.ensure_tables()

    for sid in (1, 2, 3):
        vec = np.zeros(AUDIO_DIM, dtype=np.float32)
        vec[0] = float(sid) / 3
        idx.upsert_audio(sample_id=sid, embedding=vec)

    query = np.array([0.5] + [0.0] * (AUDIO_DIM - 1), dtype=np.float32)
    results = idx.search_audio(query, k=2)

    assert len(results) == 2
    idx.close()


def test_vector_index_delete(tmp_path: Path) -> None:
    """After delete(), the sample_id must not appear in search results."""
    db = tmp_path / "vec_del.db"
    idx = VectorIndex(db_path=db)
    idx.ensure_tables()

    vec = np.ones(AUDIO_DIM, dtype=np.float32)
    idx.upsert_audio(sample_id=42, embedding=vec)
    idx.delete(42)

    query = np.ones(AUDIO_DIM, dtype=np.float32)
    results = idx.search_audio(query, k=10)
    assert 42 not in results
    idx.close()


# ── Index builder ──────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_index_builder_full_pipeline(
    tmp_path: Path, silent_wav: Path, orm_engine
) -> None:
    """build_index() should embed all library samples and return indexed=1."""
    import samplemind.data.orm as orm_module

    orm_module._engine = orm_engine

    from samplemind.core.models.sample import SampleCreate
    from samplemind.data.repositories.sample_repository import SampleRepository
    from samplemind.search.index_builder import build_index

    SampleRepository.upsert(SampleCreate(
        filename=silent_wav.name,
        path=str(silent_wav),
    ))

    db_path = tmp_path / "idx.db"
    result = build_index(db_path=db_path)

    assert result["indexed"] == 1
    assert result["errors"] == 0


@pytest.mark.slow
def test_index_builder_skips_unchanged(
    tmp_path: Path, silent_wav: Path, orm_engine
) -> None:
    """Second build_index() call (no force) should skip already-indexed sample."""
    import samplemind.data.orm as orm_module

    orm_module._engine = orm_engine

    from samplemind.core.models.sample import SampleCreate
    from samplemind.data.repositories.sample_repository import SampleRepository
    from samplemind.search.index_builder import build_index

    SampleRepository.upsert(SampleCreate(
        filename=silent_wav.name,
        path=str(silent_wav),
    ))

    db_path = tmp_path / "idx_inc.db"
    # First build
    r1 = build_index(db_path=db_path)
    assert r1["indexed"] == 1

    # Second build — hash unchanged, should skip
    r2 = build_index(db_path=db_path)
    assert r2["skipped"] == 1
    assert r2["indexed"] == 0
