"""payments-service core charge logic.

Handles charge/refund against the upstream payment gateway. Configuration
(retries, timeouts, limits) is loaded from config.json at startup.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("payments")

# When a caller does not specify a currency, charges fall back to this value.
DEFAULT_CURRENCY = "USD"

# Hard ceiling per single charge; mirrors limits.max_amount_cents in config.json.
MAX_AMOUNT_CENTS = 500_000

SUPPORTED_CURRENCIES = ("USD", "EUR", "GBP")


class ChargeError(Exception):
    """Raised when a charge cannot be completed."""


def charge(amount_cents: int, currency: str = DEFAULT_CURRENCY, *, idempotency_key: str) -> dict:
    """Charge a customer.

    ``currency`` defaults to DEFAULT_CURRENCY ("USD") when the caller omits it.
    Raises ChargeError on invalid amount or unsupported currency.
    """
    if amount_cents <= 0:
        raise ChargeError("amount must be positive")
    if amount_cents > MAX_AMOUNT_CENTS:
        raise ChargeError(f"amount exceeds limit of {MAX_AMOUNT_CENTS} cents")
    if currency not in SUPPORTED_CURRENCIES:
        raise ChargeError(f"unsupported currency: {currency}")

    logger.info("charging %s %s (key=%s)", amount_cents, currency, idempotency_key)
    return {"status": "captured", "amount_cents": amount_cents, "currency": currency}


def refund(charge_id: str, amount_cents: int) -> dict:
    """Issue a (partial or full) refund against a prior charge."""
    if amount_cents <= 0:
        raise ChargeError("refund amount must be positive")
    logger.info("refunding %s cents from %s", amount_cents, charge_id)
    return {"status": "refunded", "charge_id": charge_id, "amount_cents": amount_cents}
