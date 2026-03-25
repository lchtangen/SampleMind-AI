"""
core/auth/password.py — bcrypt password hashing

Uses the ``bcrypt`` library directly (no passlib wrapper) to avoid the
passlib 1.7.x / bcrypt 4.x incompatibility where passlib cannot read the
bcrypt version number via the removed ``__about__`` attribute.

Cost factor: 12 rounds (≈ 250 ms on modern hardware — good balance for a
desktop single-user app).  Increase to 13–14 for a server deployment.
"""

from __future__ import annotations

import logging

import bcrypt

logger = logging.getLogger(__name__)

_BCRYPT_ROUNDS: int = 12


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plain-text password."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    logger.debug("Password hashed successfully")
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if plain_password matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error verifying password: %s", exc)
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Return True if the stored hash was created with a lower cost factor
    than the current ``_BCRYPT_ROUNDS`` setting.

    bcrypt hashes are in the form ``$2b$NN$<22-char-salt><31-char-hash>``
    where NN is the cost factor (zero-padded decimal string).

    Call this after a successful ``verify_password()`` and re-hash if True.
    """
    try:
        # Split on '$': ['', '2b', 'NN', '<salt+hash>']
        parts = hashed_password.split("$")
        current_rounds = int(parts[2])
        return current_rounds < _BCRYPT_ROUNDS
    except Exception:  # noqa: BLE001
        return False

