"""Shared scraper utilities."""
from __future__ import annotations
from models import Deal


def _parse_price(price_str: str | None) -> float | None:
    """Parse price string, handling $ and commas."""
    if not price_str:
        return None
    try:
        return float(price_str.replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def _parse_items(store: str, items: list[dict]) -> list[Deal]:
    """Parse Flipp widget JSON items into Deal objects."""
    deals: list[Deal] = []
    for item in items:
        sale_price = item.get("current_price")
        if sale_price is None:
            continue
        original_price = item.get("original_price")
        discount_pct: float | None = None
        if original_price and float(original_price) > float(sale_price):
            discount_pct = round(
                (float(original_price) - float(sale_price)) / float(original_price) * 100, 1
            )
        deals.append(
            Deal(
                store=store,
                name=item.get("name", ""),
                description=item.get("description", ""),
                sale_price=float(sale_price),
                original_price=float(original_price) if original_price else None,
                discount_pct=discount_pct,
                valid_until=item.get("valid_to"),
            )
        )
    return deals
