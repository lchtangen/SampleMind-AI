"""FTS5 full-text search for samples."""
from __future__ import annotations

import sqlite3

from samplemind.core.config import get_settings


def get_fts_connection() -> sqlite3.Connection:
    """Get SQLite connection for FTS5 queries."""
    settings = get_settings()
    db_url = settings.database_url
    db_path = db_url.removeprefix("sqlite:///") if db_url.startswith("sqlite:///") else db_url
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def fts_search(query: str, limit: int = 50) -> list[int]:
    """Search samples using FTS5.
    Args:
        query: FTS5 query string (e.g., "dark kick", "trap OR dubstep")
        limit: Maximum results to return
    Returns:
        List of sample IDs matching the query
    """
    conn = get_fts_connection()
    try:
        rows = conn.execute(
            "SELECT rowid FROM samples_fts WHERE samples_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, limit)
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()

def fts_search_with_filters(
    query: str,
    energy: str | None = None,
    mood: str | None = None,
    instrument: str | None = None,
    limit: int = 50
) -> list[int]:
    """Search with FTS5 + additional filters.
    Combines full-text search with exact-match filters.
    """
    fts_parts = [query] if query else []
    if energy:
        fts_parts.append(f'"{energy}"')
    if mood:
        fts_parts.append(f'"{mood}"')
    if instrument:
        fts_parts.append(f'"{instrument}"')
    combined_query = " ".join(fts_parts)
    return fts_search(combined_query, limit=limit)
