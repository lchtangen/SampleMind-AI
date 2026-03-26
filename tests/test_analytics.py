"""Tests for analytics engine aggregations.

Phase 14 — Analytics.
Covers: get_summary() counts, get_bpm_buckets() distribution,
get_key_counts() frequency, get_growth_timeline() monotonic cumulative,
and edge-case empty-library behaviour.
"""

from __future__ import annotations

import samplemind.data.orm as orm_module

import pytest

from samplemind.analytics.engine import (
    BpmBucket,
    LibrarySummary,
    get_bpm_buckets,
    get_growth_timeline,
    get_key_counts,
    get_summary,
)
from samplemind.core.models.sample import SampleCreate
from samplemind.data.repositories.sample_repository import SampleRepository


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _seed(orm_engine, samples: list[dict]) -> None:
    """Redirect ORM to the in-memory engine and insert samples."""
    orm_module._engine = orm_engine
    for s in samples:
        SampleRepository.upsert(SampleCreate(**s))


# ── get_summary — empty library ───────────────────────────────────────────────


def test_get_summary_empty_library(orm_engine) -> None:
    orm_module._engine = orm_engine
    summary = get_summary()
    assert isinstance(summary, LibrarySummary)
    assert summary.total == 0
    assert summary.by_energy == {}
    assert summary.bpm_min is None
    assert summary.bpm_max is None
    assert summary.bpm_mean is None


# ── get_summary — seeded samples ──────────────────────────────────────────────


def test_get_summary_with_samples(orm_engine) -> None:
    _seed(orm_engine, [
        {"filename": "a.wav", "path": "/tmp/a.wav", "energy": "high", "mood": "dark",    "instrument": "kick",  "bpm": 140.0, "key": "C maj"},
        {"filename": "b.wav", "path": "/tmp/b.wav", "energy": "mid",  "mood": "chill",   "instrument": "pad",   "bpm": 90.0,  "key": "A min"},
        {"filename": "c.wav", "path": "/tmp/c.wav", "energy": "high", "mood": "neutral", "instrument": "hihat", "bpm": 160.0, "key": "F# min"},
    ])
    summary = get_summary()
    assert summary.total == 3
    assert summary.by_energy == {"high": 2, "mid": 1}
    assert summary.by_mood == {"dark": 1, "chill": 1, "neutral": 1}
    assert summary.by_instrument == {"kick": 1, "pad": 1, "hihat": 1}
    assert summary.bpm_min == pytest.approx(90.0)
    assert summary.bpm_max == pytest.approx(160.0)
    assert summary.bpm_mean == pytest.approx(130.0)


# ── get_bpm_buckets ───────────────────────────────────────────────────────────


def test_get_bpm_buckets_empty_returns_empty_list(orm_engine) -> None:
    orm_module._engine = orm_engine
    result = get_bpm_buckets()
    assert result == []


def test_get_bpm_buckets_distribution(orm_engine) -> None:
    """80, 120, 160 BPM with 3 buckets should put one sample in each bin."""
    _seed(orm_engine, [
        {"filename": "x.wav", "path": "/tmp/x.wav", "bpm": 80.0},
        {"filename": "y.wav", "path": "/tmp/y.wav", "bpm": 120.0},
        {"filename": "z.wav", "path": "/tmp/z.wav", "bpm": 160.0},
    ])
    result = get_bpm_buckets(buckets=3)
    assert len(result) == 3
    assert all(isinstance(b, BpmBucket) for b in result)
    # Total count across all buckets must equal number of samples
    assert sum(b.count for b in result) == 3
    # Each bucket must have exactly 1 sample when values are evenly spread
    assert all(b.count == 1 for b in result)


# ── get_key_counts ────────────────────────────────────────────────────────────


def test_get_key_counts(orm_engine) -> None:
    _seed(orm_engine, [
        {"filename": "k1.wav", "path": "/tmp/k1.wav", "key": "C maj"},
        {"filename": "k2.wav", "path": "/tmp/k2.wav", "key": "C maj"},
        {"filename": "k3.wav", "path": "/tmp/k3.wav", "key": "A min"},
    ])
    counts = get_key_counts()
    assert counts["C maj"] == 2
    assert counts["A min"] == 1
    # Most common key should appear first
    keys = list(counts.keys())
    assert keys[0] == "C maj"


# ── get_growth_timeline ───────────────────────────────────────────────────────


def test_get_growth_timeline_weekly_monotonic(orm_engine) -> None:
    """Cumulative count must be non-decreasing."""
    _seed(orm_engine, [
        {"filename": "t1.wav", "path": "/tmp/t1.wav"},
        {"filename": "t2.wav", "path": "/tmp/t2.wav"},
        {"filename": "t3.wav", "path": "/tmp/t3.wav"},
    ])
    timeline = get_growth_timeline(bucket="week")
    assert len(timeline) >= 1
    counts = [t["count"] for t in timeline]
    # Cumulative — each value must be >= previous
    for i in range(1, len(counts)):
        assert counts[i] >= counts[i - 1]
    # Final count equals total samples
    assert counts[-1] == 3


def test_get_growth_timeline_empty(orm_engine) -> None:
    orm_module._engine = orm_engine
    result = get_growth_timeline()
    assert result == []
