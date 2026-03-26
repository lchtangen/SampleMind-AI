"""PackListing and PackReview data models for the marketplace.

Phase 15 — Marketplace.
PackListing holds pack metadata (slug, title, price_cents, author_id, cdn_key,
stripe_product_id). PackReview holds buyer reviews (listing_id, user_id,
rating 1-5, body). Both are SQLModel tables with Alembic migrations.
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Field, SQLModel


class PackListing(SQLModel, table=True):
    """Marketplace listing for a .smpack file.

    One row per published (or draft) sample pack.  The ``r2_key`` stores the
    Cloudflare R2 object key for the ``.smpack`` archive; the optional
    ``preview_r2_key`` is a short audio preview clip.
    """

    __tablename__ = "packlistings"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    """URL-safe identifier, e.g. ``dark-trap-essentials-v2``."""

    title: str
    author_id: int = Field(foreign_key="users.id")

    price_cents: int = Field(default=0)
    """Price in US cents.  0 = free download."""

    r2_key: str
    """Cloudflare R2 object key for the ``.smpack`` archive."""

    preview_r2_key: str | None = None
    """Optional short audio preview clip key in R2."""

    stripe_product_id: str | None = None
    """Stripe Product ID — populated after ``payments.create_product()``."""

    status: str = Field(default="draft")
    """Lifecycle state: ``draft`` | ``published`` | ``suspended``."""

    avg_rating: float | None = None
    rating_count: int = Field(default=0)
    download_count: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PackReview(SQLModel, table=True):
    """Buyer review for a marketplace listing.

    One row per (listing, user) pair — users may only review a pack once.
    ``verified_purchase`` is set to ``True`` by the webhook handler when the
    Stripe ``checkout.session.completed`` event is received.
    """

    __tablename__ = "packreviews"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="packlistings.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    rating: int
    """Integer from 1 (worst) to 5 (best)."""

    title: str
    body: str

    verified_purchase: bool = Field(default=False)
    """True when the reviewer has a confirmed Stripe purchase."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
