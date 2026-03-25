"""
core/models/sample.py — SQLModel Sample table + Pydantic request/response schemas

The ``Sample`` class is both an ORM table (SQLModel) and a Pydantic model.
Pydantic-only schemas (SampleCreate, SampleUpdate) are defined below it.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


# ── ORM table ──────────────────────────────────────────────────────────────────


class Sample(SQLModel, table=True):
    """
    Samples table — one row per imported audio file.

    Auto-detected fields (bpm, key, mood, energy, instrument) are populated
    by the analysis pipeline and overwritten on re-import.

    Manually tagged fields (genre, tags) are set by the user and are *not*
    overwritten on re-import.
    """

    __tablename__ = "samples"  # type: ignore[assignment]

    # Primary key — auto-incremented by SQLite
    id: int | None = Field(default=None, primary_key=True)

    # File identity — path is unique (same file cannot be imported twice)
    filename: str = Field(index=True)
    path: str = Field(unique=True)

    # Auto-detected fields (from the audio analysis pipeline)
    bpm: float | None = Field(default=None)  # beats per minute
    key: str | None = Field(default=None)  # e.g. "C maj", "F# min"
    mood: str | None = Field(
        default=None
    )  # dark/chill/aggressive/euphoric/melancholic/neutral
    energy: str | None = Field(default=None)  # low/mid/high
    instrument: str | None = Field(
        default=None
    )  # kick/snare/hihat/bass/pad/lead/loop/sfx/unknown

    # Manually tagged fields (from user input — never overwritten on re-import)
    genre: str | None = Field(default=None)  # e.g. "trap", "lofi", "house"
    tags: str | None = Field(default=None)  # comma-separated free-form tags

    # Timestamp — set automatically on first insert
    imported_at: datetime | None = Field(default_factory=_now)


# ── Pydantic request schemas ───────────────────────────────────────────────────


class SampleCreate(SQLModel):
    """
    Schema for creating/upserting a sample.

    Only auto-detected fields are included — manually tagged fields (genre, tags)
    are not touched on import/re-import.
    """

    filename: str
    path: str
    bpm: float | None = None
    key: str | None = None
    mood: str | None = None
    energy: str | None = None
    instrument: str | None = None


class SampleUpdate(SQLModel):
    """Schema for updating manual tags on an existing sample (all fields optional)."""

    genre: str | None = None
    mood: str | None = None
    energy: str | None = None
    tags: str | None = None


# ── Pydantic response schema ───────────────────────────────────────────────────


class SamplePublic(SQLModel):
    """Safe public representation of a sample — used in API responses and JSON output."""

    id: int | None = None
    filename: str
    path: str
    bpm: float | None = None
    key: str | None = None
    mood: str | None = None
    energy: str | None = None
    instrument: str | None = None
    genre: str | None = None
    tags: str | None = None
    imported_at: datetime | None = None

    model_config = {"from_attributes": True}
