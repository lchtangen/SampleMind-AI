"""Pydantic data models for the .smpack sample pack format.

A .smpack file is a ZIP archive containing:
  manifest.json  -- PackManifest serialised with model_dump_json()
  *.wav          -- audio files at the paths listed in manifest.entries

The manifest carries full SHA-256 checksums for every audio file so that
importers can detect tampering or corruption before touching the library.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator

_VALID_ENERGY = {"low", "mid", "high"}


class PackEntry(BaseModel):
    """Metadata and integrity information for one audio file inside a pack."""

    filename: str
    """Relative POSIX path within the pack archive, e.g. 'kicks/kick_128.wav'."""

    sha256: str
    """Full-file SHA-256 hex digest (64 lowercase chars).  Verified on import."""

    size_bytes: int
    """Uncompressed file size in bytes."""

    bpm: float | None = None
    key: str | None = None
    energy: str | None = None
    mood: str | None = None
    instrument: str | None = None
    genre: str | None = None
    tags: str | None = None

    @field_validator("sha256")
    @classmethod
    def _valid_hex(cls, v: str) -> str:
        v = v.lower()
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            raise ValueError("sha256 must be a 64-character lowercase hex string")
        return v

    @field_validator("energy")
    @classmethod
    def _valid_energy(cls, v: str | None) -> str | None:
        if v is not None and v not in _VALID_ENERGY:
            raise ValueError(f"energy must be one of {sorted(_VALID_ENERGY)!r}, got {v!r}")
        return v


class PackManifest(BaseModel):
    """Root manifest for a .smpack archive."""

    name: str
    """Human-readable pack name, e.g. 'Dark Trap Essentials'."""

    version: str
    """Semantic version string, e.g. '1.0.0'."""

    author: str
    """Creator name or organisation."""

    description: str
    """Short description shown in the SampleMind pack browser."""

    created_at: str
    """ISO 8601 UTC timestamp, e.g. '2026-03-25T00:00:00Z'."""

    samplemind_version: str = "0.2.0"
    """Minimum SampleMind version required to import this pack."""

    entries: list[PackEntry]
    """One entry per audio file in the archive."""

    @field_validator("version")
    @classmethod
    def _valid_semver(cls, v: str) -> str:
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"version must be semver (e.g. '1.0.0'), got {v!r}")
        return v

    @property
    def total_size_bytes(self) -> int:
        """Sum of uncompressed sizes of all entries."""
        return sum(e.size_bytes for e in self.entries)

    @property
    def entry_count(self) -> int:
        return len(self.entries)
