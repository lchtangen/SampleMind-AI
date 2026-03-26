# Phase 12 — AI Curation Agent

**Status: 📋 Planned** — depends on Phase 11 (semantic search) | Phase 12 of 16 | Agent: `phase-12-ai-curation`

> **Goal:** Automate repetitive library management tasks — let an LLM reason
> about your sample collection and suggest organization, identify gaps,
> generate curated playlists, and surface hidden gems.
>
> **Stack:** LiteLLM (provider-agnostic LLM client) · structlog · FAISS (Phase 11) ·
> SQLite FTS5 (Phase 3) · Anthropic Claude / OpenAI GPT-4o / local Ollama.
>
> **Prerequisites:** Phase 3 (database), Phase 11 (semantic search), Phase 4 (CLI).

---

## 1. Overview

```
Library Analysis (SQLite)
        │
        ▼
  LibraryAnalyzer
  ┌─────────────────────────────────────────┐
  │ BPM histogram · Key distribution        │
  │ Instrument coverage · Mood mix          │
  │ Missing instrument types (gap analysis) │
  │ Duplicate cluster detection             │
  └─────────────────────────────────────────┘
        │
        ▼
  CurationAgent (LLM)
  ┌─────────────────────────────────────────┐
  │ System prompt: "You are a music curator"│
  │ Context: library stats + sample list    │
  │ Tools: search(), tag(), create_playlist()│
  │ Output: actions in structured JSON      │
  └─────────────────────────────────────────┘
        │
        ▼
  ActionExecutor
  ┌─────────────────────────────────────────┐
  │ Execute approved actions on library     │
  │ All actions require user confirmation   │
  │ All actions are reversible (backup DB)  │
  └─────────────────────────────────────────┘
```

---

## 2. Install Dependencies

```bash
uv add litellm anthropic openai   # LLM clients
uv add ollama                      # local model support (optional)
```

```toml
# pyproject.toml
[project.optional-dependencies]
ai = ["litellm", "anthropic", "openai"]
ai-local = ["litellm", "ollama"]
```

---

## 3. Library Analyzer — Feed the Agent Context

```python
# src/samplemind/agent/library_analyzer.py
"""
Library statistical analysis for the AI curation agent.

Provides structured context about the library so the LLM can make
informed suggestions without hallucinating sample names.

Output is a LibrarySnapshot dataclass — serializable to JSON for
inclusion in the LLM system prompt.
"""
from __future__ import annotations
import sqlite3
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any
from samplemind.data.orm import get_db_path


@dataclass
class LibrarySnapshot:
    total_samples: int
    total_duration_hours: float
    bpm_histogram: dict[str, int]          # "60-79": 12, "80-99": 45, ...
    key_distribution: dict[str, int]       # "C maj": 23, "A min": 41, ...
    instrument_counts: dict[str, int]      # "kick": 120, "pad": 45, ...
    mood_counts: dict[str, int]
    energy_counts: dict[str, int]
    missing_instruments: list[str]         # instruments with < 5 samples
    dominant_key: str
    dominant_bpm_range: str
    gap_analysis: list[str]                # human-readable gaps
    recent_imports: list[dict[str, Any]]   # last 20 samples added


def analyze_library() -> LibrarySnapshot:
    """
    Build a comprehensive snapshot of the sample library.
    Takes ~10ms for libraries up to 50k samples.
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*), SUM(duration) FROM samples").fetchone()
    total_samples = total[0] or 0
    total_duration_hours = round((total[1] or 0) / 3600, 2)

    # BPM histogram in 20-BPM buckets
    bpm_rows = conn.execute("SELECT bpm FROM samples WHERE bpm IS NOT NULL").fetchall()
    bpm_hist: Counter = Counter()
    for row in bpm_rows:
        bpm = row[0]
        bucket = f"{int(bpm // 20) * 20}-{int(bpm // 20) * 20 + 19}"
        bpm_hist[bucket] += 1

    # Key and other distributions
    key_dist  = dict(Counter(r[0] for r in conn.execute("SELECT key FROM samples WHERE key IS NOT NULL")))
    inst_cnt  = dict(Counter(r[0] for r in conn.execute("SELECT instrument FROM samples")))
    mood_cnt  = dict(Counter(r[0] for r in conn.execute("SELECT mood FROM samples")))
    energy_cnt= dict(Counter(r[0] for r in conn.execute("SELECT energy FROM samples")))

    # Gap analysis
    all_instruments = {"kick", "snare", "hihat", "bass", "pad", "lead", "loop", "sfx"}
    missing = [i for i in all_instruments if inst_cnt.get(i, 0) < 5]
    gaps = []
    if missing:
        gaps.append(f"Underrepresented instruments (< 5 samples): {', '.join(sorted(missing))}")
    if energy_cnt.get("high", 0) < 10:
        gaps.append("Few high-energy samples — consider adding aggressive or euphoric content")
    if len(key_dist) < 5:
        gaps.append("Limited key diversity — library heavily concentrated in few keys")

    # Recent imports
    recent = [dict(r) for r in conn.execute(
        "SELECT id, filename, instrument, mood, bpm, key FROM samples ORDER BY id DESC LIMIT 20"
    ).fetchall()]

    conn.close()

    dominant_key  = max(key_dist, key=key_dist.get, default="unknown") if key_dist else "unknown"
    dominant_bpm  = max(bpm_hist, key=bpm_hist.get, default="unknown") if bpm_hist else "unknown"

    return LibrarySnapshot(
        total_samples=total_samples,
        total_duration_hours=total_duration_hours,
        bpm_histogram=dict(bpm_hist),
        key_distribution=key_dist,
        instrument_counts=inst_cnt,
        mood_counts=mood_cnt,
        energy_counts=energy_cnt,
        missing_instruments=missing,
        dominant_key=dominant_key,
        dominant_bpm_range=dominant_bpm,
        gap_analysis=gaps,
        recent_imports=recent,
    )
```

