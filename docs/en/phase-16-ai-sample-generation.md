# Phase 16 — AI-Assisted Sample Generation

**Status: 📋 Planned** — depends on Phase 11 (embeddings) + Phase 12 (AI agent) | Phase 16 of 16 | Agent: `phase-16-ai-generation`

> **Goal:** Generate new audio samples from text descriptions, style references,
> and mood/BPM targets — directly integrated into the SampleMind workflow.
>
> **Models:** AudioCraft (Meta) · Stable Audio Open · DDSP · Riffusion ·
> Local Ollama + audio adapters.
>
> **Prerequisites:** Phase 11 (embeddings), Phase 12 (AI agent), Phase 4 (CLI).

---

## 1. Architecture

```
User Request
  │  "Generate a dark trap kick at 140 BPM in A minor"
  │  + optional reference audio file
  │
  ▼
GenerationRequest
  ├── prompt: str                   # text description
  ├── reference_audio: Path | None  # style reference (optional)
  ├── target_bpm: float | None      # tempo constraint
  ├── target_key: str | None        # key constraint
  ├── duration_seconds: float        # default 2.0s for one-shots
  ├── model: str                     # "audiocraft/musicgen-small" | "stable-audio" | ...
  └── instrument: str                # classifier hint for post-validation
       │
       ▼
  GenerationEngine (selects backend by model)
  ├── AudioCraftBackend   → Meta's MusicGen / AudioGen
  ├── StableAudioBackend  → Stability AI's Stable Audio Open
  ├── RiffusionBackend    → Spectrogram diffusion
  └── MockBackend         → tests (sine wave at target BPM)
       │
       ▼
  Generated WAV file → auto-analyze → auto-import → search index
```

---

## 2. Generation Request Model

```python
# src/samplemind/generation/models.py
"""
Data models for the AI sample generation pipeline.

GenerationRequest: input parameters
GenerationResult:  output including path, analysis, and quality flags
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class GenerationRequest:
    # Primary input
    prompt: str                      # "dark trap kick with heavy sub"

    # Style reference (optional — overrides prompt for timbre)
    reference_audio: Optional[Path] = None

    # Constraints
    target_bpm: Optional[float] = None
    target_key: Optional[str] = None
    duration_seconds: float = 2.0    # 2s for one-shots, 8s for loops
    instrument: Optional[str] = None # expected instrument (for post-validation)

    # Generation parameters
    model: str = "audiocraft/musicgen-small"
    guidance_scale: float = 3.0      # how closely to follow prompt (1.0–10.0)
    temperature: float = 1.0         # 1.0 = default, >1.0 = more random
    seed: Optional[int] = None       # None = random, set for reproducibility
    n_variations: int = 1            # generate N alternatives and pick best

    # Output
    output_dir: Optional[Path] = None  # None = ~/.samplemind/generated/


@dataclass
class GenerationResult:
    request: GenerationRequest
    output_path: Path
    duration_actual: float
    sample_rate: int

    # Post-generation analysis (from Phase 2 analyzer)
    bpm_detected: Optional[float] = None
    key_detected: Optional[str] = None
    instrument_classified: Optional[str] = None
    energy_classified: Optional[str] = None

    # Quality flags
    bpm_match: bool = True          # False if detected BPM differs from target by > 5
    key_match: bool = True          # False if detected key differs from target
    instrument_match: bool = True   # False if classified instrument != requested
    clipping: bool = False          # True if true peak > -0.1 dBFS

    # Library integration
    imported: bool = False          # True if auto-imported into library
    sample_id: Optional[int] = None # SQLite ID if imported
```

---

## 3. AudioCraft Backend (Meta MusicGen / AudioGen)

