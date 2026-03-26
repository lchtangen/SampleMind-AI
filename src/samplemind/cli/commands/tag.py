"""Tag samples with genre, mood, energy, and custom tags."""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import sys

from samplemind.core.models.sample import Sample, SampleUpdate
from samplemind.data.orm import init_orm
from samplemind.data.repositories.sample_repository import SampleRepository

VALID_ENERGY: frozenset[str] = frozenset({"low", "mid", "high"})


def tag_samples(
    name: str,
    genre: str | None = None,
    mood: str | None = None,
    energy: str | None = None,
    tags: str | None = None,
) -> None:
    """Manually tag a sample in the library."""
    init_orm()

    if energy and energy not in VALID_ENERGY:
        print(
            f"❌ Invalid energy '{energy}'. Choose from: low, mid, high",
            file=sys.stderr,
        )
        sys.exit(1)

    sample = SampleRepository.get_by_name(name)
    if not sample:
        print(f"❌ No sample matching '{name}' found in library.", file=sys.stderr)
        print("   Run `samplemind list` to see what's imported.", file=sys.stderr)
        sys.exit(1)

    update = SampleUpdate(genre=genre, mood=mood, energy=energy, tags=tags)
    updated = SampleRepository.tag(sample.path, update)

    if updated:
        print(f"🏷️  Tagged: {sample.filename}", file=sys.stderr)
        if genre:
            print(f"   Genre:  {genre}", file=sys.stderr)
        if mood:
            print(f"   Mood:   {mood}", file=sys.stderr)
        if energy:
            print(f"   Energy: {energy}", file=sys.stderr)
        if tags:
            print(f"   Tags:   {tags}", file=sys.stderr)
    else:
        print("⚠️  Nothing was updated (no fields provided).", file=sys.stderr)


def auto_tag_samples(
    name: str | None,
    model_path: str | None,
    workers: int,
    download_model: bool,
    json_output: bool,
) -> None:
    """Auto-tag samples using LocalAIEngine with rule-based fallback.

    When name is None, tags the entire library (--auto-all mode).
    Uses the locally loaded GGUF model when available; silently falls back
    to deterministic rule-based tags derived from stored audio metadata.
    """
    from samplemind.ai.local_models import LocalAIEngine

    init_orm()

    engine = LocalAIEngine(model_path=Path(model_path) if model_path else None)

    if download_model:
        dest = LocalAIEngine.download_model()
        if not json_output:
            print(f"Downloaded model to {dest}", file=sys.stderr)
        engine.load_llm(dest)
    else:
        # Silently load if the model already exists; use rule-based if not.
        try:
            engine.load_llm()
            if not json_output:
                print(f"Loaded model from {engine._model_path}", file=sys.stderr)
        except (FileNotFoundError, RuntimeError):
            if not json_output:
                print("Model not found — using rule-based tags.", file=sys.stderr)

    # ── Gather samples ────────────────────────────────────────────────────────
    if name:
        sample = SampleRepository.get_by_name(name)
        if not sample:
            if json_output:
                sys.stdout.write(json.dumps({"error": f"Sample not found: {name}"}) + "\n")
            else:
                print(f"No sample matching '{name}' found.", file=sys.stderr)
            sys.exit(1)
        samples = [sample]
    else:
        samples = SampleRepository.search()

    # ── Process (optionally parallel for rule-based; serialised for LLM) ─────
    effective_workers = 1 if engine.is_loaded() else workers

    def _process(s: Sample) -> dict[str, object]:
        try:
            features: dict[str, object] = {
                "bpm": s.bpm,
                "key": s.key,
                "instrument": s.instrument,
                "energy": s.energy,
                "mood": s.mood,
                "rms": s.rms,
            }
            tags = engine.generate_tags(features)
            SampleRepository.tag(s.path, SampleUpdate(tags=",".join(tags)))
            return {"path": s.path, "tags": tags, "ok": True}
        except Exception as exc:
            return {"path": s.path, "error": str(exc), "ok": False}

    with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as pool:
        results: list[dict[str, object]] = list(pool.map(_process, samples))

    if json_output:
        sys.stdout.write(json.dumps({"results": results, "total": len(results)}) + "\n")
    else:
        ok_count = sum(1 for r in results if r["ok"])
        print(f"Auto-tagged {ok_count}/{len(results)} sample(s).", file=sys.stderr)
