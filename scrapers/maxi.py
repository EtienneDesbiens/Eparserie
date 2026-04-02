"""Maxi flyer scraper — HTTP first, headed browser fallback for Forter."""
from __future__ import annotations
import logging
import os
import pathlib
import requests
from playwright.sync_api import sync_playwright
from models import Deal
from scrapers.utils import _parse_items

log = logging.getLogger(__name__)

PUBLICATIONS_URL = "https://flipp.com/api/v2/publications"
DAM_PRODUCTS_URL = "https://dam.flippenterprise.net/flyerkit/publication/{pub_id}/products"
MAXI_URL = "https://www.maxi.ca/en/flyer"

# Persistent profile directory — Forter session trust builds over time
_PROFILE_DIR = str(pathlib.Path(__file__).parent.parent / "browser_profiles" / "maxi")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://flipp.com/",
    "X-Requested-With": "XMLHttpRequest",
}


def fetch_maxi_deals() -> list[Deal]:
    """Try HTTP API first; fall back to headed browser if blocked."""
    # Primary: HTTP approach (fast, no browser needed)
    try:
        postal_code = os.getenv("POSTAL_CODE", "H2X2X3")
        publications = _get_maxi_publications(postal_code)
        if publications:
            all_items: list[dict] = []
            for pub in publications:
                items = _get_products(pub["id"])
                log.info("Maxi pub %s: fetched %d items", pub["id"], len(items))
                all_items.extend(items)
            if all_items:
                return _parse_items("Maxi", all_items)
    except RuntimeError as e:
        log.warning("Maxi HTTP approach failed (%s), trying headed browser", str(e))

    # Fallback: headed Playwright with persistent profile
    return _fetch_maxi_playwright()


def _fetch_maxi_playwright() -> list[Deal]:
    """Launch headed Chromium with persistent profile to bypass Forter."""
    log.info("Launching headed browser for Maxi (profile: %s)", _PROFILE_DIR)
    captured: list[dict] = []

    with sync_playwright() as p:
        # launch_persistent_context keeps cookies + localStorage across runs
        context = p.chromium.launch_persistent_context(
            _PROFILE_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        def on_response(response):
            if (
                "dam.flippenterprise.net" in response.url
                and "/flyerkit/publication/" in response.url
                and "/products" in response.url
            ):
                try:
                    data = response.json()
                    items = data if isinstance(data, list) else data.get("products", [])
                    if items:
                        log.info("Maxi: captured %d items from Flipp widget", len(items))
                        captured.extend(items)
                except Exception:
                    pass

        page.on("response", on_response)
        page.goto(MAXI_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(5_000)
        try:
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(2_000)
        except Exception:
            pass
        context.close()

    if not captured:
        raise RuntimeError("No Flipp widget data captured from Maxi (headed browser)")

    return _parse_items("Maxi", captured)


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
