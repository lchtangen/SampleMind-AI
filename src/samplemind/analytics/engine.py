"""Analytics query engine: aggregations over SampleRepository.

Phase 14 — Analytics.
get_summary() returns counts by energy/mood/instrument. get_bpm_buckets()
returns histogram data for BPM distribution. get_key_counts() returns
a frequency map of musical keys. get_growth_timeline() returns sample
import counts bucketed by day/week/month.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from samplemind.data.repositories.sample_repository import SampleRepository


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class LibrarySummary:
    """High-level statistics for the entire sample library."""

    total: int
    by_energy: dict[str, int] = field(default_factory=dict)
    by_mood: dict[str, int] = field(default_factory=dict)
    by_instrument: dict[str, int] = field(default_factory=dict)
    bpm_min: float | None = None
    bpm_max: float | None = None
    bpm_mean: float | None = None


@dataclass
class BpmBucket:
    """One histogram bucket for BPM distribution."""

    label: str      # e.g. "80–90"
    count: int
    bpm_min: float  # inclusive lower bound
    bpm_max: float  # exclusive upper bound


# ── Query functions ───────────────────────────────────────────────────────────


def get_summary() -> LibrarySummary:
    """Return aggregate statistics for the entire sample library.

    Makes one call to SampleRepository.get_all() and aggregates in Python —
    avoids N+1 queries and keeps the logic testable without raw SQL.
    """
    samples = SampleRepository.get_all()

    if not samples:
        return LibrarySummary(total=0)

    energy_counter: Counter[str] = Counter()
    mood_counter: Counter[str] = Counter()
    instrument_counter: Counter[str] = Counter()
    bpms: list[float] = []

    for s in samples:
        if s.energy:
            energy_counter[s.energy] += 1
        if s.mood:
            mood_counter[s.mood] += 1
        if s.instrument:
            instrument_counter[s.instrument] += 1
        if s.bpm is not None:
            bpms.append(s.bpm)

    return LibrarySummary(
        total=len(samples),
        by_energy=dict(energy_counter),
        by_mood=dict(mood_counter),
        by_instrument=dict(instrument_counter),
        bpm_min=min(bpms) if bpms else None,
        bpm_max=max(bpms) if bpms else None,
        bpm_mean=sum(bpms) / len(bpms) if bpms else None,
    )


def get_bpm_buckets(buckets: int = 10) -> list[BpmBucket]:
    """Return BPM distribution as *buckets* equal-width histogram bins.

    Args:
        buckets: Number of histogram bins (default 10).

    Returns:
        Ordered list of BpmBucket. Empty list when no samples have BPM data.
    """
    if buckets < 1:
        raise ValueError(f"buckets must be >= 1, got {buckets}")

    samples = SampleRepository.get_all()
    bpms = [s.bpm for s in samples if s.bpm is not None]

    if not bpms:
        return []

    bpm_min = math.floor(min(bpms) / 10) * 10  # round down to nearest 10
    bpm_max = math.ceil(max(bpms) / 10) * 10   # round up to nearest 10

    if bpm_min == bpm_max:
        # All samples have the same BPM — return a single bucket
        label = f"{bpm_min}–{bpm_max + 10}"
        return [BpmBucket(label=label, count=len(bpms), bpm_min=float(bpm_min), bpm_max=float(bpm_max + 10))]

    step = (bpm_max - bpm_min) / buckets

    result: list[BpmBucket] = []
    for i in range(buckets):
        lo = bpm_min + i * step
        hi = bpm_min + (i + 1) * step
        count = sum(1 for b in bpms if lo <= b < hi)
        # Last bucket is inclusive on right edge to capture exactly bpm_max
        if i == buckets - 1:
            count = sum(1 for b in bpms if lo <= b <= hi)
        label = f"{lo:.0f}–{hi:.0f}"
        result.append(BpmBucket(label=label, count=count, bpm_min=lo, bpm_max=hi))

    return result


def get_key_counts() -> dict[str, int]:
    """Return a frequency map of musical keys in the library.

    Returns:
        Dict mapping key string (e.g. "C maj") to sample count, sorted
        by count descending. Empty dict when no samples have key data.
    """
    samples = SampleRepository.get_all()
    counter: Counter[str] = Counter(s.key for s in samples if s.key)
    return dict(counter.most_common())


def get_growth_timeline(
    bucket: Literal["day", "week", "month"] = "week",
) -> list[dict]:
    """Return cumulative library growth bucketed by time period.

    Args:
        bucket: Time granularity — "day", "week", or "month".

    Returns:
        List of dicts with keys "period" (ISO 8601 date string) and "count"
        (cumulative total). Ordered chronologically.
        Empty list when no samples are in the library.
    """
    samples = SampleRepository.get_all()
    if not samples:
        return []

    # Filter samples that have imported_at; strip timezone for bucketing
    dated = [
        s for s in samples
        if s.imported_at is not None
    ]
    if not dated:
        return []

    def _bucket_key(dt: datetime) -> str:
        if dt.tzinfo is None:
            aware = dt.replace(tzinfo=UTC)
        else:
            aware = dt.astimezone(UTC)
        if bucket == "day":
            return aware.strftime("%Y-%m-%d")
        if bucket == "week":
            # ISO week: year + week number
            return aware.strftime("%Y-W%W")
        # month
        return aware.strftime("%Y-%m")

    # Count imports per bucket
    per_bucket: Counter[str] = Counter(_bucket_key(s.imported_at) for s in dated)  # type: ignore[arg-type]

    # Build cumulative timeline
    sorted_periods = sorted(per_bucket.keys())
    timeline: list[dict] = []
    cumulative = 0
    for period in sorted_periods:
        cumulative += per_bucket[period]
        timeline.append({"period": period, "count": cumulative})

    return timeline
