"""
core/auth/dependencies.py — FastAPI authentication dependencies

OAuth2PasswordBearer + user retrieval from SQLite via UserRepository.
Import these with ``Depends(...)`` in FastAPI route handlers.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .jwt_handler import verify_token

logger = logging.getLogger(__name__)

# Points to the FastAPI auth login endpoint (used by OpenAPI docs)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="JWT")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    FastAPI dependency: decode the Bearer JWT and return the User ORM object.

    Raises 401 if the token is missing, invalid, or the user no longer exists.
    """
    from samplemind.data.repositories.user_repository import UserRepository

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_token(token, token_type="access")
    if not user_id:
        logger.warning("Invalid or expired access token")
        raise credentials_exc

    user = UserRepository.get_by_id(user_id)
    if user is None:
        logger.warning("Token references unknown user_id=%s", user_id)
        raise credentials_exc

    logger.debug("Authenticated user: %s", user.email)
    return user


async def get_current_active_user(user=Depends(get_current_user)):
    """
    FastAPI dependency: get the current user and assert they are active.

    Raises 403 if the account is deactivated.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return user


# ── Convenience type aliases ──────────────────────────────────────────────────
CurrentUser = Annotated[object, Depends(get_current_active_user)]

