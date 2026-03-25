"""
core/models/user.py — SQLModel User table + Pydantic request/response schemas

The ``User`` class is both an ORM table (SQLModel) and a Pydantic model.
Pydantic-only schemas (UserCreate, UserPublic, etc.) are defined below it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlmodel import Column, DateTime, Field as SMField, SQLModel
import re


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


# ── ORM table ──────────────────────────────────────────────────────────────────


class User(SQLModel, table=True):
    """Users table — stores credentials and profile data."""

    __tablename__ = "users"

    id: Optional[int] = SMField(default=None, primary_key=True)
    user_id: str = SMField(default_factory=_new_uuid, unique=True, index=True)
    email: str = SMField(unique=True, index=True)
    username: str = SMField(unique=True, index=True)
    hashed_password: str
    role: str = SMField(default="owner")  # UserRole value
    is_active: bool = SMField(default=True)
    is_verified: bool = SMField(default=False)
    created_at: datetime = SMField(
        default_factory=_now,
        sa_column=Column(DateTime, default=_now),
    )
    updated_at: datetime = SMField(
        default_factory=_now,
        sa_column=Column(DateTime, default=_now, onupdate=_now),
    )
    last_login: Optional[datetime] = SMField(default=None)

    # Usage stats
    total_analyses: int = SMField(default=0)


# ── Pydantic request schemas ───────────────────────────────────────────────────


class UserCreate(BaseModel):
    """Registration payload."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9_]+", v):
            raise ValueError("Username may only contain letters, digits, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Profile update payload (all fields optional)."""

    username: Optional[str] = Field(None, min_length=3, max_length=50)

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.fullmatch(r"[a-zA-Z0-9_]+", v):
            raise ValueError("Username may only contain letters, digits, and underscores")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ── Pydantic response schemas ──────────────────────────────────────────────────


class UserPublic(BaseModel):
    """Safe public representation of a user (no password hash)."""

    user_id: str
    email: str
    username: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    total_analyses: int = 0

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Seconds until access token expires")


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str

