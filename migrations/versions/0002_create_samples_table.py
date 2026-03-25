"""create samples table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-25 00:00:00.000000

Migrates the legacy sqlite3 ``samples`` table schema to a Alembic-managed
table definition that exactly mirrors the ``Sample`` SQLModel class.

If the ``samples`` table already exists from the legacy ``database.py``
``init_db()`` call, this migration will fail.  In that case, mark it as
applied without running it:

    uv run alembic stamp 0002

The existing legacy table is compatible — the SQLModel layer reads/writes
the same columns.  The only difference is that Alembic now owns the schema.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "samples",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("bpm", sa.Float(), nullable=True),
        sa.Column("key", sa.String(), nullable=True),
        sa.Column("mood", sa.String(), nullable=True),
        sa.Column("energy", sa.String(), nullable=True),
        sa.Column("instrument", sa.String(), nullable=True),
        sa.Column("genre", sa.String(), nullable=True),
        sa.Column("tags", sa.String(), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
    )
    op.create_index(op.f("ix_samples_filename"), "samples", ["filename"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_samples_filename"), table_name="samples")
    op.drop_table("samples")

