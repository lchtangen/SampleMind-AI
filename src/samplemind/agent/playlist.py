"""Smart playlist generation with energy arcs and gap analysis.

Phase 12 — AI Curation.
playlist_by_energy() builds a track sequence that follows a specified energy
arc (e.g., ["low", "mid", "high", "high", "mid"]) by selecting and ordering
samples from the library. gap_analysis() identifies missing instrument types
by comparing library contents to a target profile.
"""

from __future__ import annotations

from collections import defaultdict

from samplemind.core.models.sample import Sample
from samplemind.data.repositories.sample_repository import SampleRepository


def playlist_by_energy(
    arc: list[str],
    limit_per_step: int = 5,
    mood: str | None = None,
    instrument: str | None = None,
) -> list[Sample]:
    """Build an ordered track list following an energy arc.

    For each step in *arc*, up to *limit_per_step* samples are fetched from
    the library matching that energy level (plus optional mood/instrument
    filters). One sample per step is selected (round-robin from the pool for
    that energy level), producing a playlist whose length equals len(arc).

    Args:
        arc: Ordered list of energy levels, e.g. ["low", "mid", "high", "high"].
        limit_per_step: Max candidates to fetch per unique energy level.
        mood: Optional mood filter applied to all steps.
        instrument: Optional instrument filter applied to all steps.

    Returns:
        Ordered list of Sample objects. Steps with no matching samples are
        silently skipped (result may be shorter than arc).
    """
    # Pre-fetch candidates for each unique energy level in the arc
    pools: dict[str, list[Sample]] = defaultdict(list)
    for energy_level in set(arc):
        candidates = SampleRepository.search(
            energy=energy_level,
            mood=mood,
            instrument=instrument,
            limit=limit_per_step,
        )
        pools[energy_level] = list(candidates)

    # Rotate through each pool to pick one sample per arc step
    pool_indices: dict[str, int] = defaultdict(int)
    playlist: list[Sample] = []

    for energy_level in arc:
        pool = pools.get(energy_level, [])
        if not pool:
            continue
        idx = pool_indices[energy_level] % len(pool)
        playlist.append(pool[idx])
        pool_indices[energy_level] += 1

    return playlist


def gap_analysis(target_profile: dict[str, int]) -> dict[str, dict]:
    """Compare library contents to a target instrument profile.

    Args:
        target_profile: Dict mapping instrument name to desired count,
                        e.g. {"kick": 10, "snare": 8, "hihat": 12}.

    Returns:
        Dict mapping instrument name to analysis dict:
        {
            "target": int,   # desired count from target_profile
            "actual": int,   # current count in library
            "surplus": int,  # actual - target (negative = gap)
        }
    """
    all_samples = SampleRepository.get_all()

    # Count samples per instrument in the library
    actual: dict[str, int] = defaultdict(int)
    for s in all_samples:
        if s.instrument:
            actual[s.instrument] += 1

    result: dict[str, dict] = {}
    for instrument, desired in target_profile.items():
        have = actual.get(instrument, 0)
        result[instrument] = {
            "target": desired,
            "actual": have,
            "surplus": have - desired,
        }

    return result
