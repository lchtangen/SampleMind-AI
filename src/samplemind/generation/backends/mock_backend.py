"""Deterministic mock backend for testing generation pipeline without GPU.

Phase 16 — AI Generation.
Generates a synthetic WAV file (sine wave at 440 Hz, configurable duration)
and returns its path. Output is deterministic given the same prompt string
(uses hash of prompt as random seed). Safe to use in pytest without any
ML dependencies.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import soundfile as sf

from samplemind.generation.models import GenerationRequest


class MockBackend:
    """Deterministic sine-wave backend — no GPU, no ML deps, instant generation."""

    name = "mock"

    def generate(self, req: GenerationRequest, dest_dir: Path) -> Path:
        """Generate a deterministic 440 Hz sine-wave WAV from *req*.

        Seed priority:
        1. ``req.seed`` if explicitly set
        2. MD5 of the prompt (first 8 hex digits → int) otherwise

        Args:
            req: Generation parameters.
            dest_dir: Directory in which to write the output WAV file.

        Returns:
            Absolute path to the generated WAV file.
        """
        # Derive seed from prompt so same prompt → same output
        prompt_seed = int(
            hashlib.md5(req.prompt.encode(), usedforsecurity=False).hexdigest()[:8],
            16,
        )
        seed = req.seed if req.seed is not None else prompt_seed

        sr = 22050
        n = int(req.duration_seconds * sr)
        t = np.linspace(0, req.duration_seconds, n, dtype=np.float32)
        y = (0.5 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)

        dest_dir.mkdir(parents=True, exist_ok=True)
        slug = req.prompt[:24].replace(" ", "_").replace("/", "_")
        out = dest_dir / f"generated_{slug}_{seed}.wav"
        sf.write(str(out), y, sr)
        return out