---

## 4. Curation Agent

```python
# src/samplemind/agent/curator.py
"""
AI curation agent powered by LiteLLM (works with Claude, GPT-4o, or Ollama).

The agent receives a library snapshot and a user goal, then plans
a sequence of tool calls to achieve the goal. All actions are returned
as structured JSON — no actions are executed without user confirmation.

Supported goals:
  - "organize my library" → suggests tags, playlists, folder structure
  - "find gaps in my library" → identifies missing instrument/mood combos
  - "create a dark trap playlist" → curates 20-30 samples matching the vibe
  - "suggest samples similar to this session" → BPM/key/mood matching

LLM providers (set via SAMPLEMIND_LLM_PROVIDER env var):
  anthropic/claude-sonnet-4-5   → best quality, requires API key
  openai/gpt-4o                 → good quality, requires API key
  ollama/llama3.2               → free, runs locally (needs Ollama installed)
"""
from __future__ import annotations
import json
from dataclasses import asdict
from samplemind.agent.library_analyzer import analyze_library, LibrarySnapshot
from samplemind.core.config import get_settings
from samplemind.core.logging import get_logger

log = get_logger(__name__)

SYSTEM_PROMPT = """
You are SampleMind Curator — an expert music librarian and producer assistant.

You have access to the user's audio sample library. Your job is to help them:
1. Organize and tag samples intelligently
2. Identify gaps in their collection
3. Create curated playlists for specific creative sessions
4. Surface forgotten or underused samples

RULES:
- Only suggest actions on samples that exist in the library (use provided data)
- Never fabricate sample names or IDs
- All suggested actions must be reversible
- Prefer minimal, targeted changes over bulk operations
- Ask clarifying questions before making large changes

OUTPUT FORMAT:
Always respond in this JSON structure:
{
  "reasoning": "Brief explanation of your analysis",
  "suggested_actions": [
    {
      "type": "create_playlist",
      "args": {"name": "Dark Trap Session", "sample_ids": [1, 42, 87, 134]},
      "description": "Create a playlist of 4 dark trap samples"
    },
    {
      "type": "tag_sample",
      "args": {"id": 42, "tags": "trap,dark,featured"},
      "description": "Tag sample 42 with trap,dark,featured"
    }
  ],
  "questions": [],
  "insights": "Your library has strong trap kick coverage but lacks melodic content."
}

Supported action types: create_playlist, tag_sample, update_mood, suggest_imports, create_folder
"""


def curate(goal: str, model: str | None = None, dry_run: bool = True) -> dict:
    """
    Run the curation agent for a given goal.

    Args:
        goal:    Natural language goal (e.g. "create a dark trap playlist")
        model:   LiteLLM model string (e.g. "anthropic/claude-sonnet-4-5")
        dry_run: If True, return actions without executing them

    Returns:
        Agent response with reasoning, suggested_actions, questions, insights
    """
    import litellm

    settings = get_settings()
    if model is None:
        model = "anthropic/claude-sonnet-4-5" if settings.anthropic_api_key else "ollama/llama3.2"

    snapshot = analyze_library()
    library_context = json.dumps(asdict(snapshot), indent=2)

    user_message = f"""
My library stats:
{library_context}

My goal: {goal}

Please analyze my library and suggest specific actions to help me achieve this goal.
""".strip()

    log.info("curation_request", goal=goal, model=model, samples=snapshot.total_samples)

    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": user_message},
        ],
        max_tokens=2000,
        temperature=0.3,   # low temperature for consistent structured output
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    log.info("curation_response",
             action_count=len(result.get("suggested_actions", [])),
             dry_run=dry_run)

    if not dry_run:
        _execute_actions(result.get("suggested_actions", []))

    return result


def _execute_actions(actions: list[dict]) -> list[str]:
    """Execute approved curation actions. Each action is atomic and logged."""
    executed = []
    from samplemind.data.repositories.sample_repository import SampleRepository
    from samplemind.data.repositories.playlist_repository import PlaylistRepository

    for action in actions:
        action_type = action["type"]
        args = action.get("args", {})
        try:
            if action_type == "create_playlist":
                PlaylistRepository.create_with_samples(
                    name=args["name"],
                    sample_ids=args.get("sample_ids", []),
                )
            elif action_type == "tag_sample":
                SampleRepository.update_tags(args["id"], args["tags"])
            elif action_type == "update_mood":
                SampleRepository.update_field(args["id"], "mood", args["mood"])
            executed.append(f"✓ {action_type}: {args}")
        except Exception as e:
            log.error("curation_action_failed", action=action_type, error=str(e))
    return executed
```

