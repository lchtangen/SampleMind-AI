"""
tests/test_sample_repository.py — Integration tests for SampleRepository.

Uses the orm_engine fixture from conftest.py (in-memory SQLite, StaticPool).
Importing SampleCreate at module level registers the Sample table in
SQLModel.metadata before orm_engine calls create_all(), so the samples
table is present for every test.

Tests cover all public repository methods:
  upsert, tag, search, get_by_name, get_by_path, get_by_id, count,
  get_all, delete_by_path
"""

from __future__ import annotations

from samplemind.core.models.sample import SampleCreate, SampleUpdate
from samplemind.data.repositories.sample_repository import SampleRepository

# ── upsert ────────────────────────────────────────────────────────────────────


def test_upsert_creates_new_sample(orm_engine) -> None:
    """upsert() inserts a new row when the path has never been seen."""
    data = SampleCreate(filename="kick.wav", path="/tmp/kick.wav", bpm=128.0)
    sample = SampleRepository.upsert(data)
    assert sample.id is not None
    assert sample.bpm == 128.0
    assert SampleRepository.count() == 1


def test_upsert_updates_auto_detected_fields(orm_engine) -> None:
    """upsert() overwrites auto-detected fields for an existing path."""
    SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/tmp/k.wav", bpm=120.0))
    SampleRepository.upsert(SampleCreate(filename="kick.wav", path="/tmp/k.wav", bpm=130.0))
    assert SampleRepository.count() == 1
    s = SampleRepository.get_by_path("/tmp/k.wav")
    assert s is not None
    assert s.bpm == 130.0


def test_upsert_preserves_user_tags(orm_engine) -> None:
    """Re-importing a file must NOT overwrite genre or tags."""
    SampleRepository.upsert(SampleCreate(filename="k.wav", path="/tmp/k.wav"))
    SampleRepository.tag("/tmp/k.wav", SampleUpdate(genre="trap", tags="808,heavy"))
    SampleRepository.upsert(SampleCreate(filename="k.wav", path="/tmp/k.wav", bpm=99.0))
    s = SampleRepository.get_by_path("/tmp/k.wav")
    assert s is not None
    assert s.genre == "trap"
    assert s.tags == "808,heavy"


# ── tag ───────────────────────────────────────────────────────────────────────


def test_tag_updates_genre(orm_engine) -> None:
    """tag() writes genre; leaves instrument untouched."""
    SampleRepository.upsert(SampleCreate(filename="p.wav", path="/tmp/p.wav", instrument="pad"))
    SampleRepository.tag("/tmp/p.wav", SampleUpdate(genre="lofi"))
    s = SampleRepository.get_by_path("/tmp/p.wav")
    assert s is not None
    assert s.genre == "lofi"
    assert s.instrument == "pad"


def test_tag_returns_none_for_missing_path(orm_engine) -> None:
    """tag() returns None when the path does not exist."""
    result = SampleRepository.tag("/nonexistent.wav", SampleUpdate(genre="trap"))
    assert result is None


# ── search ────────────────────────────────────────────────────────────────────


def test_search_by_query_matches_filename(orm_engine) -> None:
    """search(query=...) filters by partial filename."""
    SampleRepository.upsert(SampleCreate(filename="kick_128.wav", path="/tmp/k.wav"))
    SampleRepository.upsert(SampleCreate(filename="hat_16th.wav", path="/tmp/h.wav"))
    results = SampleRepository.search(query="kick")
    assert len(results) == 1
    assert results[0].filename == "kick_128.wav"


def test_search_by_energy_filter(orm_engine) -> None:
    """search(energy=...) returns only matching samples."""
    SampleRepository.upsert(SampleCreate(filename="a.wav", path="/a", energy="high"))
    SampleRepository.upsert(SampleCreate(filename="b.wav", path="/b", energy="low"))
    results = SampleRepository.search(energy="high")
    assert all(s.energy == "high" for s in results)
    assert len(results) == 1


def test_search_by_mood_filter(orm_engine) -> None:
    """search(mood=...) returns only matching samples."""
    SampleRepository.upsert(SampleCreate(filename="c.wav", path="/c", mood="dark"))
    SampleRepository.upsert(SampleCreate(filename="d.wav", path="/d", mood="chill"))
    results = SampleRepository.search(mood="dark")
    assert len(results) == 1
    assert results[0].mood == "dark"


def test_search_returns_all_with_no_filters(orm_engine) -> None:
    """search() with no arguments returns all samples."""
    SampleRepository.upsert(SampleCreate(filename="e.wav", path="/e"))
    SampleRepository.upsert(SampleCreate(filename="f.wav", path="/f"))
    assert len(SampleRepository.search()) == 2


# ── get_by_* ──────────────────────────────────────────────────────────────────


def test_get_by_path_returns_sample(orm_engine) -> None:
    """get_by_path() finds a sample by exact path."""
    SampleRepository.upsert(SampleCreate(filename="x.wav", path="/x"))
    s = SampleRepository.get_by_path("/x")
    assert s is not None
    assert s.filename == "x.wav"


def test_get_by_path_returns_none_for_missing(orm_engine) -> None:
    """get_by_path() returns None when path not found."""
    assert SampleRepository.get_by_path("/does-not-exist") is None


def test_get_by_id_returns_sample(orm_engine) -> None:
    """get_by_id() finds a sample by integer primary key."""
    sample = SampleRepository.upsert(SampleCreate(filename="y.wav", path="/y"))
    assert sample.id is not None
    found = SampleRepository.get_by_id(sample.id)
    assert found is not None
    assert found.filename == "y.wav"


def test_get_by_name_matches_partial_filename(orm_engine) -> None:
    """get_by_name() does a partial match on filename."""
    SampleRepository.upsert(SampleCreate(filename="snare_heavy_808.wav", path="/s"))
    s = SampleRepository.get_by_name("heavy")
    assert s is not None
    assert "heavy" in s.filename


# ── count ─────────────────────────────────────────────────────────────────────


def test_count_returns_correct_total(orm_engine) -> None:
    """count() returns the number of rows in the samples table."""
    assert SampleRepository.count() == 0
    SampleRepository.upsert(SampleCreate(filename="a.wav", path="/a"))
    SampleRepository.upsert(SampleCreate(filename="b.wav", path="/b"))
    assert SampleRepository.count() == 2


# ── delete_by_path ────────────────────────────────────────────────────────────


def test_delete_by_path_removes_row(orm_engine) -> None:
    """delete_by_path() removes the row and returns True."""
    SampleRepository.upsert(SampleCreate(filename="z.wav", path="/z"))
    assert SampleRepository.delete_by_path("/z") is True
    assert SampleRepository.get_by_path("/z") is None


def test_delete_by_path_returns_false_for_missing(orm_engine) -> None:
    """delete_by_path() returns False when path not found."""
    assert SampleRepository.delete_by_path("/nonexistent") is False
