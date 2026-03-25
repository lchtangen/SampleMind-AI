"""Add vector embeddings table for semantic search.

Phase 11 — Semantic Search.
Creates the sample_embeddings table to store CLAP audio embeddings
as BLOB columns. The sqlite-vec virtual table is created separately
via a raw SQL statement (not tracked by Alembic metadata).
"""
# TODO: implement in Phase 11 — Semantic Search

from alembic import op  # noqa: F401

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TODO: Phase 11 — create sample_embeddings table
    pass


def downgrade() -> None:
    # TODO: Phase 11 — drop sample_embeddings table
    pass