```python
# src/samplemind/generation/backends/audiocraft_backend.py
"""
Meta AudioCraft backend for sample generation.

Models available:
  audiocraft/musicgen-small   → 300M params, ~2GB VRAM, fast, lower quality
  audiocraft/musicgen-medium  → 1.5B params, ~6GB VRAM, balanced
  audiocraft/musicgen-large   → 3.3B params, ~12GB VRAM, best quality
  audiocraft/audiogen-medium  → optimized for non-musical sounds (SFX, kicks)

CPU mode:
  Works but slow (~30s for 2s of audio on M2 Mac CPU).
  Set use_sampling=True, top_k=250 for CPU efficiency.

MPS (Apple Silicon):
  PYTORCH_ENABLE_MPS_FALLBACK=1 python generate.py
  ~5x faster than CPU on M2 Ultra.

Installation:
  uv add audiocraft   # Meta's package
  # audiocraft installs: torch, torchaudio, transformers, xformers
"""
from __future__ import annotations
import numpy as np
import soundfile as sf
from pathlib import Path
from samplemind.generation.models import GenerationRequest, GenerationResult
from samplemind.core.logging import get_logger

log = get_logger(__name__)

_model_cache: dict[str, object] = {}

AUDIOCRAFT_PROMPT_TEMPLATES = {
    "kick":   "deep bass kick drum, punchy transient, {bpm} bpm, hip hop",
    "snare":  "sharp snare drum, crack, bright, {bpm} bpm, trap",
    "hihat":  "crisp hi-hat, metallic, fast, {bpm} bpm",
    "bass":   "808 bass, sub, {key}, {bpm} bpm, trap",
    "pad":    "ambient pad, {key}, slow attack, {mood}, melodic",
    "lead":   "lead synth, {key}, melodic, {bpm} bpm, electronic",
    "loop":   "full drum loop, {bpm} bpm, trap, 4 bars",
    "sfx":    "audio effect, atmosphere, texture, non-musical",
}


def _enrich_prompt(request: GenerationRequest) -> str:
    """Expand the user's prompt with BPM, key, and instrument context."""
    base = request.prompt
    additions = []
    if request.target_bpm:
        additions.append(f"{int(request.target_bpm)} BPM")
    if request.target_key:
        additions.append(f"in {request.target_key}")
    if request.instrument and request.instrument != "unknown":
        template = AUDIOCRAFT_PROMPT_TEMPLATES.get(request.instrument, "")
        if template:
            base = template.format(
                bpm=int(request.target_bpm or 120),
                key=request.target_key or "C maj",
                mood="dark",
            ) + f", {base}"
    if additions:
        base = base + ", " + ", ".join(additions)
    return base


def _get_musicgen(model_name: str):
    """Lazy-load MusicGen model — cached after first load."""
    if model_name not in _model_cache:
        from audiocraft.models import MusicGen
        log.info("loading_musicgen", model=model_name)
        _model_cache[model_name] = MusicGen.get_pretrained(
            model_name.replace("audiocraft/", "")
        )
    return _model_cache[model_name]


def generate(request: GenerationRequest) -> GenerationResult:
    """
    Generate audio using Meta MusicGen/AudioGen.

    Args:
        request: GenerationRequest with prompt, constraints, and model

    Returns:
        GenerationResult with path to generated WAV file
    """
    import torch
    model = _get_musicgen(request.model)
    model.set_generation_params(
        duration=request.duration_seconds,
        guidance_scale=request.guidance_scale,
        temperature=request.temperature,
        top_k=250,
    )

    enriched_prompt = _enrich_prompt(request)
    log.info("generating", prompt=enriched_prompt, model=request.model,
             duration=request.duration_seconds)

    # Generate N variations, pick best (by RMS — highest energy wins)
    prompts = [enriched_prompt] * request.n_variations
    with torch.no_grad():
        wav = model.generate(prompts)   # shape: (n, 1, samples)

    best_idx = int(wav.squeeze(1).pow(2).mean(dim=1).argmax())
    audio = wav[best_idx, 0].cpu().numpy().astype(np.float32)

    # Output path
    out_dir = request.output_dir or (Path.home() / ".samplemind" / "generated")
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = __import__("time").strftime("%Y%m%d_%H%M%S")
    slug = request.prompt[:30].replace(" ", "_").lower()
    out_path = out_dir / f"gen_{slug}_{timestamp}.wav"

    sf.write(str(out_path), audio, model.sample_rate)
    log.info("generated", path=str(out_path), size_kb=round(out_path.stat().st_size / 1024, 1))

    return GenerationResult(
        request=request,
        output_path=out_path,
        duration_actual=len(audio) / model.sample_rate,
        sample_rate=model.sample_rate,
    )
```

