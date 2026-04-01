from __future__ import annotations
import requests
from models import Deal

STORE_NAMES = {"Maxi", "Provigo", "IGA", "Metro"}
PUBLICATIONS_URL = "https://flipp.com/api/v2/publications"
ITEMS_URL = "https://cdn.flipp.com/flyerkit/publications/{pub_id}/items"


def fetch_flipp_deals(postal_code: str) -> list[Deal]:
    publications = _get_publications(postal_code)
    deals: list[Deal] = []
    for pub in publications:
        if pub.get("merchant_name") in STORE_NAMES:
            items = _get_items(pub["id"])
            deals.extend(_parse_items(pub["merchant_name"], items))
    return deals


def _get_publications(postal_code: str) -> list[dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://flipp.com/",
        "X-Requested-With": "XMLHttpRequest",
    }
    resp = requests.get(
        PUBLICATIONS_URL,
        params={"locale": "en-CA", "postal_code": postal_code},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()

    # Validate response is JSON
    content_type = resp.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise ValueError(f"Expected JSON response, got {content_type}. Flipp API may have changed or is blocking access.")

    return resp.json()


def _get_items(pub_id: int) -> list[dict]:
    resp = requests.get(ITEMS_URL.format(pub_id=pub_id), timeout=10)
    resp.raise_for_status()
    return resp.json()


def _parse_items(store: str, items: list[dict]) -> list[Deal]:
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
