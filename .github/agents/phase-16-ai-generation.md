# Phase 16 Agent — AI Sample Generation

Handles: AudioCraft MusicGen, Stable Audio Open, text-to-audio, quality validation, auto-import.

## Triggers
- Phase 16, AI generation, AudioCraft, MusicGen, Stable Audio, text-to-audio, generate sample, generation pipeline

## Key Files
- `src/samplemind/generation/models.py`
- `src/samplemind/generation/pipeline.py`
- `src/samplemind/generation/backends/`
- `src/samplemind/cli/commands/generate_cmd.py`

## Model Registry

```python
MODEL_REGISTRY = {
    "audiocraft/musicgen-small":  "backends.audiocraft_backend",
    "audiocraft/musicgen-medium": "backends.audiocraft_backend",
    "audiocraft/musicgen-large":  "backends.audiocraft_backend",
    "stable-audio":               "backends.stable_audio_backend",
    "mock":                       "backends.mock_backend",
}
```

## BPM-Aligned Loop Formula

```python
# For instrument="loop" with target_bpm:
duration = 4 * 4 * (60.0 / target_bpm)   # 4 bars × 4 beats × beat_duration
```

## Quality Flags

| Flag | Threshold |
|------|-----------|
| `bpm_match` | abs(detected - target) ≤ 5.0 BPM |
| `key_match` | exact string match |
| `instrument_match` | exact match of classifier output |
| `clipping` | max(abs(audio)) > 0.98 |

## Rules
1. Mock backend ALWAYS available — no downloads needed for unit tests
2. Real backends: `@pytest.mark.slow` only
3. Lazy model loading — NEVER import audiocraft or diffusers at module level
4. Auto-import updates BOTH SQLite AND FAISS index
5. n_variations > 1: generate multiple, pick best by RMS energy
6. Generated files: `~/.samplemind/generated/gen_{slug}_{timestamp}.wav`
7. Apple Silicon: `PYTORCH_ENABLE_MPS_FALLBACK=1` for ~5x speedup

