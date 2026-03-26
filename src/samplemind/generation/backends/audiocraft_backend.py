"""Meta AudioCraft MusicGen/AudioGen backend for text-to-audio generation.

Phase 16 — AI Generation.
Uses audiocraft.models.MusicGen (music loops) and audiocraft.models.AudioGen
(sound effects) from Meta's AudioCraft library. Model size is configurable:
small (300M), medium (1.5B), large (3.3B). Runs on GPU if available, else CPU.

Install:
    uv sync --extra generation
    # or: pip install audiocraft
"""

from __future__ import annotations

from pathlib import Path


def _require_audiocraft() -> None:
    """Raise ImportError with install hint if audiocraft is not installed."""
    try:
        import audiocraft  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "AudioCraft is not installed. "
            "Run: uv sync --extra generation\n"
            "Or:  pip install audiocraft"
        ) from exc


class AudioCraftBackend:
    """Meta MusicGen / AudioGen backend.

    Args:
        model_size: One of ``"small"`` (300M, recommended for CPU),
            ``"medium"`` (1.5B), or ``"large"`` (3.3B).
        task: ``"musicgen"`` for music loops or ``"audiogen"`` for SFX.
    """

    name = "audiocraft"

    def __init__(
        self,
        model_size: str = "small",
        task: str = "musicgen",
    ) -> None:
        _require_audiocraft()
        self.model_size = model_size
        self.task = task
        self._model = None  # lazy — loaded on first generate() call

    def _load_model(self) -> None:
        """Load the AudioCraft model (deferred until first call)."""
        import torch

        if self.task == "musicgen":
            from audiocraft.models import MusicGen

            self._model = MusicGen.get_pretrained(
                f"facebook/musicgen-{self.model_size}",
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
        elif self.task == "audiogen":
            from audiocraft.models import AudioGen

            self._model = AudioGen.get_pretrained(
                f"facebook/audiogen-{self.model_size}",
                device="cuda" if torch.cuda.is_available() else "cpu",
            )
        else:
            raise ValueError(f"Unknown task {self.task!r}. Choose 'musicgen' or 'audiogen'.")

    def generate(self, req: GenerationRequest, dest_dir: Path) -> Path:  # type: ignore[name-defined]  # noqa: F821
        """Generate audio and return path to the written WAV file.

        Args:
            req: Generation parameters.
            dest_dir: Directory in which to write the output WAV file.

        Returns:
            Absolute path to the generated WAV file.
        """
        import soundfile as sf
        import torch

        from samplemind.generation.models import (
            GenerationRequest,  # noqa: F401 (for type check)
        )

        if self._model is None:
            self._load_model()

        # Build enriched prompt
        prompt = req.prompt
        if req.instrument:
            prompt = f"{req.instrument} {prompt}"
        if req.key:
            prompt = f"{prompt}, key {req.key}"
        if req.bpm:
            prompt = f"{prompt}, {int(req.bpm)} bpm"

        self._model.set_generation_params(
            duration=req.duration_seconds,
            cfg_coef=req.guidance_scale,
        )

        with torch.inference_mode():
            wav = self._model.generate([prompt])  # shape: (batch, channels, samples)

        # wav[0] → (channels, samples); convert to (samples,) or (samples, channels)
        audio = wav[0].cpu().numpy()
        if audio.ndim == 2:
            audio = audio.T  # (samples, channels)
        elif audio.ndim == 1:
            pass  # already (samples,)
        else:
            audio = audio[0]  # take first channel

        sr = self._model.sample_rate
        dest_dir.mkdir(parents=True, exist_ok=True)
        slug = req.prompt[:24].replace(" ", "_").replace("/", "_")
        out = dest_dir / f"audiocraft_{self.task}_{slug}.wav"
        sf.write(str(out), audio, sr)
        return out
