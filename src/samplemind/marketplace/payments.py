"""Stripe checkout session creation and webhook fulfillment.

Phase 15 — Marketplace.
create_checkout_session() builds a Stripe Checkout session for a PackListing
and returns the redirect URL. handle_webhook() verifies the Stripe signature,
handles checkout.session.completed (issue download URL) and charge.refunded
(revoke access). Uses stripe.checkout.Session and stripe.Webhook.

Install:
    uv sync --extra marketplace
    # or: pip install stripe>=7

Environment variables:
    SAMPLEMIND_STRIPE_SECRET_KEY   — Stripe secret key (sk_live_... / sk_test_...)
    SAMPLEMIND_STRIPE_WEBHOOK_SECRET — Webhook signing secret (whsec_...)
"""

from __future__ import annotations

import os


def _require_stripe() -> object:
    """Return the stripe module or raise ImportError with install hint."""
    try:
        import stripe  # type: ignore[import-untyped]

        return stripe
    except ImportError as exc:
        raise ImportError(
            "stripe is not installed. "
            "Run: uv sync --extra marketplace\n"
            "Or:  pip install 'stripe>=7'"
        ) from exc


def _stripe_key() -> str:
    key = os.environ.get("SAMPLEMIND_STRIPE_SECRET_KEY", "")
    if not key:
        raise RuntimeError(
            "SAMPLEMIND_STRIPE_SECRET_KEY environment variable is not set. "
            "Set it to your Stripe secret key before calling payments functions."
        )
    return key


def create_checkout_session(
    listing_id: int,
    price_cents: int,
    pack_title: str,
    success_url: str,
    cancel_url: str,
    metadata: dict[str, str] | None = None,
) -> str:
    """Create a Stripe Checkout session for a pack purchase.

    Args:
        listing_id: PackListing primary key — stored in Stripe metadata for
            later webhook reconciliation.
        price_cents: Pack price in US cents (e.g. 999 = $9.99).  Must be ≥ 50
            (Stripe minimum) or 0 for free downloads.
        pack_title: Human-readable pack name shown on the Stripe checkout page.
        success_url: Redirect URL on successful payment.
        cancel_url: Redirect URL if the buyer cancels.
        metadata: Optional extra key/value pairs stored on the Stripe session.

    Returns:
        The Stripe Checkout Session ``url`` to redirect the buyer to.

    Raises:
        ValueError: If *price_cents* is 0 (use a direct download link instead).
        ImportError: If stripe is not installed.
        RuntimeError: If ``SAMPLEMIND_STRIPE_SECRET_KEY`` is not set.
    """
    if price_cents == 0:
        raise ValueError("Free packs (price_cents=0) do not need a checkout session.")

    stripe = _require_stripe()
    stripe.api_key = _stripe_key()  # type: ignore[attr-defined]

    session_metadata = {"listing_id": str(listing_id)}
    if metadata:
        session_metadata.update(metadata)

    session = stripe.checkout.Session.create(  # type: ignore[attr-defined]
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": pack_title},
                    "unit_amount": price_cents,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=session_metadata,
    )
    return str(session.url)


def handle_webhook(
    payload: bytes,
    sig_header: str,
) -> dict[str, object]:
    """Verify and dispatch a Stripe webhook event.

    Verifies the ``Stripe-Signature`` header against
    ``SAMPLEMIND_STRIPE_WEBHOOK_SECRET``, then dispatches on event type:

    - ``checkout.session.completed`` → returns
      ``{"event": "purchase", "listing_id": int, "customer_email": str}``
    - ``charge.refunded`` → returns
      ``{"event": "refund", "payment_intent": str}``
    - All other events → returns ``{"event": "ignored", "type": str}``

    Args:
        payload: Raw HTTP request body bytes (do **not** parse before passing).
        sig_header: Value of the ``Stripe-Signature`` HTTP header.

    Returns:
        A dict summarising the action taken.

    Raises:
        ValueError: If the signature is invalid or the timestamp is stale.
        ImportError: If stripe is not installed.
        RuntimeError: If ``SAMPLEMIND_STRIPE_WEBHOOK_SECRET`` is not set.
    """
    stripe = _require_stripe()
    stripe.api_key = _stripe_key()  # type: ignore[attr-defined]

    webhook_secret = os.environ.get("SAMPLEMIND_STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise RuntimeError(
            "SAMPLEMIND_STRIPE_WEBHOOK_SECRET environment variable is not set."
        )

    try:
        event = stripe.Webhook.construct_event(  # type: ignore[attr-defined]
            payload, sig_header, webhook_secret
        )
    except stripe.error.SignatureVerificationError as exc:  # type: ignore[attr-defined]
        raise ValueError(f"Invalid Stripe signature: {exc}") from exc

    event_type: str = event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        listing_id = int(session.get("metadata", {}).get("listing_id", 0))
        customer_email: str = session.get("customer_details", {}).get("email", "")
        return {"event": "purchase", "listing_id": listing_id, "customer_email": customer_email}

    if event_type == "charge.refunded":
        charge = event["data"]["object"]
        return {"event": "refund", "payment_intent": charge.get("payment_intent", "")}

    return {"event": "ignored", "type": event_type}
