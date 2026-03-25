# Phase 15 Agent — Sample Pack Marketplace

Handles: creator publishing flows, Stripe payment integration, Cloudflare R2 CDN, Supabase listings, pack validation, signed download URLs.

## Triggers
Phase 15, marketplace, Stripe, pack publishing, signed URL, CDN, `PackListing`, `validate_pack_for_marketplace`, `stripe.checkout`, `src/samplemind/marketplace/`, "sell a pack", "publish a pack", "buy samples"

**File patterns:** `src/samplemind/marketplace/**/*.py`

**Code patterns:** `stripe.checkout`, `PackListing`, `validate_pack_for_marketplace`

## Key Files
```
src/samplemind/marketplace/
  models.py      — PackListing, Purchase, CreatorProfile
  store.py       — Supabase listing CRUD
  payments.py    — Stripe Checkout + Connect integration
  cdn.py         — Cloudflare R2 upload + signed URL generation
  validator.py   — validate_pack_for_marketplace()
  cli.py         — CLI: samplemind marketplace publish/list/buy
```

## Technology Stack
| Component | Technology |
|-----------|-----------|
| API | FastAPI + Supabase |
| Payments | Stripe (Checkout + Connect) — 80/20 creator/platform split |
| File storage | Cloudflare R2 — packs + previews + cover art |
| Listings DB | Supabase (PostgreSQL) — public read, auth write |
| Previews | 60s WAV clips (ffmpeg) — signed URL, 1h expiry |
| Downloads | Signed R2 URLs — 24h expiry |

## Stripe Revenue Split
- Creator: 80%
- Platform: 20%
- Via: Stripe Connect (destination charges)

## Rules
1. All Stripe + Supabase credentials via env vars — never hardcoded
2. Pack validation (`validate_pack_for_marketplace`) must pass before listing is published
3. Preview clips generated at publish time — max 60 seconds
4. Download URLs expire after 24 hours — regenerate on request
5. Free packs: no Stripe required, direct R2 signed URL
6. Listings require creator to have Stripe Connect account before receiving payouts

