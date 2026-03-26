"""Tests for the AI curation agent and smart playlist generation.

Phase 12 — AI Curation.
Covers: playlist_by_energy() ordering, empty energy returns empty,
gap_analysis() identifies missing instruments, gap_analysis() surplus,
and CuratorAgent with pydantic-ai TestModel (no real API calls).
"""

from __future__ import annotations

import samplemind.core.models.sample  # noqa: F401  -- registers Sample in SQLModel.metadata
import samplemind.data.orm as orm_module

import pytest

from samplemind.agent.playlist import gap_analysis, playlist_by_energy
from samplemind.core.models.sample import SampleCreate
from samplemind.data.repositories.sample_repository import SampleRepository


# ── Helpers ───────────────────────────────────────────────────────────────────


def _seed(orm_engine, samples: list[dict]) -> None:
    orm_module._engine = orm_engine
    for s in samples:
        SampleRepository.upsert(SampleCreate(**s))


# ── playlist_by_energy ────────────────────────────────────────────────────────


def test_playlist_by_energy_ordering(orm_engine) -> None:
    """Playlist should follow the energy arc sequence."""
    _seed(orm_engine, [
        {"filename": "lo1.wav", "path": "/tmp/lo1.wav", "energy": "low",  "instrument": "pad"},
        {"filename": "lo2.wav", "path": "/tmp/lo2.wav", "energy": "low",  "instrument": "pad"},
        {"filename": "hi1.wav", "path": "/tmp/hi1.wav", "energy": "high", "instrument": "kick"},
        {"filename": "hi2.wav", "path": "/tmp/hi2.wav", "energy": "high", "instrument": "kick"},
    ])
    arc = ["low", "high", "low", "high"]
    playlist = playlist_by_energy(arc, limit_per_step=5)
    assert len(playlist) == 4
    energies = [s.energy for s in playlist]
    assert energies == ["low", "high", "low", "high"]


def test_playlist_by_energy_empty_energy_returns_empty(orm_engine) -> None:
    """When no samples match the requested energy, result is empty."""
    _seed(orm_engine, [
        {"filename": "s1.wav", "path": "/tmp/s1.wav", "energy": "mid"},
    ])
    playlist = playlist_by_energy(["high"], limit_per_step=5)
    assert playlist == []


def test_playlist_by_energy_instrument_filter(orm_engine) -> None:
    """instrument filter should restrict which samples appear in the playlist."""
    _seed(orm_engine, [
        {"filename": "k1.wav", "path": "/tmp/k1.wav", "energy": "high", "instrument": "kick"},
        {"filename": "p1.wav", "path": "/tmp/p1.wav", "energy": "high", "instrument": "pad"},
    ])
    playlist = playlist_by_energy(["high"], instrument="kick", limit_per_step=5)
    assert len(playlist) == 1
    assert playlist[0].instrument == "kick"


# ── gap_analysis ──────────────────────────────────────────────────────────────


def test_gap_analysis_identifies_missing(orm_engine) -> None:
    """gap_analysis should show negative surplus for instruments not in library."""
    _seed(orm_engine, [
        {"filename": "k1.wav", "path": "/tmp/k1.wav", "instrument": "kick"},
        {"filename": "k2.wav", "path": "/tmp/k2.wav", "instrument": "kick"},
    ])
    gaps = gap_analysis({"kick": 5, "snare": 8})
    assert gaps["kick"]["actual"] == 2
    assert gaps["kick"]["surplus"] == -3   # 2 - 5
    assert gaps["snare"]["actual"] == 0
    assert gaps["snare"]["surplus"] == -8  # 0 - 8


def test_gap_analysis_surplus_is_positive_when_over_target(orm_engine) -> None:
    """gap_analysis should show positive surplus when library exceeds target."""
    _seed(orm_engine, [
        {"filename": "h1.wav", "path": "/tmp/h1.wav", "instrument": "hihat"},
        {"filename": "h2.wav", "path": "/tmp/h2.wav", "instrument": "hihat"},
        {"filename": "h3.wav", "path": "/tmp/h3.wav", "instrument": "hihat"},
    ])
    gaps = gap_analysis({"hihat": 2})
    assert gaps["hihat"]["surplus"] == 1  # 3 - 2


# ── CuratorAgent — TestModel ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_curator_agent_with_mock_model(orm_engine) -> None:
    """CuratorAgent must return a CurationResult without hitting a real API."""
    from pydantic_ai.models.test import TestModel

    orm_module._engine = orm_engine

    from samplemind.agent.curator import CurationResult, CuratorAgent

    agent = CuratorAgent(model_id=TestModel())
    result = await agent.curate("Find gaps in my hip-hop library")

    assert isinstance(result, CurationResult)
    # TestModel fills all required fields with minimal values — just check types
    assert isinstance(result.recommendations, list)
    assert isinstance(result.suggested_tags, dict)
    assert isinstance(result.gap_analysis, dict)
    # energy_arc is optional — may be None or a list
    assert result.energy_arc is None or isinstance(result.energy_arc, list)