---

## 4. Stable Audio Open Backend

```python
# src/samplemind/generation/backends/stable_audio_backend.py
"""
Stability AI's Stable Audio Open backend.

Stable Audio Open is specifically designed for audio sample generation
(not music generation), making it better than MusicGen for:
  - Drum one-shots (kick, snare, hihat)
  - Sound effects and textures
  - Percussive loops at specific BPMs

Model: stabilityai/stable-audio-open-1.0 (HuggingFace)
Requirements:
  uv add diffusers transformers accelerate soundfile
  # Model size: ~3.4GB (downloaded on first use to ~/.cache/huggingface/)

BPM conditioning:
  Stable Audio Open supports explicit seconds_start and seconds_total
  conditioning — use to generate exact-length samples for BPM alignment.
"""
from __future__ import annotations
import numpy as np
import soundfile as sf
from pathlib import Path
from samplemind.generation.models import GenerationRequest, GenerationResult
from samplemind.core.logging import get_logger

log = get_logger(__name__)
_pipe_cache = None


def _get_pipeline():
    global _pipe_cache
    if _pipe_cache is None:
        import torch
        from diffusers import StableAudioPipeline

        log.info("loading_stable_audio")
        _pipe_cache = StableAudioPipeline.from_pretrained(
            "stabilityai/stable-audio-open-1.0",
            torch_dtype=torch.float16,
        )
        # Use MPS on Apple Silicon if available
        if torch.backends.mps.is_available():
            _pipe_cache = _pipe_cache.to("mps")
        elif torch.cuda.is_available():
            _pipe_cache = _pipe_cache.to("cuda")
    return _pipe_cache


def generate(request: GenerationRequest) -> GenerationResult:
    """Generate with Stable Audio Open — optimized for one-shots and loops."""
    import torch
    pipe = _get_pipeline()

    # BPM-aligned duration for loops
    duration = request.duration_seconds
    if request.target_bpm and request.instrument == "loop":
        bars = 4   # generate 4 bars
        beats_per_bar = 4
        duration = bars * beats_per_bar * (60.0 / request.target_bpm)
        log.debug("bpm_aligned_duration", bpm=request.target_bpm, duration=duration)

    generator = (
        torch.Generator(device="cpu").manual_seed(request.seed)
        if request.seed is not None else None
    )

    output = pipe(
        request.prompt,
        negative_prompt="noise, low quality, clipping, distorted",
        num_inference_steps=200,   # higher = better quality, slower
        audio_end_in_s=duration,
        num_waveforms_per_prompt=request.n_variations,
        generator=generator,
    )

    # Pick best by energy
    waveforms = output.audios   # shape: (n_variations, samples)
    best_idx  = int(np.array([w.mean()**2 for w in waveforms]).argmax())
    audio     = waveforms[best_idx]

    sample_rate = pipe.vae.config.sampling_rate   # usually 44100

    out_dir = request.output_dir or (Path.home() / ".samplemind" / "generated")
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = request.prompt[:30].replace(" ", "_").lower()
    ts   = __import__("time").strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"sa_{slug}_{ts}.wav"

    sf.write(str(out_path), audio, sample_rate)
    return GenerationResult(
        request=request,
        output_path=out_path,
        duration_actual=len(audio) / sample_rate,
        sample_rate=sample_rate,
    )
```

---

## 5. Post-Generation Analysis and Auto-Import

