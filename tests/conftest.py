from pathlib import Path
import sqlite3

import numpy as np
import pytest
import soundfile as sf
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# ── --slow CLI flag ──────────────────────────────────────────────────────────
# Allows: ``pytest --slow`` to include slow tests while the default
# addopts = "-m 'not slow'" skips them for fast interactive runs.


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Also run tests marked @pytest.mark.slow (disabled by default).",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--slow"):
        # Remove the 'not slow' marker expression injected by addopts
        # so that slow tests run alongside fast ones.
        for item in items:
            item.own_markers  # ensure markers are loaded
        config.option.markexpr = ""


# ── Eager imports to prevent C-extension double-load on Python 3.13 ──────────
# Python 3.13 is stricter about C extensions: a .so loaded twice in the same
# process raises "cannot load module more than once per process".
# librosa and scipy use lazy_loader, which can trigger re-imports of already-
# loaded C extensions (numpy.fft._pocketfft_umath, scipy.signal, etc.) if the
# first import of the top-level package doesn't pull them in.
# Pre-importing the full chain here — before any test module imports — ensures
# every C extension is loaded exactly once, into the correct module namespace.
#
# Also fixes: numba 0.64 lazily initialises PyYAML, causing
#   AttributeError: partially initialized module 'yaml'
# when multiple test modules trigger numba initialisation in close succession.
try:
    import numba  # noqa: F401 — forces yaml to be fully initialised
    import numpy.fft  # noqa: F401 — loads _pocketfft_umath C ext once
    import scipy.signal  # noqa: F401 — loads scipy C exts before lazy_loader can
    import librosa  # noqa: F401 — resolves lazy submodule chain up front
    # Warm up the most commonly used lazy submodules that trigger the issue
    import librosa.core.audio  # noqa: F401
    import librosa.feature  # noqa: F401
except ImportError:
    pass  # optional deps; tests that need them will skip or fail on their own

# ── Audio fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def silent_wav(tmp_path: Path) -> Path:
    path = tmp_path / "test.wav"
    sf.write(str(path), np.zeros(22050, dtype=np.float32), 22050)
    return path


@pytest.fixture
def kick_wav(tmp_path: Path) -> Path:
    """Simulated kick: loud, low-frequency sine burst (60 Hz, 0.5 s)."""
    t = np.linspace(0, 0.5, int(22050 * 0.5), dtype=np.float32)
    samples = (0.9 * np.sin(2 * np.pi * 60 * t)).astype(np.float32)
    path = tmp_path / "kick.wav"
    sf.write(str(path), samples, 22050)
    return path


@pytest.fixture
def hihat_wav(tmp_path: Path) -> Path:
    """Simulated hihat: white noise burst (0.1 s)."""
    rng = np.random.default_rng(seed=42)
    samples = rng.uniform(-0.3, 0.3, 2205).astype(np.float32)
    path = tmp_path / "hihat.wav"
    sf.write(str(path), samples, 22050)
    return path


# ── Legacy sqlite3 database fixture ────────────────────────────────────────────


@pytest.fixture
def in_memory_db():
    """
    In-memory SQLite connection with the legacy samples schema.
    Matches src/samplemind/data/database.py — use for data-layer unit tests.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE samples (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT NOT NULL,
            path        TEXT UNIQUE NOT NULL,
            bpm         REAL,
            key         TEXT,
            mood        TEXT,
            genre       TEXT,
            energy      TEXT,
            tags        TEXT,
            instrument  TEXT,
            imported_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    yield conn
    conn.close()


# ── SQLModel ORM fixtures (Phase 3: users table) ────────────────────────────────


@pytest.fixture(scope="function")
def orm_engine():
    """
    In-memory SQLite engine with all SQLModel tables created.

    Injects the test engine directly into ``samplemind.data.orm._engine``
    (the module-level cache used by ``get_engine()``) for the duration of
    the test, so that UserRepository and FastAPI routes use this isolated
    engine rather than touching the real on-disk database.
    """
    import samplemind.core.models.user  # noqa: F401  ← registers User in SQLModel.metadata
    import samplemind.data.orm as _orm_mod

    # StaticPool: all sessions share the same single connection.
    # This is required for in-memory SQLite — without it, each new connection
    # gets a fresh empty database, so tables created in one connection are
    # invisible to sessions opened by subsequent requests.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)  # create users (and any other) tables

    # Swap the cached engine out for the test engine
    _original = _orm_mod._engine
    _orm_mod._engine = engine

    yield engine

    # Restore the original engine (None on first test, real engine if run later)
    _orm_mod._engine = _original


@pytest.fixture
def orm_session(orm_engine):
    """Yield a SQLModel Session bound to the test in-memory engine."""
    with Session(orm_engine) as session:
        yield session


@pytest.fixture
def test_user(orm_engine):
    """
    Create and return a test User in the ORM database.

    Password is ``Test1234`` (meets all strength requirements).
    """
    from samplemind.core.auth import hash_password
    from samplemind.data.repositories.user_repository import UserRepository

    return UserRepository.create(
        email="testuser@example.com",
        username="testuser",
        hashed_password=hash_password("Test1234"),
    )


@pytest.fixture
def access_token(test_user):
    """Return a valid JWT access token for the test user."""
    from samplemind.core.auth import create_access_token

    return create_access_token(test_user.user_id, test_user.email)


@pytest.fixture
def auth_headers(access_token):
    """Return HTTP headers dict with Bearer token for use with httpx / test clients."""
    return {"Authorization": f"Bearer {access_token}"}
