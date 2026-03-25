"""
core/auth/jwt_handler.py — JWT token creation and verification

Uses python-jose with HS256. Config is seeded from Settings on first import
and can be overridden at runtime via configure_jwt() (called from FastAPI lifespan).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

logger = logging.getLogger(__name__)

# ── Runtime-configurable JWT settings ─────────────────────────────────────────


class _JWTConfig:
    """Mutable JWT configuration — initialised from Settings, overridable."""

    def __init__(self) -> None:
        from samplemind.core.config import get_settings

        s = get_settings()
        self.SECRET_KEY: str = s.SECRET_KEY
        self.ALGORITHM: str = s.ALGORITHM
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = s.ACCESS_TOKEN_EXPIRE_MINUTES
        self.REFRESH_TOKEN_EXPIRE_DAYS: int = s.REFRESH_TOKEN_EXPIRE_DAYS


_cfg = _JWTConfig()


def configure_jwt(
    *,
    secret_key: str,
    algorithm: str = "HS256",
    access_expire_minutes: int = 30,
    refresh_expire_days: int = 7,
) -> None:
    """Override JWT settings at runtime (called from FastAPI lifespan)."""
    _cfg.SECRET_KEY = secret_key
    _cfg.ALGORITHM = algorithm
    _cfg.ACCESS_TOKEN_EXPIRE_MINUTES = access_expire_minutes
    _cfg.REFRESH_TOKEN_EXPIRE_DAYS = refresh_expire_days


# ── Token creation ─────────────────────────────────────────────────────────────


def create_access_token(
    user_id: str,
    email: str,
    additional_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=_cfg.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "iat": datetime.now(UTC),
        "exp": expire,
    }
    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(payload, _cfg.SECRET_KEY, algorithm=_cfg.ALGORITHM)
    logger.debug("Created access token for user %s", user_id)
    return token


def create_refresh_token(
    user_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token (no email claim — smaller payload)."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=_cfg.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "iat": datetime.now(UTC),
        "exp": expire,
    }
    token = jwt.encode(payload, _cfg.SECRET_KEY, algorithm=_cfg.ALGORITHM)
    logger.debug("Created refresh token for user %s", user_id)
    return token


# ── Token verification ────────────────────────────────────────────────────────


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT; return payload or None on failure."""
    try:
        return jwt.decode(token, _cfg.SECRET_KEY, algorithms=[_cfg.ALGORITHM])
    except JWTError as exc:
        logger.warning("Token decode failed: %s", exc)
        return None


def verify_token(token: str, *, token_type: str = "access") -> str | None:
    """
    Verify token signature, expiry, and type.

    Returns the user_id (``sub`` claim) on success, ``None`` on failure.
    """
    payload = decode_token(token)
    if payload is None:
        return None

    user_id: str | None = payload.get("sub")
    if not user_id:
        logger.warning("Token missing sub claim")
        return None

    if payload.get("type") != token_type:
        logger.warning(
            "Token type mismatch: expected=%s got=%s", token_type, payload.get("type")
        )
        return None

    logger.debug("Token verified for user %s", user_id)
    return user_id

