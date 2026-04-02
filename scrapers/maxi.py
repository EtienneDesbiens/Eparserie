"""Maxi flyer scraper — bypasses Forter antibot by never visiting maxi.ca."""
from __future__ import annotations
import logging
import os
import requests
from models import Deal
from scrapers.utils import _parse_items

log = logging.getLogger(__name__)

PUBLICATIONS_URL = "https://flipp.com/api/v2/publications"
DAM_PRODUCTS_URL = "https://dam.flippenterprise.net/flyerkit/publication/{pub_id}/products"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://flipp.com/",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_maxi_deals() -> list[Deal]:
    """Fetch Maxi deals via Flipp API, bypassing Forter protection."""
    postal_code = os.getenv("POSTAL_CODE", "H2X2X3")
    publications = _get_maxi_publications(postal_code)
    if not publications:
        raise RuntimeError(f"No Maxi publications found for postal code {postal_code!r}")

    all_items: list[dict] = []
    for pub in publications:
        items = _get_products(pub["id"])
        log.info("Maxi pub %s: fetched %d items", pub["id"], len(items))
        all_items.extend(items)

    return _parse_items("Maxi", all_items)


def _get_maxi_publications(postal_code: str) -> list[dict]:
    """Return all Maxi-branded publications from Flipp for the given postal code."""
    try:
        resp = requests.get(
            PUBLICATIONS_URL,
            params={"locale": "en-CA", "postal_code": postal_code},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        if "application/json" not in resp.headers.get("content-type", ""):
            raise RuntimeError(
                f"Flipp publications API returned non-JSON "
                f"(content-type: {resp.headers.get('content-type')!r})"
            )
        return [p for p in resp.json() if p.get("merchant_name") == "Maxi"]
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to reach Flipp publications API: {exc}") from exc


def _get_products(pub_id: int) -> list[dict]:
    """Fetch product items from dam.flippenterprise.net for a single publication."""
    resp = requests.get(
        DAM_PRODUCTS_URL.format(pub_id=pub_id),
        params={"display_type": "all", "locale": "en"},
        headers=_HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "products" in data:
        return data["products"]
    return []
