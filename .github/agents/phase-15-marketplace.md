# Phase 15 Agent — Marketplace

Handles: Stripe Checkout, Stripe Connect, pack publishing, signed CDN URLs, pack validation, reviews.

## Triggers
- Phase 15, marketplace, Stripe, purchase, listing, pack review, signed URL, creator publishing

## Key Files
- `src/samplemind/marketplace/models.py`
- `src/samplemind/marketplace/publisher.py`
- `src/samplemind/marketplace/payments.py`
- `src/samplemind/marketplace/cdn.py`

## Revenue Split

- Platform fee: 20% (`application_fee_amount = int(price_cents * 0.20)`)
- Creator receives: 80% directly via Stripe Connect

## Validation Rules (MUST enforce before publishing)

1. Energy values: ONLY `"low"`, `"mid"`, `"high"` — REJECT `"medium"`
2. Instrument values: only from canonical set
3. SHA-256 checksums verified against archive contents
4. All listed samples present in ZIP
5. `manifest.json` has all required fields: name, slug, version, author, license
6. Slug: a-z, 0-9, hyphens only

## URL Expiry

- Preview audio: 1 hour signed URL
- Pack download: 24 hour signed URL
- NEVER serve files without expiring signed URLs

## Rules
1. Stripe webhook MUST verify signature before processing
2. `has_purchased()` check BEFORE issuing download URL for paid packs
3. Free packs (price_cents=0): skip purchase check, direct download
4. All Stripe and Supabase calls mocked in tests

