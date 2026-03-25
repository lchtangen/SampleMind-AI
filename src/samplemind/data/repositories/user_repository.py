"""
data/repositories/user_repository.py — synchronous CRUD for the User table

All methods are synchronous (SQLite + SQLModel doesn't need async for a
single-user desktop app).  FastAPI async routes call these via a thread
pool automatically thanks to Starlette's ``run_in_threadpool``.

Pattern: class with @staticmethod methods — no instance state needed.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Optional

from sqlmodel import select

from samplemind.core.models.user import User
from samplemind.data.orm import get_session

logger = logging.getLogger(__name__)


class UserRepository:
    """Static CRUD methods for the ``users`` table."""

    # ── Read ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(user_id: str) -> Optional[User]:
        """Return user by UUID string, or None."""
        with get_session() as session:
            return session.exec(
                select(User).where(User.user_id == user_id)
            ).first()

    @staticmethod
    def get_by_email(email: str) -> Optional[User]:
        """Return user by email (case-sensitive), or None."""
        with get_session() as session:
            return session.exec(
                select(User).where(User.email == email.lower())
            ).first()

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """Return user by username (case-insensitive), or None."""
        with get_session() as session:
            return session.exec(
                select(User).where(User.username == username.lower())
            ).first()

    # ── Write ─────────────────────────────────────────────────────────────────

    @staticmethod
    def create(
        email: str,
        username: str,
        hashed_password: str,
        role: str = "owner",
        is_active: bool = True,
        is_verified: bool = False,
    ) -> User:
        """Insert a new user and return the persisted object."""
        user = User(
            user_id=str(uuid.uuid4()),
            email=email.lower(),
            username=username.lower(),
            hashed_password=hashed_password,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        with get_session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    @staticmethod
    def update(user_id: str, **fields) -> Optional[User]:
        """
        Update arbitrary fields on a user by UUID.

        ``updated_at`` is always refreshed automatically.
        Returns the updated User or None if not found.
        """
        with get_session() as session:
            user = session.exec(
                select(User).where(User.user_id == user_id)
            ).first()
            if user is None:
                return None

            for key, value in fields.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.now(UTC)

            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    @staticmethod
    def record_login(user_id: str) -> None:
        """Stamp last_login = now."""
        UserRepository.update(user_id, last_login=datetime.now(UTC))

    @staticmethod
    def deactivate(user_id: str) -> bool:
        """Soft-delete: mark is_active=False. Returns True if the user existed."""
        result = UserRepository.update(user_id, is_active=False)
        return result is not None

    @staticmethod
    def exists_by_email(email: str) -> bool:
        return UserRepository.get_by_email(email) is not None

    @staticmethod
    def exists_by_username(username: str) -> bool:
        return UserRepository.get_by_username(username) is not None

