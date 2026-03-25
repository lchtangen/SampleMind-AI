"""
core/auth/permissions.py — FastAPI permission-checking dependencies

Use these with ``Depends(...)`` to enforce RBAC on individual routes.

Example::

    @router.delete("/samples/{id}")
    async def delete_sample(
        sample_id: int,
        user = Depends(require_permission(Permission.AUDIO_DELETE)),
    ):
        ...
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from .dependencies import get_current_active_user
from .rbac import Permission, RBACService, UserRole


def require_permission(permission: Permission):
    """Return a FastAPI dependency that checks for a single permission."""

    async def _check(current_user=Depends(get_current_active_user)):
        role = UserRole(getattr(current_user, "role", "member"))
        if not RBACService.has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}",
            )
        return current_user

    return _check


def require_any_permission(*permissions: Permission):
    """Return a dependency that passes if the user has ANY of the given permissions."""

    async def _check(current_user=Depends(get_current_active_user)):
        role = UserRole(getattr(current_user, "role", "member"))
        if not RBACService.has_any(role, *permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {[p.value for p in permissions]}",
            )
        return current_user

    return _check


def require_role(minimum: UserRole):
    """Return a dependency that passes if the user meets the minimum role tier."""

    async def _check(current_user=Depends(get_current_active_user)):
        role = UserRole(getattr(current_user, "role", "member"))
        if not RBACService.meets_minimum_role(role, minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{minimum.value}' or higher required",
            )
        return current_user

    return _check


def admin_only():
    """Shortcut dependency for admin-only routes."""
    return require_role(UserRole.ADMIN)

