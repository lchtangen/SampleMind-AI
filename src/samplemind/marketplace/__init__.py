"""Sample pack marketplace with Stripe payments and R2 CDN distribution.

Phase 15 — Marketplace.
Enables creators to publish .smpack files to a hosted marketplace. Buyers
complete a Stripe checkout session; a signed R2 download URL is issued on
payment confirmation. Handles webhooks for fulfillment and refunds.

See: docs/en/phase-15-marketplace.md
"""
