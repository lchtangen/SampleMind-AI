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

from .api_keys import APIKeyCreate, APIKeyPermission, APIKeyService
from .dependencies import get_current_active_user, get_current_user
from .jwt_handler import (
    configure_jwt,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from .password import hash_password, needs_rehash, verify_password
from .permissions import admin_only, require_permission, require_role
from .rbac import Permission, RBACService, UserRole

__all__ = [
    "APIKeyCreate",
    "APIKeyPermission",
    "APIKeyService",
    "Permission",
    "RBACService",
    "UserRole",
    "admin_only",
    "configure_jwt",
    "create_access_token",
    "create_refresh_token",
    "get_current_active_user",
    "get_current_user",
    "hash_password",
    "needs_rehash",
    "require_permission",
    "require_role",
    "verify_password",
    "verify_token",
]
