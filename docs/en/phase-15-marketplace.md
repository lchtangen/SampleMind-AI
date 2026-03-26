# Phase 15 — Sample Pack Marketplace

**Status: 📋 Planned** — depends on Phase 9 (sample packs) + Phase 13 (cloud sync) | Phase 15 of 16 | Agent: `phase-15-marketplace`

> **Goal:** A producer-facing marketplace where creators can publish, discover,
> and install sample packs — with ratings, previews, commercial licensing,
> and revenue sharing for paid packs.
>
> **Stack:** FastAPI (marketplace API) · Stripe (payments) · Cloudflare R2 (file CDN) ·
> Supabase (listings + reviews) · SampleMind registry format (Phase 9).
>
> **Prerequisites:** Phase 9 (sample packs), Phase 13 (cloud sync), Phase 3 (auth).

---

## 1. Architecture

```
Creator (Publisher)                  Consumer (Producer)
┌─────────────────────┐             ┌─────────────────────┐
│ uv run samplemind   │             │ uv run samplemind   │
│ pack publish        │             │ pack search         │
│   --stripe-connect  │             │ pack install        │
└─────────────────────┘             └─────────────────────┘
         │                                    │
         ▼                                    ▼
┌────────────────────────────────────────────────────────┐
│                  Marketplace API (FastAPI)              │
│                                                        │
│  /marketplace/packs        → search, browse            │
│  /marketplace/packs/{slug} → details, preview          │
│  /marketplace/publish      → creator upload            │
│  /marketplace/purchase     → Stripe checkout           │
│  /marketplace/download     → signed R2 URL             │
│  /marketplace/reviews      → ratings & comments        │
└────────────────────────────────────────────────────────┘
         │                    │                │
         ▼                    ▼                ▼
  Supabase DB          Stripe API       Cloudflare R2
  (listings,           (checkout,       (pack files,
   reviews, users)      webhooks)        previews)
```

---

## 2. Pack Listing Schema

```python
# src/samplemind/marketplace/models.py
"""
Marketplace data models.

A PackListing extends the basic PackManifest (Phase 9) with
marketplace-specific fields: pricing, ratings, sales counts, previews.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PackListing:
    # Core identity (from Phase 9 manifest)
    slug: str             # URL-safe identifier: "dark-trap-vol-1"
    name: str
    version: str          # semver: "1.0.0"
    author: str           # creator username
    author_id: str        # Supabase user UUID

    # Content description
    description: str
    long_description: str = ""
    tags: list[str] = field(default_factory=list)
    instruments: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    moods: list[str] = field(default_factory=list)
    sample_count: int = 0
    size_mb: float = 0.0
    duration_minutes: float = 0.0
    bpm_range: str = ""           # "120-140"
    key_signatures: list[str] = field(default_factory=list)

    # Pricing (in USD cents — Stripe convention)
    price_cents: int = 0          # 0 = free
    currency: str = "usd"
    license: str = "Royalty-Free" # see Phase 9 licensing

    # Files (R2 object keys)
    pack_file_key: str = ""       # full pack .smpack in R2
    preview_file_key: str = ""    # 60-second preview WAV
    cover_image_key: str = ""     # 1:1 cover art JPEG

    # Marketplace metrics
    downloads: int = 0
    purchases: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    featured: bool = False

    # Timestamps
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "draft"  # draft | published | suspended


@dataclass
class PackReview:
    listing_slug: str
    reviewer_id: str
    reviewer_username: str
    rating: int           # 1–5 stars
    title: str
    body: str
    verified_purchase: bool
    created_at: datetime
    helpful_count: int = 0
```

---

## 3. Marketplace API Routes

