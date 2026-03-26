"""GenerationRequest and GenerationResult data models.

Phase 16 — AI Generation.
GenerationRequest captures prompt, duration, optional musical constraints (BPM,
key, instrument hint), backend selection, and generation parameters.
GenerationResult carries the output file path, detected audio features, and an
optional sample_id set after auto-import into the library.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """Parameters for a text-to-audio generation call."""

    prompt: str
    """Natural-language description of the sound to generate."""

    duration_seconds: float = Field(default=5.0, gt=0, le=60)
    """Requested clip length in seconds (max 60 s; actual length may differ by backend)."""

    bpm: float | None = None
    """Target tempo hint. Passed to the backend as conditioning if supported."""

    key: str | None = None
    """Target musical key hint, e.g. 'C major', 'A minor'."""

    instrument: str | None = None
    """Instrument hint, e.g. 'kick', 'pad', 'hihat'. Used to enrich the prompt."""

    backend: str = "mock"
    """Backend name: 'mock' | 'audiocraft' | 'stable_audio'."""

    seed: int | None = None
    """Random seed for reproducible generation. None = non-deterministic."""

    guidance_scale: float = Field(default=3.0, ge=0)
    """Classifier-free guidance scale (higher = more prompt-adherent, less varied)."""


class GenerationResult(BaseModel):
    """Result of a generation call, optionally enriched by auto-analysis."""

    output_path: Path
    """Absolute path to the generated WAV file."""

    duration_seconds: float
    """Actual duration of the generated clip in seconds."""

    backend_used: str
    """Name of the backend that produced the file."""

    sample_id: int | None = None
    """Library sample ID, set when auto_import=True is passed to generate()."""

    bpm_detected: float | None = None
    key_detected: str | None = None
    instrument_detected: str | None = None
    energy_detected: str | None = None
