"""Shared Playwright scraper that intercepts Flipp widget network responses."""
from __future__ import annotations
from playwright.sync_api import sync_playwright
from models import Deal
from scrapers.utils import _parse_items

STORE_URLS = {
    "Maxi":    "https://www.maxi.ca/en/flyer",
    "Metro":   "https://www.metro.ca/en/flyer",
    "IGA":     "https://www.iga.net/en/flyer",
    "Provigo": "https://www.provigo.ca/en/promotion",
}


def fetch_store_deals(store: str) -> list[Deal]:
    """
    Open store flyer page, intercept Flipp widget JSON responses.

    The store's flyer page embeds a Flipp widget that makes HTTP requests to:
    cdn.flipp.com/flyerkit/publications/{id}/items

    We intercept these responses and extract the JSON deal data directly.
    """
    if store not in STORE_URLS:
        raise ValueError(f"Unknown store: {store}")

    url = STORE_URLS[store]
    captured: list[dict] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Intercept responses from Flipp widget's items endpoint
            def on_response(response):
                if "cdn.flipp.com/flyerkit/publications" in response.url and "/items" in response.url:
                    try:
                        items = response.json()
                        if isinstance(items, list):
                            captured.extend(items)
                    except Exception:
                        # Silently ignore JSON parse errors
                        pass

            page.on("response", on_response)
            page.goto(url, wait_until="networkidle", timeout=60_000)
            browser.close()

    except Exception as e:
        raise RuntimeError(f"Failed to load {store} flyer page: {e}")

    if not captured:
        raise RuntimeError(f"No Flipp widget data captured from {store}")

    return _parse_items(store, captured)