```python
# src/samplemind/marketplace/routes/listings.py
"""
Marketplace listing routes.

All search and browse endpoints are PUBLIC (no auth required).
Upload, purchase, and review endpoints require auth.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from samplemind.marketplace.repository import ListingRepository
from samplemind.marketplace.models import PackListing

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.get("/packs")
async def search_packs(
    q: str = Query("", description="Full-text search"),
    instrument: str = Query("", description="Filter by instrument"),
    genre: str = Query("", description="Filter by genre"),
    mood: str = Query("", description="Filter by mood"),
    price: str = Query("all", enum=["all", "free", "paid"]),
    sort: str = Query("featured", enum=["featured", "newest", "rating", "downloads"]),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
):
    """
    Browse and search the marketplace.

    Public endpoint — no authentication required.
    Results are paginated and include cover art CDN URLs.
    """
    return await ListingRepository.search(
        query=q, instrument=instrument, genre=genre, mood=mood,
        price_filter=price, sort=sort, page=page, per_page=per_page,
    )


@router.get("/packs/{slug}")
async def get_pack(slug: str):
    """Get full pack details including sample list and reviews."""
    listing = await ListingRepository.get_by_slug(slug)
    if not listing:
        raise HTTPException(status_code=404, detail=f"Pack '{slug}' not found")
    return listing


@router.get("/packs/{slug}/preview")
async def get_preview_url(slug: str):
    """
    Get a short-lived signed URL for the 60-second preview audio.
    Signed URLs expire in 1 hour to prevent hotlinking.
    """
    listing = await ListingRepository.get_by_slug(slug)
    if not listing or not listing.preview_file_key:
        raise HTTPException(status_code=404, detail="Preview not available")

    from samplemind.marketplace.cdn import get_signed_url
    url = get_signed_url(listing.preview_file_key, expires_in_seconds=3600)
    return {"preview_url": url, "expires_in": 3600}


@router.get("/featured")
async def get_featured():
    """Return featured and trending packs for the homepage."""
    return {
        "featured": await ListingRepository.get_featured(limit=6),
        "new_releases": await ListingRepository.get_newest(limit=12),
        "top_rated": await ListingRepository.get_top_rated(limit=12),
        "trending": await ListingRepository.get_trending(limit=12),
    }
```

---

## 4. Creator Publishing Flow

```python
# src/samplemind/marketplace/publisher.py
"""
Pack publishing pipeline for creators.

Flow:
  1. Creator runs: uv run samplemind pack publish my-pack.smpack
  2. Pack is validated (schema, SHA-256, license, energy values)
  3. Pack uploaded to R2 (creator's storage)
  4. Preview WAV extracted and uploaded separately
  5. Listing created in Supabase (status: draft)
  6. Creator reviews listing in web UI, hits "Publish"
  7. Status changes to "published" → visible in marketplace

Stripe Connect (for paid packs):
  - Creator must connect their Stripe account
  - Revenue split: 80% creator / 20% platform (configurable)
  - Payouts: automatic monthly, via Stripe Connect
"""
from __future__ import annotations
import json
import zipfile
import hashlib
import tempfile
from pathlib import Path
from samplemind.packs.licensing import check_license
from samplemind.core.logging import get_logger

log = get_logger(__name__)

VALID_ENERGY_VALUES   = {"low", "mid", "high"}
VALID_INSTRUMENT_VALUES = {
    "kick", "snare", "hihat", "bass", "pad", "lead", "loop", "sfx", "unknown"
}


def validate_pack_for_marketplace(pack_path: Path) -> list[str]:
    """
    Comprehensive validation before publishing.

    Returns empty list if valid, or list of error strings.
    """
    errors: list[str] = []

    if not zipfile.is_zipfile(str(pack_path)):
        return ["Not a valid ZIP/smpack file"]

    with zipfile.ZipFile(pack_path, "r") as zf:
        if "manifest.json" not in zf.namelist():
            errors.append("Missing manifest.json")
            return errors

        manifest = json.loads(zf.read("manifest.json"))

        # Required fields
        for field in ["name", "slug", "version", "author", "license"]:
            if not manifest.get(field):
                errors.append(f"manifest.json missing required field: '{field}'")

        # Validate slug format
        slug = manifest.get("slug", "")
        if not slug.replace("-", "").isalnum():
            errors.append(f"Invalid slug '{slug}' — use only a-z, 0-9, hyphens")

        # Validate sample energy values
        for sample in manifest.get("samples", []):
            energy = sample.get("energy")
            if energy and energy not in VALID_ENERGY_VALUES:
                errors.append(
                    f"Sample '{sample.get('filename')}' has invalid energy='{energy}'. "
                    f"Use: low/mid/high (never 'medium')"
                )
            instrument = sample.get("instrument")
            if instrument and instrument not in VALID_INSTRUMENT_VALUES:
                errors.append(
                    f"Sample '{sample.get('filename')}' has invalid instrument='{instrument}'"
                )

        # Verify SHA-256 checksums for all listed samples
        archive_files = set(zf.namelist())
        for sample in manifest.get("samples", []):
            arc_name = f"samples/{sample['filename']}"
            if arc_name not in archive_files:
                errors.append(f"Missing in archive: {arc_name}")
                continue
            data = zf.read(arc_name)
            actual_sha256 = hashlib.sha256(data).hexdigest()
            if actual_sha256 != sample.get("sha256", ""):
                errors.append(f"SHA-256 mismatch for {sample['filename']}")

        # License check
        license_str = manifest.get("license", "")
        license_result = check_license(slug, license_str)
        if license_result.warning:
            log.warning("pack_license_warning", warning=license_result.warning)
            # License warnings don't block publishing — just log

    return errors


def extract_preview_audio(pack_path: Path, duration_seconds: float = 60.0) -> Path | None:
    """
    Extract a 60-second preview from the first loop sample in the pack.

    Returns path to preview WAV, or None if no suitable sample found.
    Requires ffmpeg to be installed.
    """
    try:
        import subprocess
        with zipfile.ZipFile(pack_path, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            # Prefer loops for preview; fall back to any sample
            samples = manifest.get("samples", [])
            loops = [s for s in samples if s.get("instrument") == "loop"]
            preview_sample = loops[0] if loops else (samples[0] if samples else None)

            if not preview_sample:
                return None

            # Extract sample to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(zf.read(f"samples/{preview_sample['filename']}"))
                src_path = Path(tmp.name)

        # Fade in/out and trim to duration_seconds
        preview_path = src_path.with_suffix(".preview.wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", str(src_path),
            "-t", str(duration_seconds),
            "-af", f"afade=t=in:d=1,afade=t=out:st={duration_seconds-3}:d=3",
            str(preview_path),
        ], check=True, capture_output=True)
        src_path.unlink()
        return preview_path
    except Exception as e:
        log.warning("preview_extraction_failed", error=str(e))
        return None
```

