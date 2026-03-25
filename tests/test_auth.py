"""
tests/test_auth.py — unit tests for the auth system (Phase 3)

Covers:
- Password hashing and verification (passlib/bcrypt)
- JWT creation, verification, and expiry
- RBAC role/permission checks
- UserRepository CRUD against an in-memory SQLite ORM engine
- FastAPI auth routes (register, login, refresh, me, change-password)

All database access uses the ``orm_engine`` / ``test_user`` fixtures from
conftest.py — no on-disk files are touched.
"""

from __future__ import annotations

from datetime import timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

# ── Password ──────────────────────────────────────────────────────────────────


def test_hash_and_verify():
    from samplemind.core.auth import hash_password, verify_password

    hashed = hash_password("Test1234")
    assert hashed != "Test1234"
    assert verify_password("Test1234", hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_needs_rehash_is_false_for_fresh_hash():
    from samplemind.core.auth import hash_password
    from samplemind.core.auth.password import needs_rehash

    hashed = hash_password("Test1234")
    assert needs_rehash(hashed) is False


# ── JWT ───────────────────────────────────────────────────────────────────────


def test_create_and_verify_access_token():
    from samplemind.core.auth import create_access_token, verify_token

    token = create_access_token("user-id-123", "user@example.com")
    assert isinstance(token, str)
    assert len(token) > 20

    user_id = verify_token(token, token_type="access")
    assert user_id == "user-id-123"


def test_create_and_verify_refresh_token():
    from samplemind.core.auth import create_refresh_token, verify_token

    token = create_refresh_token("user-id-456")
    user_id = verify_token(token, token_type="refresh")
    assert user_id == "user-id-456"


def test_token_type_mismatch_rejected():
    from samplemind.core.auth import create_access_token, verify_token

    access = create_access_token("uid", "u@x.com")
    # Trying to use an access token as a refresh token must fail
    assert verify_token(access, token_type="refresh") is None


def test_expired_token_rejected():
    from samplemind.core.auth import create_access_token, verify_token

    expired = create_access_token("uid", "u@x.com", expires_delta=timedelta(seconds=-1))
    assert verify_token(expired) is None


def test_tampered_token_rejected():
    from samplemind.core.auth import verify_token

    assert verify_token("this.is.not.a.valid.jwt") is None


# ── RBAC ──────────────────────────────────────────────────────────────────────


def test_owner_has_audio_write():
    from samplemind.core.auth.rbac import Permission, RBACService, UserRole

    assert RBACService.has_permission(UserRole.OWNER, Permission.AUDIO_WRITE) is True


def test_viewer_lacks_audio_write():
    from samplemind.core.auth.rbac import Permission, RBACService, UserRole

    assert RBACService.has_permission(UserRole.VIEWER, Permission.AUDIO_WRITE) is False


def test_admin_has_all_permissions():
    from samplemind.core.auth.rbac import Permission, RBACService, UserRole

    for perm in Permission:
        assert RBACService.has_permission(UserRole.ADMIN, perm) is True


def test_meets_minimum_role():
    from samplemind.core.auth.rbac import RBACService, UserRole

    assert RBACService.meets_minimum_role(UserRole.ADMIN, UserRole.OWNER) is True
    assert RBACService.meets_minimum_role(UserRole.VIEWER, UserRole.OWNER) is False


# ── UserRepository ────────────────────────────────────────────────────────────


def test_create_and_retrieve_user(orm_engine):
    from samplemind.core.auth import hash_password
    from samplemind.data.repositories.user_repository import UserRepository

    user = UserRepository.create(
        email="alice@example.com",
        username="alice",
        hashed_password=hash_password("Alice1234"),
    )
    assert user.user_id is not None

    fetched = UserRepository.get_by_email("alice@example.com")
    assert fetched is not None
    assert fetched.username == "alice"


def test_email_uniqueness(orm_engine):
    from samplemind.core.auth import hash_password
    from samplemind.data.repositories.user_repository import UserRepository

    UserRepository.create(
        email="bob@example.com",
        username="bob",
        hashed_password=hash_password("Bob12345"),
    )
    assert UserRepository.exists_by_email("bob@example.com") is True
    assert UserRepository.exists_by_email("unknown@example.com") is False


def test_get_by_id(test_user):
    from samplemind.data.repositories.user_repository import UserRepository

    found = UserRepository.get_by_id(test_user.user_id)
    assert found is not None
    assert found.email == test_user.email


def test_update_username(test_user):
    from samplemind.data.repositories.user_repository import UserRepository

    updated = UserRepository.update(test_user.user_id, username="newname")
    assert updated is not None
    assert updated.username == "newname"


def test_record_login(test_user):
    from samplemind.data.repositories.user_repository import UserRepository

    assert test_user.last_login is None
    UserRepository.record_login(test_user.user_id)
    refreshed = UserRepository.get_by_id(test_user.user_id)
    assert refreshed.last_login is not None


# ── FastAPI routes ────────────────────────────────────────────────────────────


@pytest.fixture
def api_client(orm_engine):
    """
    Sync TestClient for the FastAPI app, using the in-memory ORM engine.

    The FastAPI lifespan is replaced with a no-op so it doesn't call
    init_orm() (which would create a new engine pointing at the real DB).
    The orm_engine fixture has already created the tables in memory and
    patched get_engine() to return that engine.
    """
    from contextlib import asynccontextmanager

    from fastapi import FastAPI

    from samplemind.api import __version__
    from samplemind.api.routes import auth as auth_router
    from fastapi.middleware.cors import CORSMiddleware

    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        # Tables already exist in the in-memory engine from the orm_engine fixture.
        yield

    test_app = FastAPI(
        title="SampleMind AI API (test)",
        version=__version__,
        lifespan=noop_lifespan,
        docs_url=None,
        redoc_url=None,
    )
    test_app.include_router(auth_router.router, prefix="/api/v1")

    with TestClient(test_app, raise_server_exceptions=True) as client:
        yield client


def test_register_success(api_client):
    resp = api_client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "username": "newuser", "password": "NewPass1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body


def test_register_duplicate_email(api_client, test_user):
    resp = api_client.post(
        "/api/v1/auth/register",
        json={"email": test_user.email, "username": "other", "password": "Other123"},
    )
    assert resp.status_code == 400


def test_login_success(api_client, test_user):
    resp = api_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Test1234"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(api_client, test_user):
    resp = api_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "WrongPass1"},
    )
    assert resp.status_code == 401


def test_me_authenticated(api_client, auth_headers):
    resp = api_client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "testuser@example.com"


def test_me_unauthenticated(api_client):
    resp = api_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_refresh_token(api_client, test_user):
    from samplemind.core.auth import create_refresh_token

    refresh = create_refresh_token(test_user.user_id)
    resp = api_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_change_password(api_client, auth_headers, test_user):
    resp = api_client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Test1234", "new_password": "NewPass99"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    # Old password no longer works
    login_resp = api_client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Test1234"},
    )
    assert login_resp.status_code == 401