```python
# src/samplemind/generation/pipeline.py
"""
Full generation pipeline: generate → analyze → validate → import.

After generation:
  1. Run Phase 2 audio analyzer on the generated file
  2. Check if BPM/key/instrument match the request
  3. Optionally auto-import into the library
  4. Add to FAISS vector index (Phase 11)
"""
from __future__ import annotations
from pathlib import Path
from samplemind.generation.models import GenerationRequest, GenerationResult
from samplemind.core.logging import get_logger

log = get_logger(__name__)

MODEL_REGISTRY = {
    "audiocraft/musicgen-small":   "samplemind.generation.backends.audiocraft_backend",
    "audiocraft/musicgen-medium":  "samplemind.generation.backends.audiocraft_backend",
    "audiocraft/musicgen-large":   "samplemind.generation.backends.audiocraft_backend",
    "stable-audio":                "samplemind.generation.backends.stable_audio_backend",
    "mock":                        "samplemind.generation.backends.mock_backend",
}


def generate_sample(request: GenerationRequest, auto_import: bool = False) -> GenerationResult:
    """
    Full generation pipeline: generate → analyze → validate → (auto-import).

    Args:
        request:     GenerationRequest with all parameters
        auto_import: If True, automatically import into the library

    Returns:
        GenerationResult with analysis, quality flags, and optional sample_id
    """
    # 1. Select and run backend
    backend_module = MODEL_REGISTRY.get(request.model, MODEL_REGISTRY["mock"])
    import importlib
    backend = importlib.import_module(backend_module)
    result = backend.generate(request)

    # 2. Analyze generated audio
    try:
        from samplemind.analyzer.audio_analysis import analyze_file
        analysis = analyze_file(str(result.output_path))
        result.bpm_detected          = analysis.get("bpm")
        result.key_detected          = analysis.get("key")
        result.instrument_classified = analysis.get("instrument")
        result.energy_classified     = analysis.get("energy")
    except Exception as e:
        log.warning("post_analysis_failed", error=str(e))

    # 3. Quality validation
    if request.target_bpm and result.bpm_detected:
        result.bpm_match = abs(result.bpm_detected - request.target_bpm) <= 5.0
    if request.target_key and result.key_detected:
        result.key_match = result.key_detected == request.target_key
    if request.instrument and result.instrument_classified:
        result.instrument_match = result.instrument_classified == request.instrument

    # Clipping check
    try:
        import soundfile as sf, numpy as np
        data, _ = sf.read(str(result.output_path))
        result.clipping = float(np.max(np.abs(data))) > 0.98
    except Exception:
        pass

    # 4. Auto-import
    if auto_import:
        try:
            from samplemind.data.repositories.sample_repository import SampleRepository
            sample = SampleRepository.import_from_path(result.output_path, analysis or {})
            result.imported  = True
            result.sample_id = sample.id

            # Update FAISS index
            from samplemind.search.embeddings import embed_audio
            from samplemind.search.vector_index import get_vector_index
            vec = embed_audio(result.output_path)
            get_vector_index().add_batch([sample.id], vec.reshape(1, -1))
        except Exception as e:
            log.error("auto_import_failed", error=str(e))

    # Quality summary
    quality_flags = []
    if not result.bpm_match:
        quality_flags.append(f"BPM mismatch: target={request.target_bpm}, got={result.bpm_detected}")
    if not result.key_match:
        quality_flags.append(f"Key mismatch: target={request.target_key}, got={result.key_detected}")
    if result.clipping:
        quality_flags.append("WARNING: audio is clipping (peak > -0.1 dBFS)")
    if quality_flags:
        log.warning("generation_quality_issues", issues=quality_flags)

    return result
```

---

## 6. CLI Generate Command

