"""
api/routes/auth.py — Authentication REST endpoints

All routes are mounted under /api/v1/auth by the FastAPI app.

Endpoints:
  POST /register       — create account
  POST /login          — issue JWT pair (OAuth2PasswordRequestForm compatible)
  POST /refresh        — exchange refresh token for new access token
  POST /logout         — client-side hint (stateless JWT; no server state)
  GET  /me             — get current user profile
  PUT  /me             — update username
  POST /change-password — change password
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from samplemind.core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    hash_password,
    verify_password,
    verify_token,
)
from samplemind.core.models.user import (
    ChangePasswordRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserPublic,
    UserUpdate,
)
from samplemind.data.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

_ACCESS_TTL_SECONDS = 30 * 60  # 30 minutes


# ── Registration ──────────────────────────────────────────────────────────────


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate):
    """
    Create a new user account.

    - **email**: unique, valid email address
    - **username**: 3–50 characters, letters/digits/underscores only
    - **password**: ≥8 chars, at least one upper, lower, and digit
    """
    if UserRepository.exists_by_email(body.email):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    if UserRepository.exists_by_username(body.username):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")

    user = UserRepository.create(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
    )
    logger.info("New user registered: %s", user.email)
    return UserPublic.model_validate(user)


# ── Login ─────────────────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate and receive JWT access + refresh tokens.

    ``username`` field accepts either an email address or a username.
    This endpoint is fully compatible with the OAuth2 password flow.
    """
    # Try email first, fall back to username
    user = UserRepository.get_by_email(form.username) or UserRepository.get_by_username(
        form.username
    )

    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")

    UserRepository.record_login(user.user_id)
    access = create_access_token(user.user_id, user.email)
    refresh = create_refresh_token(user.user_id)

    logger.info("User logged in: %s", user.email)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=_ACCESS_TTL_SECONDS,
    )


# ── Token refresh ─────────────────────────────────────────────────────────────


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    user_id = verify_token(body.refresh_token, token_type="refresh")
    if not user_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = UserRepository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")

    access = create_access_token(user.user_id, user.email)
    new_refresh = create_refresh_token(user.user_id)
    return TokenResponse(access_token=access, refresh_token=new_refresh, expires_in=_ACCESS_TTL_SECONDS)


# ── Logout ────────────────────────────────────────────────────────────────────


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user=Depends(get_current_active_user)):
    """
    Signal logout (stateless — client must discard the tokens).

    A future enhancement may maintain a server-side token blocklist.
    """
    logger.info("User logged out: %s", current_user.email)
    return MessageResponse(message="Logged out successfully")


# ── Profile ───────────────────────────────────────────────────────────────────


@router.get("/me", response_model=UserPublic)
async def me(current_user=Depends(get_current_active_user)):
    """Return the authenticated user's profile."""
    return UserPublic.model_validate(current_user)


@router.put("/me", response_model=UserPublic)
async def update_profile(body: UserUpdate, current_user=Depends(get_current_active_user)):
    """Update the authenticated user's profile (username only for now)."""
    if body.username:
        conflict = UserRepository.get_by_username(body.username)
        if conflict and conflict.user_id != current_user.user_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already taken")

    updated = UserRepository.update(current_user.user_id, **body.model_dump(exclude_none=True))
    return UserPublic.model_validate(updated)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest, current_user=Depends(get_current_active_user)
):
    """Change the authenticated user's password."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect current password")

    UserRepository.update(current_user.user_id, hashed_password=hash_password(body.new_password))
    logger.info("Password changed for user: %s", current_user.email)
    return MessageResponse(message="Password changed successfully")

