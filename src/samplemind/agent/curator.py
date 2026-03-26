"""pydantic-ai agent for library analysis and sample curation recommendations.

Phase 12 — AI Curation.
CuratorAgent wraps a pydantic-ai Agent with three tools:
  _tool_summary()         -- LibrarySummary as text
  _tool_search(...)       -- search the sample library
  _tool_gap_analysis(...) -- compare library to a target profile

Returns structured CurationResult with recommendations, suggested tags,
gap analysis, and an optional energy arc.

Default model: claude-haiku-4-5-20251001 (fast, cheap).
Tests: pass pydantic_ai.models.test.TestModel to avoid real API calls.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from pydantic import BaseModel
from pydantic_ai import Agent

from samplemind.core.models.sample import Sample


# ── Output schema ─────────────────────────────────────────────────────────────


class CurationResult(BaseModel):
    """Structured output from CuratorAgent.run()."""

    recommendations: list[str] = field(default_factory=list)
    suggested_tags: dict[str, list[str]] = field(default_factory=dict)
    gap_analysis: dict[str, dict] = field(default_factory=dict)
    energy_arc: list[str] | None = None


# ── Curator agent ──────────────────────────────────────────────────────────────


class CuratorAgent:
    """AI-powered library curator.

    Usage::

        agent = CuratorAgent()
        result = asyncio.run(agent.curate("Find gaps in my hip-hop library"))

    Args:
        model_id: pydantic-ai model identifier or model instance.
                  Pass ``pydantic_ai.models.test.TestModel()`` in tests.
    """

    _SYSTEM_PROMPT = (
        "You are an expert music producer and sample library curator. "
        "Analyse the user's sample library using the available tools and return "
        "structured curation recommendations, suggested tags, gap analysis, and "
        "an optional energy arc (list of 'low'/'mid'/'high' values)."
    )

    def __init__(self, model_id: str | object = "claude-haiku-4-5-20251001") -> None:
        self._agent: Agent[None, CurationResult] = Agent(
            model_id,  # type: ignore[arg-type]
            output_type=CurationResult,
            system_prompt=self._SYSTEM_PROMPT,
        )
        self._register_tools()

    def _register_tools(self) -> None:
        """Register tools on the agent (called once at init)."""

        @self._agent.tool_plain
        def get_library_summary() -> str:
            """Return a text summary of the sample library (counts by energy, mood, instrument)."""
            from samplemind.analytics.engine import get_summary  # noqa: PLC0415

            s = get_summary()
            return (
                f"Total samples: {s.total}\n"
                f"By energy: {s.by_energy}\n"
                f"By mood: {s.by_mood}\n"
                f"By instrument: {s.by_instrument}\n"
                f"BPM range: {s.bpm_min}–{s.bpm_max} (mean {s.bpm_mean})"
            )

        @self._agent.tool_plain
        def search_samples(
            energy: str | None = None,
            mood: str | None = None,
            instrument: str | None = None,
            limit: int = 10,
        ) -> list[str]:
            """Search the library. Returns list of filenames matching the filters."""
            from samplemind.data.repositories.sample_repository import SampleRepository  # noqa: PLC0415

            samples = SampleRepository.search(
                energy=energy,
                mood=mood,
                instrument=instrument,
                limit=limit,
            )
            return [s.filename for s in samples]

        @self._agent.tool_plain
        def analyze_gaps(target_kicks: int = 10, target_snares: int = 8, target_hihats: int = 12) -> dict:
            """Analyse gaps between library and a target instrument profile."""
            from samplemind.agent.playlist import gap_analysis  # noqa: PLC0415

            return gap_analysis({"kick": target_kicks, "snare": target_snares, "hihat": target_hihats})

    async def curate(self, prompt: str = "Analyse my library and suggest improvements.") -> CurationResult:
        """Run curation against the library.

        Args:
            prompt: Natural language curation goal.

        Returns:
            CurationResult with recommendations, tags, gaps, and optional arc.
        """
        result = await self._agent.run(prompt)
        return result.output

    def curate_sync(self, prompt: str = "Analyse my library and suggest improvements.") -> CurationResult:
        """Synchronous wrapper around curate() for CLI use."""
        return asyncio.run(self.curate(prompt))
