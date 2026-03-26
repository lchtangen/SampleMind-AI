"""Stability AI Stable Audio Open backend for text-to-audio generation.

Phase 16 — AI Generation.
Uses the stable-audio-tools library with the stabilityai/stable-audio-open-1.0
model from HuggingFace. Supports variable-length generation (up to 47 seconds)
with conditioning on seconds_start and seconds_total prompts.

Install:
    uv sync --extra stable-audio
    # or: pip install stable-audio-tools diffusers torch
"""

from __future__ import annotations

from pathlib import Path


def _require_stable_audio() -> None:
    """Raise ImportError with install hint if stable-audio-tools is not installed."""
    try:
        import stable_audio_tools  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "stable-audio-tools is not installed. "
            "Run: uv sync --extra stable-audio\n"
            "Or:  pip install stable-audio-tools diffusers torch"
        ) from exc


class StableAudioBackend:
    """Stability AI Stable Audio Open backend.

    Args:
        model_id: HuggingFace model ID.  Defaults to the open-weights model.
    """

    name = "stable_audio"

    def __init__(
        self,
        model_id: str = "stabilityai/stable-audio-open-1.0",
    ) -> None:
        _require_stable_audio()
        self.model_id = model_id
        self._model = None
        self._sample_rate: int = 44100

    def _load_model(self) -> None:
        """Download and load the model (deferred until first call)."""
        from stable_audio_tools import get_pretrained_model
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model, self._sample_rate = get_pretrained_model(self.model_id)
        self._model = self._model.to(device)
        self._device = device

    def generate(self, req: GenerationRequest, dest_dir: Path) -> Path:  # type: ignore[name-defined]  # noqa: F821
        """Generate audio and return path to the written WAV file.

        Stable Audio Open conditions on (prompt, seconds_start, seconds_total)
        so we pass ``req.duration_seconds`` directly as ``seconds_total``.

        Args:
            req: Generation parameters.
            dest_dir: Directory in which to write the output WAV file.

        Returns:
            Absolute path to the generated WAV file.
        """
        from einops import rearrange
        import soundfile as sf
        from stable_audio_tools.inference.generation import generate_diffusion_cond
        import torch

        if self._model is None:
            self._load_model()

        conditioning = [
            {
                "prompt": req.prompt,
                "seconds_start": 0,
                "seconds_total": req.duration_seconds,
            }
        ]

        generator = None
        if req.seed is not None:
            generator = torch.Generator(device=self._device).manual_seed(req.seed)

        with torch.inference_mode():
            output = generate_diffusion_cond(
                self._model,
                steps=100,
                cfg_scale=req.guidance_scale,
                conditioning=conditioning,
                sample_size=int(self._sample_rate * req.duration_seconds),
                sigma_min=0.3,
                sigma_max=500,
                sampler_type="dpmpp-3m-sde",
                device=self._device,
                seed=req.seed,
                generator=generator,
            )

        # output shape: (batch, channels, samples) → (samples, channels)
        audio = rearrange(output, "b d n -> n d").cpu().numpy()

        dest_dir.mkdir(parents=True, exist_ok=True)
        slug = req.prompt[:24].replace(" ", "_").replace("/", "_")
        out = dest_dir / f"stable_audio_{slug}.wav"
        sf.write(str(out), audio, self._sample_rate)
        return out