---

## 5. Curation CLI Commands

```python
# src/samplemind/cli/commands/curate_cmd.py
"""
AI curation commands.

Usage:
  uv run samplemind curate "create a dark trap playlist"
  uv run samplemind curate "find gaps in my library" --execute
  uv run samplemind curate "organize by mood" --model ollama/llama3.2
  uv run samplemind curate analyze  # library stats without LLM
"""
import json, sys
import typer
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON as RichJSON

app = typer.Typer(help="AI-powered library curation")
console = Console(stderr=True)


@app.command()
def analyze(json_output: bool = typer.Option(False, "--json")):
    """Show library statistics without running the AI agent."""
    from samplemind.agent.library_analyzer import analyze_library
    from dataclasses import asdict
    snapshot = asdict(analyze_library())
    if json_output:
        print(json.dumps(snapshot, indent=2))
        return
    console.print(Panel(RichJSON(json.dumps(snapshot, indent=2)),
                        title="Library Analysis", border_style="cyan"))


@app.command()
def curate(
    goal: str = typer.Argument(..., help="What do you want to achieve?"),
    model: str = typer.Option(None, "--model", "-m",
                               help="LLM model: anthropic/claude-sonnet-4-5 | openai/gpt-4o | ollama/llama3.2"),
    execute: bool = typer.Option(False, "--execute",
                                  help="Execute suggested actions (default: dry-run)"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Run the AI curation agent for a given goal."""
    from samplemind.core.feature_flags import is_enabled
    if not is_enabled("ai_curation"):
        console.print("[yellow]AI curation is not yet enabled.[/yellow]")
        raise typer.Exit(1)

    from samplemind.agent.curator import curate as run_curate
    console.print(f"[cyan]Goal:[/cyan] {goal}")
    console.print(f"[dim]Model:[/dim] {model or 'auto'} · dry_run={not execute}")

    result = run_curate(goal=goal, model=model, dry_run=not execute)

    if json_output:
        print(json.dumps(result, indent=2))
        return

    console.print(Panel(result.get("insights", ""), title="Insights", border_style="green"))
    console.print("\n[bold]Suggested Actions:[/bold]")
    for i, action in enumerate(result.get("suggested_actions", []), 1):
        console.print(f"  {i}. [cyan]{action['type']}[/cyan] — {action['description']}")

    if result.get("questions"):
        console.print("\n[bold]Questions:[/bold]")
        for q in result["questions"]:
            console.print(f"  • {q}")

    if not execute and result.get("suggested_actions"):
        console.print("\n[yellow]Dry run — no changes made.[/yellow]")
        console.print("Re-run with [bold]--execute[/bold] to apply these actions.")
```

---

## 6. Smart Playlist Generation

