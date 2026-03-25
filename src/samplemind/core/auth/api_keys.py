"""
core/auth/api_keys.py — API key generation and validation

Generates opaque API keys prefixed with ``sm_live_`` / ``sm_test_``.
Keys are stored as SHA-256 hashes — the plain key is shown only once at creation.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class APIKeyEnv(str, Enum):
    """Environment tag embedded in the key prefix."""

    PRODUCTION = "sm_live_"
    DEVELOPMENT = "sm_test_"


class APIKeyPermission(str, Enum):
    """Coarse permissions for API key access."""

    READ = "audio:read"
    WRITE = "audio:write"
    ANALYZE = "audio:analyze"
    SEARCH = "search:all"
    ADMIN = "admin:all"


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class APIKeyCreate(BaseModel):
    name: str
    permissions: list[APIKeyPermission]
    expires_in_days: Optional[int] = None
    description: Optional[str] = None
    environment: str = "production"


class APIKeyResponse(BaseModel):
    """Returned only at creation — contains the plain key (shown once)."""

    key_id: str
    key: str
    prefix: str
    name: str
    permissions: list[APIKeyPermission]
    created_at: datetime
    expires_at: Optional[datetime]
    warning: str = "Store this key securely. It will not be shown again."


class APIKeyPublic(BaseModel):
    """Safe representation — no sensitive data."""

    key_id: str
    name: str
    prefix: str
    permissions: list[APIKeyPermission]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    is_active: bool
    usage_count: int


# ── Key service ────────────────────────────────────────────────────────────────


class APIKeyService:
    """Static helpers for API key lifecycle management."""

    @staticmethod
    def generate(env: APIKeyEnv = APIKeyEnv.PRODUCTION) -> tuple[str, str]:
        """
        Generate a (plain_key, key_hash) pair.

        Store only the hash; return the plain key to the caller once.
        """
        secret = secrets.token_urlsafe(32)
        full_key = f"{env.value}{secret}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        return full_key, key_hash

    @staticmethod
    def hash(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def verify(provided_key: str, stored_hash: str) -> bool:
        """Constant-time comparison to prevent timing attacks."""
        return secrets.compare_digest(APIKeyService.hash(provided_key), stored_hash)

    @staticmethod
    def create(user_id: str, params: APIKeyCreate) -> APIKeyResponse:
        """Build an APIKeyResponse (does NOT persist to DB — caller must do that)."""
        env = APIKeyEnv.PRODUCTION if params.environment != "development" else APIKeyEnv.DEVELOPMENT
        full_key, _ = APIKeyService.generate(env)
        key_id = f"key_{secrets.token_urlsafe(16)}"
        expires_at = (
            datetime.utcnow() + timedelta(days=params.expires_in_days)
            if params.expires_in_days
            else None
        )
        return APIKeyResponse(
            key_id=key_id,
            key=full_key,
            prefix=full_key[:16],
            name=params.name,
            permissions=params.permissions,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )

