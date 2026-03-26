"""
tests/test_web.py — Integration tests for the Flask web UI.

Uses an in-memory SQLite database (orm_engine fixture) and the Flask
Application Factory so each test gets a fresh, isolated app instance.

Tests cover:
  - Authentication flows: login, logout, register
  - Protected routes: index redirects unauthenticated users
  - API endpoints: /api/samples, /api/status, /api/tag
  - Audio streaming: /audio/<id> 404 for missing sample
  - HTMX partial: /samples/partial returns HTML fragment
"""

from __future__ import annotations

from flask.testing import FlaskClient
import pytest

from samplemind.core.models.sample import SampleCreate
from samplemind.data.repositories.sample_repository import SampleRepository


@pytest.fixture
def client(orm_engine) -> FlaskClient:
    """Flask test client backed by the in-memory test engine.

    orm_engine has already swapped samplemind.data.orm._engine to the test
    engine, so any init_orm() / before_app_request call in the blueprint
    picks up the in-memory database automatically.
    """
    from samplemind.web.app import create_app

    flask_app = create_app({"TESTING": True, "SECRET_KEY": "test-secret-key"})
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def authed_client(client: FlaskClient, test_user) -> FlaskClient:
    """Flask test client with a pre-populated authenticated session."""
    with client.session_transaction() as sess:
        sess["user_id"] = test_user.user_id
    return client


# ── Login / register / logout ─────────────────────────────────────────────────


def test_login_page_loads(client: FlaskClient) -> None:
    """GET /login returns HTTP 200."""
    r = client.get("/login")
    assert r.status_code == 200


