"""Generation backend registry: AudioCraft, Stable Audio, and Mock.

Phase 16 — AI Generation.
Each backend implements the BaseGenerationBackend protocol:
  generate(request: GenerationRequest, dest_dir: Path) -> Path

Backends are selected at runtime by GenerationRequest.backend name.
"""

from __future__ import annotations

from samplemind.generation.backends.audiocraft_backend import AudioCraftBackend
from samplemind.generation.backends.mock_backend import MockBackend
from samplemind.generation.backends.stable_audio_backend import StableAudioBackend

__all__ = ["AudioCraftBackend", "MockBackend", "StableAudioBackend"]
