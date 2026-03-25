"""Add sample pack tables (pack_listings, pack_reviews).

Phase 9 / Phase 15 — Sample Packs and Marketplace.
Creates pack_listings table (id, slug, title, price_cents, author_id,
cdn_key, stripe_product_id, created_at) and pack_reviews table
(id, listing_id, user_id, rating, body, created_at).
"""
# TODO: implement in Phase 9 / Phase 15 — Sample Packs / Marketplace

from alembic import op  # noqa: F401

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TODO: Phase 9/15 — create pack_listings and pack_reviews tables
    pass


def downgrade() -> None:
    # TODO: Phase 9/15 — drop pack_listings and pack_reviews tables
    pass
