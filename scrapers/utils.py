"""Shared scraper utilities."""
from __future__ import annotations
import logging
from models import Deal

log = logging.getLogger(__name__)


def _parse_price(price_str: str | None) -> float | None:
    """Parse price string, handling $ and commas."""
    if not price_str:
        return None
    try:
        return float(price_str.replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def _parse_items(store: str, items: list[dict]) -> list[Deal]:
    """Parse Flipp widget JSON items into Deal objects.

    Handles both old format (current_price, original_price) and new dam.flippenterprise.net format (price_text, original_price).
    """
    deals: list[Deal] = []

    for item in items:
        # Try new format first (price_text), fall back to old format (current_price)
        sale_price_str = item.get("price_text") or item.get("current_price")
        if not sale_price_str:
            continue

        # Parse the sale price (handles $12.99 format or plain 12.99)
        sale_price = _parse_price(str(sale_price_str))
        if sale_price is None:
            continue

        # Get original price (should be numeric in both formats)
        original_price_val = item.get("original_price")
        original_price: float | None = None
        if original_price_val:
            original_price = _parse_price(str(original_price_val))

        # Calculate discount percentage
        discount_pct: float | None = None
        if original_price and original_price > sale_price:
            discount_pct = round(
                (original_price - sale_price) / original_price * 100, 1
            )

        # Get valid_until date (new format uses valid_to_timestamp, old uses valid_to)
        valid_until = item.get("valid_to") or item.get("valid_to_timestamp")

        deals.append(
            Deal(
                store=store,
                name=item.get("name", ""),
                description=item.get("description", ""),
                sale_price=sale_price,
                original_price=original_price,
                discount_pct=discount_pct,
                valid_until=valid_until,
            )
        )
    return deals
