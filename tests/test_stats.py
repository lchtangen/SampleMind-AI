"""
tests/test_stats.py — Unit tests for the stats command helpers.

Covers:
  _pct()          — percentage formatting helper
  _compute_stats() — pure data-extraction function (no Rich output)
  print_stats()   — JSON stdout path (--json mode)

These tests bypass Rich terminal output entirely — the JSON mode path and the
helper functions are the only things exercised here.  Rich table rendering
requires a live console; that branch is validated by manual smoke testing.
"""

from __future__ import annotations

from io import StringIO
import json
import sys

from samplemind.cli.commands.stats import _compute_stats, _pct, print_stats
from samplemind.core.models.sample import SampleCreate
from samplemind.data.repositories.sample_repository import SampleRepository

# ── _pct ──────────────────────────────────────────────────────────────────────


def test_pct_zero_total_returns_dash() -> None:
    """_pct(n, 0) must return '—' without dividing by zero."""
    assert _pct(5, 0) == "—"


def test_pct_normal_case() -> None:
    """_pct(1, 4) should be '25.0 %'."""
    assert _pct(1, 4) == "25.0 %"


def test_pct_full_percent() -> None:
    """_pct(10, 10) should be '100.0 %'."""
    assert _pct(10, 10) == "100.0 %"


# ── _compute_stats ────────────────────────────────────────────────────────────


def test_compute_stats_empty_library(orm_engine) -> None:
    """_compute_stats([]) returns sensible zero-filled result."""
    stats = _compute_stats([])
    assert stats["total"] == 0
    assert stats["with_bpm"] == 0
    assert stats["bpm"] is None
    assert stats["by_energy"] == {}
    assert stats["by_instrument"] == {}
    assert stats["by_mood"] == {}


def test_compute_stats_with_samples(orm_engine) -> None:
    """_compute_stats returns correct totals and BPM statistics."""
    SampleRepository.upsert(
        SampleCreate(filename="a.wav", path="/a", bpm=120.0, energy="high", mood="dark", instrument="kick")
    )
    SampleRepository.upsert(
        SampleCreate(filename="b.wav", path="/b", bpm=140.0, energy="mid", mood="chill", instrument="hihat")
    )
    samples = SampleRepository.get_all()
    stats = _compute_stats(samples)

    assert stats["total"] == 2
    assert stats["with_bpm"] == 2
    assert stats["without_bpm"] == 0
    assert stats["bpm"] is not None
    assert stats["bpm"]["min"] == 120.0
    assert stats["bpm"]["max"] == 140.0
    assert stats["bpm"]["mean"] == 130.0
    assert stats["by_energy"]["high"] == 1
    assert stats["by_energy"]["mid"] == 1
    assert stats["by_mood"]["dark"] == 1
    assert stats["by_instrument"]["kick"] == 1


def test_compute_stats_without_bpm(orm_engine) -> None:
    """Samples without BPM are counted separately; bpm stats key is None."""
    SampleRepository.upsert(SampleCreate(filename="no_bpm.wav", path="/no_bpm"))
    samples = SampleRepository.get_all()
    stats = _compute_stats(samples)

    assert stats["total"] == 1
    assert stats["with_bpm"] == 0
    assert stats["without_bpm"] == 1
    assert stats["bpm"] is None


# ── print_stats --json mode ───────────────────────────────────────────────────


def test_print_stats_json_mode_outputs_valid_json(orm_engine) -> None:
    """print_stats(json_output=True) writes valid JSON to stdout."""
    SampleRepository.upsert(
        SampleCreate(filename="k.wav", path="/k", bpm=128.0, energy="high")
    )

    captured = StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured
    try:
        print_stats(json_output=True)
    finally:
        sys.stdout = original_stdout

    output = captured.getvalue().strip()
    data = json.loads(output)  # must be valid JSON
    assert data["total"] == 1
    assert data["with_bpm"] == 1
    assert data["bpm"]["min"] == 128.0
    assert "by_energy" in data
    assert "by_instrument" in data
    assert "by_mood" in data


def test_print_stats_json_empty_library(orm_engine) -> None:
    """print_stats --json with no samples returns total=0 without raising."""
    captured = StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured
    try:
        print_stats(json_output=True)
    finally:
        sys.stdout = original_stdout

    data = json.loads(captured.getvalue().strip())
    assert data["total"] == 0
    assert data["bpm"] is None
