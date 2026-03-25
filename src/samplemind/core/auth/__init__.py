"""
SampleMind AI — authentication & authorization layer

Public surface:

    from samplemind.core.auth import (
        create_access_token, create_refresh_token, verify_token,
        hash_password, verify_password,
        get_current_user, get_current_active_user,
        UserRole, Permission, RBACService,
    )
"""

from .api_keys import APIKeyService, APIKeyCreate, APIKeyPermission
from .dependencies import get_current_active_user, get_current_user
from .jwt_handler import configure_jwt, create_access_token, create_refresh_token, verify_token
from .password import hash_password, needs_rehash, verify_password
from .permissions import admin_only, require_permission, require_role
from .rbac import Permission, RBACService, UserRole

__all__ = [
    # JWT
    "configure_jwt",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    # Password
    "hash_password",
    "verify_password",
    "needs_rehash",
    # FastAPI dependencies
    "get_current_user",
    "get_current_active_user",
    # RBAC
    "UserRole",
    "Permission",
    "RBACService",
    "require_permission",
    "require_role",
    "admin_only",
    # API keys
    "APIKeyService",
    "APIKeyCreate",
    "APIKeyPermission",
]