```python
# src/samplemind/cli/commands/generate_cmd.py
"""
AI sample generation CLI.

Usage:
  uv run samplemind generate "dark trap kick" --bpm 140 --import
  uv run samplemind generate "ambient pad in A minor" --model audiocraft/musicgen-large
  uv run samplemind generate "hi-hat shuffle" --bpm 135 --n 5 --duration 1.0
  uv run samplemind generate "similar to this" --reference ~/kick.wav
"""
import json, sys
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="AI-powered sample generation")
console = Console(stderr=True)


@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Text description of the desired sound"),
    bpm: float = typer.Option(None, "--bpm", help="Target BPM"),
    key: str = typer.Option(None, "--key", "-k", help="Target key e.g. 'A min'"),
    duration: float = typer.Option(2.0, "--duration", "-d", help="Duration in seconds"),
    instrument: str = typer.Option(None, "--instrument", "-i"),
    model: str = typer.Option("audiocraft/musicgen-small", "--model", "-m"),
    reference: str = typer.Option(None, "--reference", "-r", help="Reference audio file"),
    n: int = typer.Option(1, "--n", help="Number of variations to generate"),
    seed: int = typer.Option(None, "--seed", help="Seed for reproducibility"),
    auto_import: bool = typer.Option(False, "--import", help="Auto-import into library"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Generate a new audio sample using AI."""
    from samplemind.core.feature_flags import is_enabled
    # Generation is available to all but requires model downloads

    from samplemind.generation.models import GenerationRequest
    from samplemind.generation.pipeline import generate_sample

    request = GenerationRequest(
        prompt=prompt,
        reference_audio=Path(reference).expanduser() if reference else None,
        target_bpm=bpm,
        target_key=key,
        duration_seconds=duration,
        instrument=instrument,
        model=model,
        n_variations=n,
        seed=seed,
    )

    console.print(f"[cyan]Generating:[/cyan] {prompt!r}")
    console.print(f"[dim]Model:[/dim] {model} · {n} variation(s) · {duration}s")

    result = generate_sample(request, auto_import=auto_import)

    output = {
        "path":       str(result.output_path),
        "duration":   result.duration_actual,
        "bpm":        result.bpm_detected,
        "key":        result.key_detected,
        "instrument": result.instrument_classified,
        "energy":     result.energy_classified,
        "bpm_match":  result.bpm_match,
        "key_match":  result.key_match,
        "clipping":   result.clipping,
        "imported":   result.imported,
        "sample_id":  result.sample_id,
    }

    if json_output:
        print(json.dumps(output, indent=2))
        return

    table = Table(title="Generation Result")
    for k, v in output.items():
        style = "red" if k == "clipping" and v else "green" if not result.clipping else ""
        table.add_row(k, str(v), style=style)
    console.print(table)

    if result.clipping:
        console.print("[red]⚠ WARNING: Generated audio is clipping.[/red]")
    if not result.bpm_match:
        console.print(f"[yellow]⚠ BPM target: {bpm}, detected: {result.bpm_detected}[/yellow]")
```

---

## 7. Mock Backend for Tests

```python
# src/samplemind/generation/backends/mock_backend.py
"""
Mock generation backend for tests.

Generates a sine wave at the target BPM's note frequency.
No ML models required — instant, deterministic, small.

Used automatically when model="mock":
  GenerationRequest(prompt="test", model="mock")
"""
from __future__ import annotations
import numpy as np
import soundfile as sf
from pathlib import Path
from samplemind.generation.models import GenerationRequest, GenerationResult


def generate(request: GenerationRequest) -> GenerationResult:
    """Generate a simple sine wave — used for testing."""
    sr = 22050
    duration = request.duration_seconds
    t = np.linspace(0, duration, int(sr * duration), dtype=np.float32)

    # Frequency based on BPM: 60/BPM = beat period, use 1/period as frequency
    freq = request.target_bpm / 60.0 if request.target_bpm else 2.0
    audio = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)

    out_dir = request.output_dir or (Path.home() / ".samplemind" / "generated")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"mock_{request.prompt[:20].replace(' ', '_')}.wav"
    sf.write(str(out_path), audio, sr)

    return GenerationResult(
        request=request,
        output_path=out_path,
        duration_actual=duration,
        sample_rate=sr,
    )
```