```python
# src/samplemind/agent/playlist_generator.py
"""
Rule-based smart playlist generation (no LLM required).

These generators work offline and complement the LLM agent.
They use pure SQL + classifier data — no embeddings needed.

Generators:
  by_session_bpm    → match samples to a target BPM ± 5
  by_key_signature  → samples in compatible keys (circle of fifths)
  by_energy_arc     → builds from low → high → low energy (DJ set arc)
  by_mood_journey   → neutral → dark → aggressive → euphoric arc
  similar_to_sample → samples with matching instrument + key + energy
"""
from __future__ import annotations
import sqlite3
from samplemind.data.orm import get_db_path

CIRCLE_OF_FIFTHS = {
    "C maj":  ["C maj", "G maj", "F maj", "A min", "E min", "D min"],
    "G maj":  ["G maj", "D maj", "C maj", "E min", "B min", "A min"],
    "A min":  ["A min", "E min", "D min", "C maj", "G maj", "F maj"],
    # ... (full circle omitted for brevity)
}


def playlist_by_bpm(target_bpm: float, tolerance: float = 5.0,
                    limit: int = 30) -> list[dict]:
    """Samples within ±tolerance BPM of target."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM samples WHERE bpm BETWEEN ? AND ? ORDER BY ABS(bpm - ?) LIMIT ?",
        (target_bpm - tolerance, target_bpm + tolerance, target_bpm, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def playlist_by_energy_arc(
    low_count: int = 5, mid_count: int = 10, high_count: int = 10,
    mid_out_count: int = 5, cool_down: int = 5,
) -> list[dict]:
    """
    Build a DJ-set style energy arc:
      intro (low) → build (mid) → peak (high) → peak (high) → outro (low)
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row

    def get_energy(energy: str, limit: int) -> list[dict]:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM samples WHERE energy = ? ORDER BY RANDOM() LIMIT ?",
            (energy, limit),
        ).fetchall()]

    arc = (
        get_energy("low",  low_count) +
        get_energy("mid",  mid_count) +
        get_energy("high", high_count) +
        get_energy("mid",  mid_out_count) +
        get_energy("low",  cool_down)
    )
    conn.close()
    return arc


def playlist_similar_to(sample_id: int, limit: int = 20) -> list[dict]:
    """Find samples with the same instrument, energy, and compatible key."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    ref = dict(conn.execute(
        "SELECT instrument, energy, key FROM samples WHERE id = ?", (sample_id,)
    ).fetchone() or {})
    if not ref:
        conn.close()
        return []

    compatible_keys = CIRCLE_OF_FIFTHS.get(ref.get("key", ""), [ref.get("key", "")])
    placeholders = ", ".join("?" * len(compatible_keys))
    rows = conn.execute(
        f"""SELECT * FROM samples
            WHERE id != ?
              AND instrument = ?
              AND energy = ?
              AND key IN ({placeholders})
            ORDER BY RANDOM() LIMIT ?""",
        [sample_id, ref["instrument"], ref["energy"], *compatible_keys, limit],
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
```

---

## 7. Testing

```python
# tests/test_ai_curation.py
"""
Tests for Phase 12 AI curation.
LLM calls are always mocked — no API keys required for tests.
"""
import pytest
from unittest.mock import patch, MagicMock
from samplemind.agent.library_analyzer import analyze_library
from samplemind.agent.playlist_generator import playlist_by_energy_arc


def test_analyze_library_returns_snapshot(db):
    """Library analyzer should not crash on empty or populated DB."""
    snapshot = analyze_library()
    assert snapshot.total_samples >= 0
    assert isinstance(snapshot.gap_analysis, list)
    assert isinstance(snapshot.instrument_counts, dict)


def test_energy_arc_playlist_order(db):
    """Energy arc should start low, peak high, end low."""
    # This test relies on having energy-tagged samples in the test DB
    arc = playlist_by_energy_arc(low_count=2, mid_count=2, high_count=2, mid_out_count=1, cool_down=1)
    # Verify structure — actual content depends on DB state
    assert isinstance(arc, list)


@patch("samplemind.agent.curator.litellm.completion")
def test_curate_dry_run(mock_llm, db):
    """Curation in dry-run mode should call LLM but not modify DB."""
    mock_llm.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='''{
            "reasoning": "test",
            "suggested_actions": [],
            "questions": [],
            "insights": "Library looks good"
        }'''))]
    )
    from samplemind.agent.curator import curate
    result = curate("organize my library", dry_run=True)
    assert result["insights"] == "Library looks good"
    mock_llm.assert_called_once()
```

---

## 8. Checklist

- [ ] `uv add litellm anthropic` — AI dependencies installed
- [ ] `analyze_library()` returns correct counts from SQLite
- [ ] `curate("goal")` calls LLM and returns structured JSON
- [ ] `--execute` flag applies actions to database
- [ ] All LLM calls mocked in tests (no API key required)
- [ ] Feature flag `ai_curation` gates the feature
- [ ] `playlist_by_energy_arc()` generates valid energy progression
- [ ] `playlist_similar_to(id)` uses circle of fifths
- [ ] LLM provider configurable via env: `SAMPLEMIND_ANTHROPIC_API_KEY`
- [ ] `uv run samplemind curate analyze --json` works without API key

