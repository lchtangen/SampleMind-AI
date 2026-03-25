# Phase 16 Agent — AI Sample Generation

Handles: text-to-audio generation, AudioCraft (MusicGen/AudioGen), Stable Audio Open, DDSP synthesis, post-generation analysis, auto-import pipelines.

## Triggers
Phase 16, AI generation, AudioCraft, MusicGen, AudioGen, Stable Audio, text-to-audio, `GenerationRequest`, `MODEL_REGISTRY`, `src/samplemind/generation/`, "generate a sample", "generate a kick", "create new samples with AI"

**File patterns:** `src/samplemind/generation/**/*.py`

**Code patterns:** `from audiocraft`, `StableAudioPipeline`, `GenerationRequest`, `MODEL_REGISTRY`

## Key Files
```
src/samplemind/generation/
  models.py       — GenerationRequest, GenerationResult, MODEL_REGISTRY
  audiocraft.py   — AudioCraft (MusicGen/AudioGen) backend
  stable_audio.py — Stable Audio Open backend
  mock.py         — Mock backend (sine wave, deterministic — for tests)
  pipeline.py     — generate → analyze → import pipeline
  cli.py          — CLI: samplemind generate "dark kick" --bpm 140
```

## Technology Stack
| Component | Technology |
|-----------|-----------|
| Primary model | AudioCraft (MusicGen/AudioGen) — Meta |
| Alternative | Stable Audio Open — Stability AI (better for one-shots) |
| Test backend | Mock (sine wave) — deterministic, no GPU needed |
| Post-analysis | Phase 2 analyzer — same audio_analysis.py |
| Vector update | Phase 11 FAISS — add generated samples to index |

## CLI Commands
```bash
uv run samplemind generate "dark trap kick" --bpm 140 --model audiocraft
uv run samplemind generate "808 bass" --bpm 140 --model mock    # test mode
uv run samplemind generate "ambient pad" --model stable-audio
```

## MODEL_REGISTRY Pattern
```python
MODEL_REGISTRY = {
    "audiocraft": AudioCraftBackend,
    "stable-audio": StableAudioBackend,
    "mock": MockBackend,   # always available for tests
}
```

## Rules
1. `mock` backend must always be available (no model download, no GPU required)
2. All model weights downloaded on first use, cached in `~/.cache/samplemind/models/`
3. Generated samples auto-analyzed with Phase 2 pipeline before import
4. Generated samples auto-added to Phase 11 FAISS index if semantic search enabled
5. New backends added via `MODEL_REGISTRY` — no pipeline changes required
6. Tests must use `--model mock` — never real models in CI