---

## 8. Testing

```python
# tests/test_generation.py
"""
Tests for Phase 16 sample generation.
All real model backends are mocked — no GPU/model downloads needed.
"""
import pytest
import numpy as np
from pathlib import Path
from samplemind.generation.models import GenerationRequest


def test_mock_backend_generates_file(tmp_path):
    """Mock backend should create a WAV file."""
    from samplemind.generation.backends.mock_backend import generate
    request = GenerationRequest(
        prompt="test kick", model="mock", duration_seconds=1.0,
        target_bpm=140.0, output_dir=tmp_path,
    )
    result = generate(request)
    assert result.output_path.exists()
    assert result.duration_actual == pytest.approx(1.0, abs=0.1)


def test_mock_backend_bpm_affects_frequency(tmp_path):
    """Different BPM should produce different sine frequency."""
    from samplemind.generation.backends.mock_backend import generate
    import soundfile as sf

    r1 = generate(GenerationRequest(prompt="test", model="mock", target_bpm=120.0, output_dir=tmp_path))
    r2 = generate(GenerationRequest(prompt="test", model="mock", target_bpm=140.0, output_dir=tmp_path / "b"))

    d1, _ = sf.read(str(r1.output_path))
    d2, _ = sf.read(str(r2.output_path))
    # They should differ (different frequencies)
    assert not np.allclose(d1[:1000], d2[:1000])


def test_pipeline_quality_flags(tmp_path):
    """Pipeline should set bpm_match=False when BPM is way off."""
    from samplemind.generation.pipeline import generate_sample
    from unittest.mock import patch

    request = GenerationRequest(
        prompt="test", model="mock", target_bpm=140.0,
        target_key="A min", instrument="kick", output_dir=tmp_path,
    )
    # Mock analyzer to return very different BPM
    with patch("samplemind.generation.pipeline.analyze_file") as mock_analyze:
        mock_analyze.return_value = {
            "bpm": 90.0, "key": "C maj", "instrument": "pad", "energy": "low"
        }
        result = generate_sample(request, auto_import=False)

    assert result.bpm_match is False      # 140 vs 90 → mismatch
    assert result.key_match is False      # A min vs C maj → mismatch
    assert result.instrument_match is False  # kick vs pad → mismatch


@pytest.mark.slow
def test_audiocraft_backend_real_generation(tmp_path):
    """Requires AudioCraft model download (~2GB). Only run with -m slow."""
    from samplemind.generation.backends.audiocraft_backend import generate
    request = GenerationRequest(
        prompt="kick drum, punchy, 140 bpm",
        model="audiocraft/musicgen-small",
        duration_seconds=2.0,
        output_dir=tmp_path,
    )
    result = generate(request)
    assert result.output_path.exists()
    assert result.duration_actual >= 1.5
```

---

## 9. Checklist

- [ ] Mock backend generates WAV without any ML models
- [ ] `generate_sample()` pipeline runs: generate → analyze → quality check
- [ ] Quality flags set correctly: bpm_match, key_match, instrument_match, clipping
- [ ] `uv run samplemind generate "test" --model mock --json` works
- [ ] AudioCraft backend: `from audiocraft.models import MusicGen` imports cleanly
- [ ] Stable Audio backend: `from diffusers import StableAudioPipeline` imports cleanly
- [ ] BPM-aligned duration for loops: 4 bars × 4 beats × (60/BPM)
- [ ] Auto-import updates both SQLite and FAISS index
- [ ] All tests pass: `uv run pytest tests/test_generation.py -m "not slow"`
- [ ] Slow tests documented: `uv run pytest tests/test_generation.py -m slow`
- [ ] Model registry extendable without modifying pipeline.py
- [ ] Generated files stored in `~/.samplemind/generated/` by default

