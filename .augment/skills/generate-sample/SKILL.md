---
name: generate-sample
description: Generate new audio samples from text descriptions using AudioCraft MusicGen or Stable Audio
---

# Skill: generate-sample

Generate new audio samples from text descriptions using AI (AudioCraft MusicGen / Stable Audio Open).

## Commands

```bash
# Generate with mock backend (instant — no downloads)
uv run samplemind generate "test kick" --model mock --json

# Generate with AudioCraft (downloads ~2GB on first run)
uv run samplemind generate "dark trap kick" --bpm 140 --instrument kick
uv run samplemind generate "ambient pad A minor" --key "A min" --duration 4.0
uv run samplemind generate "hi-hat shuffle" --bpm 135 --n 5  # 5 variations

# Generate and auto-import into library
uv run samplemind generate "trap kick 808" --bpm 140 --import --json

# Generate loop (BPM-aligned: 4 bars × 4 beats × 60/BPM)
uv run samplemind generate "trap drum loop" --instrument loop --bpm 140

# Use reference audio for style transfer
uv run samplemind generate "similar vibe" --reference ~/kick.wav

# Stable Audio Open (better for one-shots)
uv run samplemind generate "dark kick" --model stable-audio --bpm 140
```

## Models

| Model | Size | Best For | Speed |
|-------|------|----------|-------|
| `mock` | 0 | testing pipeline | instant |
| `audiocraft/musicgen-small` | ~2GB | fast iteration | ~30s/2s on CPU |
| `audiocraft/musicgen-medium` | ~6GB | balanced quality | ~2min/2s on CPU |
| `audiocraft/musicgen-large` | ~12GB | best loops | ~5min/2s on CPU |
| `stable-audio` | ~3.4GB | one-shots, percussion | ~20s/2s on CPU |

Apple Silicon: set `PYTORCH_ENABLE_MPS_FALLBACK=1` for ~5x speedup.

## Key Files

```
src/samplemind/generation/
  models.py               # GenerationRequest, GenerationResult
  pipeline.py             # generate_sample() — full pipeline
  backends/
    audiocraft_backend.py # MusicGen/AudioGen
    stable_audio_backend.py # Stable Audio Open
    mock_backend.py       # sine wave (tests)

src/samplemind/cli/commands/generate_cmd.py
tests/test_generation.py
```

## Quality Flags (in GenerationResult)

| Flag | Condition | Threshold |
|------|-----------|-----------|
| `bpm_match` | abs(detected - target) ≤ 5.0 | 5 BPM tolerance |
| `key_match` | detected_key == target_key | exact match |
| `instrument_match` | classified == requested | exact match |
| `clipping` | max(abs(audio)) > 0.98 | near-full-scale warning |

## BPM-Aligned Loop Formula

```python
# Always use for instrument="loop":
duration = 4 * 4 * (60.0 / target_bpm)   # 4 bars × 4 beats × beat_duration
```

## Testing

```bash
# Fast (always works — no downloads)
uv run pytest tests/test_generation.py -m "not slow" -v

# Real model tests (downloads ~2GB+)
uv run pytest tests/test_generation.py -m slow -v
```

**Rule:** Mock backend (`model="mock"`) must ALWAYS be available for unit tests.

## Auto-Import Pipeline

When `--import` is used:
1. Generate WAV → `~/.samplemind/generated/gen_*.wav`
2. Run Phase 2 analyzer (BPM, key, instrument, energy)
3. Check quality flags (warn if bpm_match=False or clipping=True)
4. Import into SQLite via `SampleRepository`
5. Add embedding to FAISS index (Phase 11)

## Dependencies

```bash
uv add soundfile numpy
# AudioCraft:
uv add audiocraft        # Meta's package — installs torch, torchaudio
# Stable Audio:
uv add diffusers transformers accelerate
```

