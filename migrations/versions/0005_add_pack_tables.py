"""Add marketplace tables: packlistings and packreviews.

Phase 9 / Phase 15 — Sample Packs and Marketplace.
Creates packlistings table (id, slug, title, price_cents, author_id,
r2_key, preview_r2_key, stripe_product_id, status, avg_rating,
rating_count, download_count, created_at, updated_at) and packreviews
table (id, listing_id, user_id, rating, title, body, verified_purchase,
created_at).
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "packlistings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("r2_key", sa.String(), nullable=False),
        sa.Column("preview_r2_key", sa.String(), nullable=True),
        sa.Column("stripe_product_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("avg_rating", sa.Float(), nullable=True),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_packlistings_slug", "packlistings", ["slug"])

    op.create_table(
        "packreviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("packlistings.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("verified_purchase", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_packreviews_listing_id", "packreviews", ["listing_id"])
    op.create_index("ix_packreviews_user_id", "packreviews", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_packreviews_user_id", table_name="packreviews")
    op.drop_index("ix_packreviews_listing_id", table_name="packreviews")
    op.drop_table("packreviews")

    op.drop_index("ix_packlistings_slug", table_name="packlistings")
    op.drop_table("packlistings")
