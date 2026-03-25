"""
database.py — SQLite storage for SampleMind AI

Manages ~/.samplemind/library.db — a single file, no server needed.
Each row = one sample with auto-detected + manually tagged metadata.

Migration strategy: _migrate() adds new columns to existing databases
so users don't lose their library when the schema evolves.
"""

import os
import sqlite3

DB_PATH = os.path.expanduser("~/.samplemind/library.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["bpm"] works
    return conn


def _migrate(conn: sqlite3.Connection):
    """
    Add columns that didn't exist in older versions of the schema.
    ALTER TABLE ADD COLUMN is safe to run repeatedly — it silently fails
    if the column already exists (we catch that specific error).
    """
    new_columns = [
        ("genre",      "TEXT"),
        ("energy",     "TEXT"),   # low / mid / high
        ("tags",       "TEXT"),   # comma-separated free-form tags
        ("instrument", "TEXT"),   # kick / snare / hihat / bass / pad / lead / loop / sfx
    ]
    for col_name, col_type in new_columns:
        try:
            conn.execute(f"ALTER TABLE samples ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass  # column already exists — that's fine


def init_db():
    """Create the samples table (if needed) and apply any migrations."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS samples (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                path        TEXT NOT NULL UNIQUE,
                bpm         REAL,
                key         TEXT,
                mood        TEXT,
                genre       TEXT,
                energy      TEXT,
                tags        TEXT,
                imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        _migrate(conn)


def save_sample(filename: str, path: str, bpm: float, key: str,
                mood: str = None, energy: str = None, instrument: str = None):
    """Insert or update a sample. Re-importing the same path updates auto-detected fields."""
    with _connect() as conn:
        conn.execute("""
            INSERT INTO samples (filename, path, bpm, key, mood, energy, instrument)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                bpm        = excluded.bpm,
                key        = excluded.key,
                mood       = excluded.mood,
                energy     = excluded.energy,
                instrument = excluded.instrument
        """, (filename, path, bpm, key, mood, energy, instrument))


def tag_sample(path: str, genre: str = None, mood: str = None,
               energy: str = None, tags: str = None) -> bool:
    """
    Update the manual tags on a sample by its file path.
    Only updates fields that are explicitly passed (None = leave unchanged).
    Returns True if the sample was found, False if not in the library.
    """
    fields, params = [], []
    if genre  is not None: fields.append("genre = ?");  params.append(genre)
    if mood   is not None: fields.append("mood = ?");   params.append(mood)
    if energy is not None: fields.append("energy = ?"); params.append(energy)
    if tags   is not None: fields.append("tags = ?");   params.append(tags)

    if not fields:
        return False

    params.append(path)
    with _connect() as conn:
        cur = conn.execute(
            f"UPDATE samples SET {', '.join(fields)} WHERE path = ?", params
        )
        return cur.rowcount > 0


def get_sample_by_name(name: str):
    """Find a sample by partial filename match (case-insensitive)."""
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM samples WHERE filename LIKE ? LIMIT 1",
            (f"%{name}%",)
        ).fetchone()


def search_samples(query: str = None, bpm_min=None, bpm_max=None,
                   key=None, genre=None, energy=None, instrument=None):
    """
    Full search with all filters combined.
    query = partial filename or tag match.
    """
    sql = "SELECT * FROM samples WHERE 1=1"
    params = []

    if query:
        sql += " AND (filename LIKE ? OR tags LIKE ?)"
        params += [f"%{query}%", f"%{query}%"]
    if bpm_min  is not None: sql += " AND bpm >= ?";        params.append(bpm_min)
    if bpm_max  is not None: sql += " AND bpm <= ?";        params.append(bpm_max)
    if key      is not None: sql += " AND key LIKE ?";      params.append(f"%{key}%")
    if genre      is not None: sql += " AND genre LIKE ?";      params.append(f"%{genre}%")
    if energy     is not None: sql += " AND energy = ?";        params.append(energy)
    if instrument is not None: sql += " AND instrument LIKE ?"; params.append(f"%{instrument}%")

    sql += " ORDER BY imported_at DESC"

    with _connect() as conn:
        return conn.execute(sql, params).fetchall()


def get_all_samples(bpm_min=None, bpm_max=None, key=None):
    return search_samples(bpm_min=bpm_min, bpm_max=bpm_max, key=key)


def count_samples() -> int:
    with _connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
