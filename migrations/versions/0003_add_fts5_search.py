"""add FTS5 full-text search index for samples

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-25 00:00:00.000000

Creates a FTS5 virtual table (``samples_fts``) that indexes the
``filename``, ``tags``, and ``genre`` columns of the ``samples`` table.

Three triggers keep the FTS index automatically in sync with the base table:
  samples_ai  AFTER INSERT  — add new row to index
  samples_au  AFTER UPDATE  — delete old entry, insert updated entry
  samples_ad  AFTER DELETE  — remove entry from index

The ``content='samples'`` and ``content_rowid='id'`` options tell FTS5 to
read document content from the base table (not store a redundant copy), so
the virtual table only stores the search index, not the original text.

At upgrade time the existing rows in ``samples`` are bulk-inserted into
the FTS index so searches work immediately without a full re-import.

If SQLite was compiled without FTS5 support this migration will raise.
Standard CPython on macOS and most Linux distributions include FTS5.
Check with:
    python -c "import sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')"
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create the FTS5 virtual table — content-based, rowid maps to samples.id
    op.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS samples_fts
        USING fts5(
            filename,
            tags,
            genre,
            content='samples',
            content_rowid='id'
        )
    """)

    # 2. Backfill the index with existing rows
    op.execute("""
        INSERT INTO samples_fts(rowid, filename, tags, genre)
        SELECT id,
               filename,
               COALESCE(tags, ''),
               COALESCE(genre, '')
        FROM samples
    """)

    # 3. AFTER INSERT trigger — add new sample to index
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS samples_ai
        AFTER INSERT ON samples
        BEGIN
            INSERT INTO samples_fts(rowid, filename, tags, genre)
            VALUES (new.id,
                    new.filename,
                    COALESCE(new.tags, ''),
                    COALESCE(new.genre, ''));
        END
    """)

    # 4. AFTER UPDATE trigger — remove old entry, insert updated entry
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS samples_au
        AFTER UPDATE ON samples
        BEGIN
            INSERT INTO samples_fts(samples_fts, rowid, filename, tags, genre)
            VALUES ('delete',
                    old.id,
                    old.filename,
                    COALESCE(old.tags, ''),
                    COALESCE(old.genre, ''));
            INSERT INTO samples_fts(rowid, filename, tags, genre)
            VALUES (new.id,
                    new.filename,
                    COALESCE(new.tags, ''),
                    COALESCE(new.genre, ''));
        END
    """)

    # 5. AFTER DELETE trigger — remove deleted sample from index
    op.execute("""
        CREATE TRIGGER IF NOT EXISTS samples_ad
        AFTER DELETE ON samples
        BEGIN
            INSERT INTO samples_fts(samples_fts, rowid, filename, tags, genre)
            VALUES ('delete',
                    old.id,
                    old.filename,
                    COALESCE(old.tags, ''),
                    COALESCE(old.genre, ''));
        END
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS samples_ai")
    op.execute("DROP TRIGGER IF EXISTS samples_au")
    op.execute("DROP TRIGGER IF EXISTS samples_ad")
    op.execute("DROP TABLE IF EXISTS samples_fts")
