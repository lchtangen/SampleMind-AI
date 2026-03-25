"""
data/repositories/sample_repository.py — SQLModel-based Sample repository

All database access for audio samples goes through this class.
No raw SQL strings outside this file.

Replaces the legacy sqlite3 functions in data/database.py:
  save_sample()        → SampleRepository.upsert()
  tag_sample()         → SampleRepository.tag()
  search_samples()     → SampleRepository.search()
  get_sample_by_name() → SampleRepository.get_by_name()
  count_samples()      → SampleRepository.count()
  get_all_samples()    → SampleRepository.get_all()
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlmodel import Session, select

from samplemind.core.models.sample import Sample, SampleCreate, SampleUpdate
from samplemind.data.orm import get_session

logger = logging.getLogger(__name__)


class SampleRepository:
    """
    Repository for audio sample CRUD operations.

    All methods are static and use the shared SQLModel session from orm.py.
    """

    # ── Create / Upsert ──────────────────────────────────────────────────────

    @staticmethod
    def upsert(data: SampleCreate) -> Sample:
        """
        Insert a new sample, or update auto-detected fields if path already exists.

        Manually tagged fields (genre, tags) are *never* overwritten on re-import.
        """
        with get_session() as session:
            existing = session.exec(
                select(Sample).where(Sample.path == data.path)
            ).first()

            if existing:
                existing.bpm = data.bpm
                existing.key = data.key
                existing.mood = data.mood
                existing.energy = data.energy
                existing.instrument = data.instrument
                existing.filename = data.filename
                session.add(existing)
                logger.debug("Updated existing sample: %s", data.path)
                return existing

            sample = Sample(
                filename=data.filename,
                path=data.path,
                bpm=data.bpm,
                key=data.key,
                mood=data.mood,
                energy=data.energy,
                instrument=data.instrument,
            )
            session.add(sample)
            logger.debug("Inserted new sample: %s", data.path)
            return sample

    # ── Update Tags ───────────────────────────────────────────────────────────

    @staticmethod
    def tag(path: str, update: SampleUpdate) -> Optional[Sample]:
        """
        Update manual tags (genre, mood, energy, tags) for a sample by path.
        Only fields explicitly set (not None) are written.
        """
        with get_session() as session:
            sample = session.exec(
                select(Sample).where(Sample.path == path)
            ).first()
            if not sample:
                return None

            update_data = update.model_dump(exclude_none=True)
            for field, value in update_data.items():
                setattr(sample, field, value)
            session.add(sample)
            return sample

    # ── Search ────────────────────────────────────────────────────────────────

    @staticmethod
    def search(
        query: Optional[str] = None,
        bpm_min: Optional[float] = None,
        bpm_max: Optional[float] = None,
        key: Optional[str] = None,
        genre: Optional[str] = None,
        energy: Optional[str] = None,
        instrument: Optional[str] = None,
    ) -> list[Sample]:
        """Search with combined filters — all filters are optional."""
        with get_session() as session:
            stmt = select(Sample)

            if query:
                stmt = stmt.where(
                    Sample.filename.contains(query) | Sample.tags.contains(query)
                )
            if bpm_min is not None:
                stmt = stmt.where(Sample.bpm >= bpm_min)
            if bpm_max is not None:
                stmt = stmt.where(Sample.bpm <= bpm_max)
            if key:
                stmt = stmt.where(Sample.key.contains(key))
            if genre:
                stmt = stmt.where(Sample.genre.contains(genre))
            if energy:
                stmt = stmt.where(Sample.energy == energy)
            if instrument:
                stmt = stmt.where(Sample.instrument.contains(instrument))

            stmt = stmt.order_by(Sample.imported_at.desc())
            return list(session.exec(stmt).all())

    # ── Lookup ────────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_name(name: str) -> Optional[Sample]:
        """Find sample by partial filename match (case-insensitive LIKE)."""
        with get_session() as session:
            return session.exec(
                select(Sample).where(Sample.filename.contains(name)).limit(1)
            ).first()

    @staticmethod
    def get_by_path(path: str) -> Optional[Sample]:
        """Find sample by exact file path."""
        with get_session() as session:
            return session.exec(
                select(Sample).where(Sample.path == path)
            ).first()

    @staticmethod
    def get_by_id(sample_id: int) -> Optional[Sample]:
        """Find sample by integer primary key."""
        with get_session() as session:
            return session.get(Sample, sample_id)

    @staticmethod
    def count() -> int:
        """Return total number of samples in the library."""
        with get_session() as session:
            return len(session.exec(select(Sample)).all())

    @staticmethod
    def get_all() -> list[Sample]:
        """Return all samples ordered by import date descending."""
        return SampleRepository.search()

    # ── Delete ────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_by_path(path: str) -> bool:
        """Delete a sample row by exact file path.

        Used by the ``duplicates --remove`` command to remove the DB record
        for a duplicate file after the file itself has been unlinked from disk.

        Args:
            path: Absolute file path matching Sample.path exactly.

        Returns:
            True if a row was found and deleted; False if no row matched.
        """
        with get_session() as session:
            sample = session.exec(
                select(Sample).where(Sample.path == path)
            ).first()
            if sample is None:
                return False
            session.delete(sample)
            # commit is handled by get_session()'s context manager
            return True

