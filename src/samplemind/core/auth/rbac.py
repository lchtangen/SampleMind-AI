"""
core/auth/rbac.py — Role-Based Access Control

Defines UserRole hierarchy and Permission enum.
SampleMind-AI is a single-user desktop app so the default role is OWNER;
the RBAC layer exists to support future multi-user / cloud deployments.
"""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar


class UserRole(StrEnum):
    """User role tier — controls feature access."""

    VIEWER = "viewer"  # Read-only access (shared library view)
    MEMBER = "member"  # Standard single user
    OWNER = "owner"  # Full local library access
    ADMIN = "admin"  # Administrative operations


class Permission(StrEnum):
    """Granular permission flags."""

    # Audio library
    AUDIO_READ = "audio:read"
    AUDIO_WRITE = "audio:write"
    AUDIO_DELETE = "audio:delete"
    AUDIO_ANALYZE = "audio:analyze"
    AUDIO_BATCH = "audio:batch"

    # Search
    SEARCH_BASIC = "search:basic"
    SEARCH_ADVANCED = "search:advanced"

    # Sample packs
    PACK_CREATE = "pack:create"
    PACK_EXPORT = "pack:export"

    # API keys
    API_KEY_CREATE = "api:key_create"
    API_KEY_REVOKE = "api:key_revoke"

    # Admin
    ADMIN_USER_MANAGE = "admin:user_manage"
    ADMIN_SYSTEM = "admin:system"


# ── Role → permission mapping ──────────────────────────────────────────────────

_VIEWER_PERMS: frozenset[Permission] = frozenset(
    {
        Permission.AUDIO_READ,
        Permission.SEARCH_BASIC,
    }
)

_MEMBER_PERMS: frozenset[Permission] = _VIEWER_PERMS | frozenset(
    {
        Permission.AUDIO_WRITE,
        Permission.AUDIO_DELETE,
        Permission.AUDIO_ANALYZE,
        Permission.AUDIO_BATCH,
        Permission.SEARCH_ADVANCED,
        Permission.PACK_CREATE,
        Permission.PACK_EXPORT,
        Permission.API_KEY_CREATE,
    }
)

_OWNER_PERMS: frozenset[Permission] = _MEMBER_PERMS | frozenset(
    {
        Permission.API_KEY_REVOKE,
    }
)

_ADMIN_PERMS: frozenset[Permission] = frozenset(Permission)

ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.VIEWER: _VIEWER_PERMS,
    UserRole.MEMBER: _MEMBER_PERMS,
    UserRole.OWNER: _OWNER_PERMS,
    UserRole.ADMIN: _ADMIN_PERMS,
}

_ROLE_RANK: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.MEMBER: 1,
    UserRole.OWNER: 2,
    UserRole.ADMIN: 3,
}


class RBACService:
    """Static helpers for permission and role checks."""

    _rank: ClassVar[dict[UserRole, int]] = _ROLE_RANK

    @staticmethod
    def get_permissions(role: UserRole) -> frozenset[Permission]:
        return ROLE_PERMISSIONS.get(role, frozenset())

    @staticmethod
    def has_permission(role: UserRole, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(role, frozenset())

    @staticmethod
    def has_any(role: UserRole, *permissions: Permission) -> bool:
        role_perms = ROLE_PERMISSIONS.get(role, frozenset())
        return any(p in role_perms for p in permissions)

    @staticmethod
    def has_all(role: UserRole, *permissions: Permission) -> bool:
        role_perms = ROLE_PERMISSIONS.get(role, frozenset())
        return all(p in role_perms for p in permissions)

    @classmethod
    def meets_minimum_role(cls, role: UserRole, minimum: UserRole) -> bool:
        return cls._rank.get(role, 0) >= cls._rank.get(minimum, 0)