---

## 5. Purchase & Download Flow

```python
# src/samplemind/marketplace/payments.py
"""
Stripe payment integration for paid sample packs.

Flow:
  1. POST /marketplace/purchase/{slug}
     → Create Stripe Checkout Session
     → Return checkout_url to client
  2. User completes payment on Stripe-hosted page
  3. Stripe sends webhook: checkout.session.completed
  4. Webhook handler: record purchase in DB
  5. GET /marketplace/download/{slug}
     → Verify purchase record
     → Generate signed R2 download URL (valid 24h)
     → Return download_url

Stripe Connect:
  - Each creator has a Stripe Connected Account
  - On purchase, application_fee_amount = 20% of price
  - Creator receives 80% directly to their bank account
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from samplemind.api.routes.auth import get_current_active_user
from samplemind.core.config import get_settings

router = APIRouter(prefix="/marketplace", tags=["Payments"])


@router.post("/purchase/{slug}")
async def create_checkout(
    slug: str,
    user=Depends(get_current_active_user),
):
    """Create a Stripe Checkout Session for purchasing a sample pack."""
    try:
        import stripe
    except ImportError:
        raise HTTPException(500, "Stripe not installed: uv add stripe")

    from samplemind.marketplace.repository import ListingRepository, PurchaseRepository

    listing = await ListingRepository.get_by_slug(slug)
    if not listing:
        raise HTTPException(404, f"Pack '{slug}' not found")

    if listing.price_cents == 0:
        raise HTTPException(400, "This pack is free — use /marketplace/download directly")

    # Check if already purchased
    if await PurchaseRepository.has_purchased(user.id, slug):
        raise HTTPException(400, "Already purchased")

    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": listing.currency,
                "unit_amount": listing.price_cents,
                "product_data": {"name": listing.name, "description": listing.description},
            },
            "quantity": 1,
        }],
        metadata={"slug": slug, "user_id": str(user.id)},
        success_url=f"{settings.api_host}:{settings.api_port}/marketplace/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.api_host}:{settings.api_port}/marketplace/packs/{slug}",
        # Application fee for marketplace platform
        application_fee_amount=int(listing.price_cents * 0.20),
        transfer_data={"destination": listing.stripe_account_id},
    )
    return {"checkout_url": session.url}


@router.get("/download/{slug}")
async def download_pack(slug: str, user=Depends(get_current_active_user)):
    """
    Get a signed download URL for a purchased (or free) pack.
    Signed URLs are valid for 24 hours.
    """
    from samplemind.marketplace.repository import ListingRepository, PurchaseRepository
    from samplemind.marketplace.cdn import get_signed_url

    listing = await ListingRepository.get_by_slug(slug)
    if not listing:
        raise HTTPException(404, "Pack not found")

    # Free packs: no purchase check required
    if listing.price_cents > 0:
        if not await PurchaseRepository.has_purchased(user.id, slug):
            raise HTTPException(403, "Purchase required to download this pack")

    url = get_signed_url(listing.pack_file_key, expires_in_seconds=86400)
    await ListingRepository.increment_downloads(slug)
    return {"download_url": url, "filename": f"{slug}.smpack", "expires_in": 86400}
```

