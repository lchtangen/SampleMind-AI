"""
database.py — SQLite storage for SampleMind AI

This module manages a local database file (~/.samplemind/library.db).
It stores one row per sample with its metadata: file path, BPM, key, mood.

sqlite3 is part of Python's standard library — no installation needed.
"""

import sqlite3
import os

# The database lives in the user's home directory so it persists across
# different project folders and terminal sessions.
DB_PATH = os.path.expanduser("~/.samplemind/library.db")


def _connect() -> sqlite3.Connection:
    """Open (or create) the database file and return a connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["bpm"] works
    return conn


def init_db():
    """Create the samples table if it doesn't exist yet."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS samples (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                filename  TEXT NOT NULL,
                path      TEXT NOT NULL UNIQUE,
                bpm       REAL,
                key       TEXT,
                mood      TEXT,
                imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_sample(filename: str, path: str, bpm: float, key: str, mood: str = None):
    """
    Insert a sample into the database.
    INSERT OR REPLACE means re-importing the same file updates its metadata
    instead of creating a duplicate row.
    """
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO samples (filename, path, bpm, key, mood)
            VALUES (?, ?, ?, ?, ?)
        """, (filename, path, bpm, key, mood))


def get_all_samples(bpm_min=None, bpm_max=None, key=None):
    """
    Query all samples, with optional filters.
    The ? placeholders protect against SQL injection — never use f-strings for SQL.
    """
    query = "SELECT * FROM samples WHERE 1=1"
    params = []

    if bpm_min is not None:
        query += " AND bpm >= ?"
        params.append(bpm_min)
    if bpm_max is not None:
        query += " AND bpm <= ?"
        params.append(bpm_max)
    if key is not None:
        query += " AND key LIKE ?"
        params.append(f"%{key}%")

    query += " ORDER BY imported_at DESC"

    with _connect() as conn:
        return conn.execute(query, params).fetchall()


def count_samples() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