def test_login_success_redirects(client: FlaskClient, test_user) -> None:
    """POST /login with correct credentials redirects to the library index."""
    r = client.post(
        "/login",
        data={"username": "testuser", "password": "Test1234"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    assert "/" in r.headers.get("Location", "")


def test_login_wrong_password_shows_error(client: FlaskClient, test_user) -> None:
    """POST /login with wrong password stays on the login page and shows an error."""
    r = client.post(
        "/login",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert r.status_code == 200
    body = r.data.lower()
    assert b"invalid" in body or b"error" in body


def test_register_page_loads(client: FlaskClient) -> None:
    """GET /register returns HTTP 200."""
    r = client.get("/register")
    assert r.status_code == 200


def test_register_creates_user_and_redirects(client: FlaskClient) -> None:
    """POST /register with valid data creates a user and redirects."""
    r = client.post(
        "/register",
        data={
            "email": "new@example.com",
            "username": "newuser",
            "password": "NewPass123",
            "confirm_password": "NewPass123",
        },
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)


def test_register_duplicate_email_shows_error(client: FlaskClient, test_user) -> None:
    """POST /register with an email that already exists shows an error."""
    r = client.post(
        "/register",
        data={
            "email": "testuser@example.com",  # same as test_user
            "username": "anotheruser",
            "password": "AnotherPass1",
            "confirm_password": "AnotherPass1",
        },
    )
    assert r.status_code == 200
    assert b"already" in r.data.lower() or b"error" in r.data.lower()


def test_logout_clears_session(authed_client: FlaskClient) -> None:
    """GET /logout clears the session and redirects to /login."""
    r = authed_client.get("/logout", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers.get("Location", "")


# ── Protected routes ───────────────────────────────────────────────────────────


def test_index_requires_auth(client: FlaskClient) -> None:
    """GET / redirects unauthenticated users to /login."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 303)
    assert "/login" in r.headers.get("Location", "")


def test_index_loads_when_authenticated(authed_client: FlaskClient) -> None:
    """GET / returns HTTP 200 for authenticated users."""
    r = authed_client.get("/")
    assert r.status_code == 200


# ── JSON API endpoints (no auth required) ─────────────────────────────────────


def test_api_samples_returns_json_array(client: FlaskClient) -> None:
    """GET /api/samples returns a JSON array (may be empty)."""
    r = client.get("/api/samples")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)


def test_api_samples_filters_by_energy(client: FlaskClient) -> None:
    """GET /api/samples?energy=high returns only high-energy samples."""
    SampleRepository.upsert(SampleCreate(filename="a.wav", path="/a", energy="high"))
    SampleRepository.upsert(SampleCreate(filename="b.wav", path="/b", energy="low"))
    r = client.get("/api/samples?energy=high")
    data = r.get_json()
    assert r.status_code == 200
    assert all(s["energy"] == "high" for s in data)


def test_api_status_returns_ok(client: FlaskClient) -> None:
    """GET /api/status returns {"ok": True, "total": <int>}."""
    r = client.get("/api/status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert isinstance(body["total"], int)


def test_api_tag_updates_sample(client: FlaskClient) -> None:
    """POST /api/tag writes genre to the sample row."""
    SampleRepository.upsert(SampleCreate(filename="k.wav", path="/tmp/k.wav"))
    r = client.post("/api/tag", json={"path": "/tmp/k.wav", "genre": "trap"})
    assert r.status_code == 200
    s = SampleRepository.get_by_path("/tmp/k.wav")
    assert s is not None and s.genre == "trap"


def test_api_tag_missing_path_returns_400(client: FlaskClient) -> None:
    """POST /api/tag without a 'path' field returns HTTP 400."""
    r = client.post("/api/tag", json={"genre": "trap"})
    assert r.status_code == 400


def test_api_tag_unknown_path_returns_404(client: FlaskClient) -> None:
    """POST /api/tag for a path that does not exist returns HTTP 404."""
    r = client.post("/api/tag", json={"path": "/does/not/exist.wav", "genre": "trap"})
    assert r.status_code == 404


# ── Audio streaming ────────────────────────────────────────────────────────────


def test_audio_stream_404_for_missing_id(client: FlaskClient) -> None:
    """GET /audio/<id> returns 404 when the sample id does not exist."""
    r = client.get("/audio/999999")
    assert r.status_code == 404


# ── HTMX partial ───────────────────────────────────────────────────────────────


def test_samples_partial_returns_html(client: FlaskClient) -> None:
    """GET /samples/partial returns an HTML fragment (no full page)."""
    SampleRepository.upsert(SampleCreate(filename="loop.wav", path="/loop.wav"))
    r = client.get("/samples/partial")
    assert r.status_code == 200
    assert b"loop.wav" in r.data
    # Partial should NOT contain a full HTML page
    assert b"<!DOCTYPE" not in r.data


def test_samples_partial_filters_by_energy(client: FlaskClient) -> None:
    """GET /samples/partial?energy=high returns only high-energy samples."""
    SampleRepository.upsert(SampleCreate(filename="hi.wav", path="/hi.wav", energy="high"))
    SampleRepository.upsert(SampleCreate(filename="lo.wav", path="/lo.wav", energy="low"))
    r = client.get("/samples/partial?energy=high")
    assert r.status_code == 200
    assert b"hi.wav" in r.data
    assert b"lo.wav" not in r.data


# ── /api/export-to-fl ─────────────────────────────────────────────────────────


def test_export_to_fl_requires_auth(client: FlaskClient) -> None:
    """POST /api/export-to-fl redirects unauthenticated users to /login."""
    r = client.post("/api/export-to-fl", json={}, follow_redirects=False)
    assert r.status_code in (302, 303)


def test_export_to_fl_returns_ok(
    authed_client: FlaskClient,
    tmp_path,
    silent_wav,
) -> None:
    """POST /api/export-to-fl copies matching samples and returns ok + counts."""
    from unittest.mock import patch as _patch

    from samplemind.core.models.sample import SampleCreate
    from samplemind.data.repositories.sample_repository import SampleRepository

    SampleRepository.upsert(
        SampleCreate(filename="kick.wav", path=str(silent_wav), energy="high")
    )

    dest = tmp_path / "fl_out"
    with _patch(
        "samplemind.integrations.filesystem.export_to_fl_studio",
        return_value={"copied": 1, "skipped": 0, "targets": 1},
    ) as mock_export:
        r = authed_client.post(
            "/api/export-to-fl",
            json={"energy": "high", "dest": str(dest)},
        )

    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert body["copied"] == 1
    assert body["skipped"] == 0
    mock_export.assert_called_once()


def test_export_to_fl_no_fl_installed_returns_500(
    authed_client: FlaskClient,
) -> None:
    """POST /api/export-to-fl returns 500 when no FL Studio is found."""
    from unittest.mock import patch as _patch

    with _patch(
        "samplemind.integrations.filesystem.export_to_fl_studio",
        side_effect=RuntimeError("No FL Studio installation detected."),
    ):
        r = authed_client.post("/api/export-to-fl", json={})

    assert r.status_code == 500
    assert "No FL Studio" in r.get_json()["error"]