---

## 6. CLI Marketplace Commands

```bash
# Browse
uv run samplemind marketplace search "dark trap"
uv run samplemind marketplace browse --genre trap --price free
uv run samplemind marketplace pack dark-trap-vol-1      # view details

# Install
uv run samplemind marketplace install dark-trap-vol-1   # free pack
uv run samplemind marketplace purchase dark-trap-vol-1  # opens browser for payment

# Create and publish (requires creator account)
uv run samplemind marketplace publish my-pack.smpack --price 0         # free
uv run samplemind marketplace publish my-pack.smpack --price 9.99      # paid ($9.99)
uv run samplemind marketplace withdraw my-slug        # pull from marketplace

# Review
uv run samplemind marketplace review dark-trap-vol-1 --rating 5 --title "Excellent" --body "..."
```

---

## 7. Testing

```python
# tests/test_marketplace.py
"""Marketplace tests — all external services mocked."""
import pytest
from samplemind.marketplace.publisher import validate_pack_for_marketplace
import zipfile, json, hashlib
from pathlib import Path


@pytest.fixture
def valid_smpack(tmp_path: Path) -> Path:
    """Create a valid .smpack file for testing."""
    wav_data = b"RIFF" + b"\x00" * 36   # minimal WAV header stub
    sha256 = hashlib.sha256(wav_data).hexdigest()
    manifest = {
        "name": "Test Pack", "slug": "test-pack", "version": "1.0.0",
        "author": "tester", "license": "Royalty-Free",
        "samples": [{"filename": "kick.wav", "sha256": sha256,
                     "instrument": "kick", "energy": "high"}],
    }
    pack_path = tmp_path / "test-pack.smpack"
    with zipfile.ZipFile(pack_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("samples/kick.wav", wav_data)
    return pack_path


def test_valid_pack_passes_validation(valid_smpack):
    errors = validate_pack_for_marketplace(valid_smpack)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_invalid_energy_value_detected(tmp_path):
    wav_data = b"RIFF" + b"\x00" * 36
    sha256 = hashlib.sha256(wav_data).hexdigest()
    manifest = {
        "name": "Bad Pack", "slug": "bad-pack", "version": "1.0.0",
        "author": "tester", "license": "Royalty-Free",
        "samples": [{"filename": "kick.wav", "sha256": sha256,
                     "instrument": "kick", "energy": "medium"}],  # ← invalid!
    }
    pack_path = tmp_path / "bad.smpack"
    with zipfile.ZipFile(pack_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        zf.writestr("samples/kick.wav", wav_data)

    errors = validate_pack_for_marketplace(pack_path)
    assert any("medium" in e for e in errors), "Should detect invalid energy value 'medium'"


def test_missing_sample_detected(tmp_path):
    manifest = {
        "name": "Missing Pack", "slug": "missing", "version": "1.0.0",
        "author": "tester", "license": "CC0",
        "samples": [{"filename": "ghost.wav", "sha256": "abc123",
                     "instrument": "kick", "energy": "high"}],
    }
    pack_path = tmp_path / "missing.smpack"
    with zipfile.ZipFile(pack_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
        # ghost.wav is NOT added to archive

    errors = validate_pack_for_marketplace(pack_path)
    assert any("ghost.wav" in e for e in errors)
```

---

## 8. Checklist

- [ ] `uv add stripe supabase` — marketplace dependencies installed
- [ ] `validate_pack_for_marketplace()` catches invalid energy/instrument values
- [ ] SHA-256 checksums verified during validation
- [ ] Signed R2 download URLs generated correctly
- [ ] Stripe Checkout session created with 20% platform fee
- [ ] Stripe webhook verifies signature before recording purchase
- [ ] `has_purchased()` check before issuing download URL
- [ ] Preview audio extracted correctly (requires ffmpeg)
- [ ] All marketplace tests pass with mocked Stripe and Supabase
- [ ] `uv run samplemind marketplace search "trap"` works without auth
- [ ] Creator publishing validates schema AND energy values

