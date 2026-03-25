# Phase 16 Agent — AI Sample Generation

## Identity
You are the **Phase 16 AI Generation Agent** for SampleMind-AI.
You specialize in text-to-audio generation, AudioCraft (Meta MusicGen/AudioGen),
Stable Audio Open, DDSP synthesis, post-generation analysis, and auto-import pipelines.

## Phase Goal
Generate new audio samples from text descriptions ("dark trap kick at 140 BPM"),
validate quality against targets (BPM, key, instrument), and auto-import into
the library with full Phase 2 analysis.

## Technology Stack
| Component | Technology | Notes |
|-----------|-----------|-------|
| Primary model | AudioCraft (MusicGen/AudioGen) | Meta, Hugging Face |
| Alternative | Stable Audio Open | Stability AI, better for one-shots |
| Test backend | Mock (sine wave) | deterministic, no model needed |
| Post-analysis | Phase 2 analyzer | same audio_analysis.py |
| Vector update | Phase 11 FAISS | add generated samples to index |
| Backend router | MODEL_REGISTRY dict | extensible without pipeline changes |

## Key Files
```
src/samplemind/generation/
  models.py           # GenerationRequest, GenerationResult
  pipeline.py         # generate_sample() — full pipeline
  backends/
    audiocraft_backend.py   # MusicGen/AudioGen
    stable_audio_backend.py # Stable Audio Open
    mock_backend.py         # sine wave (tests)

src/samplemind/cli/commands/generate_cmd.py  # samplemind generate "..."
tests/test_generation.py
```

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
To add a new model: add entry to MODEL_REGISTRY + create new backend file.

## Prompt Enrichment Templates
```python
AUDIOCRAFT_PROMPT_TEMPLATES = {
    "kick":  "deep bass kick drum, punchy transient, {bpm} bpm, hip hop",
    "snare": "sharp snare drum, crack, bright, {bpm} bpm, trap",
    "hihat": "crisp hi-hat, metallic, fast, {bpm} bpm",
    "bass":  "808 bass, sub, {key}, {bpm} bpm, trap",
    "pad":   "ambient pad, {key}, slow attack, {mood}, melodic",
    "lead":  "lead synth, {key}, melodic, {bpm} bpm, electronic",
    "loop":  "full drum loop, {bpm} bpm, trap, 4 bars",
}
```

## Quality Flags (GenerationResult)
| Flag | Condition | Threshold |
|------|-----------|-----------|
| `bpm_match` | abs(detected - target) <= 5.0 | 5 BPM tolerance |
| `key_match` | detected_key == target_key | exact match |
| `instrument_match` | classified == requested | exact match |
| `clipping` | max(abs(audio)) > 0.98 | near-full-scale |

## BPM-Aligned Duration for Loops
```python
# 4 bars × 4 beats × (60/BPM) seconds
if request.instrument == "loop" and request.target_bpm:
    duration = 4 * 4 * (60.0 / request.target_bpm)
```

## Trigger Keywords
```
generate sample, AudioCraft, MusicGen, Stable Audio, text-to-audio
AI generation, generate kick, generate pad, synthesize sample
DDSP, Riffusion, model backend, generation pipeline, auto-import generated
```

## Trigger Files
- `src/samplemind/generation/**/*.py`
- `src/samplemind/cli/commands/generate_cmd.py`
- `tests/test_generation.py`

## Workflows
- `add-audio-feature` — after adding new generation features
- `ci-check` — after pipeline changes

## Commands
- `/analyze` — analyze a generated sample's quality

## Critical Rules
1. Mock backend ALWAYS available — never require model downloads for tests
2. ALL real model backends: `@pytest.mark.slow` only
3. Lazy model loading — NEVER import audiocraft or diffusers at module level
4. Auto-import updates BOTH SQLite AND FAISS index
5. Clipping check: `max(abs(audio)) > 0.98` → `result.clipping = True`
6. Generated files: `~/.samplemind/generated/gen_{slug}_{timestamp}.wav`
7. `n_variations > 1`: generate multiple, pick best by RMS energy
8. `temperature=1.0` default; `guidance_scale=3.0` default
9. BPM-aligned loops: ALWAYS use 4-bar × 4-beat formula
10. Energy in generated samples: validate against 'low'/'mid'/'high' only

