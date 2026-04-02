"""Shared Playwright scraper that intercepts Flipp widget network responses."""
from __future__ import annotations
import logging
from playwright.sync_api import sync_playwright
from models import Deal
from scrapers.utils import _parse_items

log = logging.getLogger(__name__)

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

    log.info(f"Starting scrape for {store} ({url})")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # Track any Flipp-related requests for debugging
            flipp_urls_seen = []

            # Intercept responses from Flipp widget's endpoints
            def on_response(response):
                # Track Flipp requests for debugging
                if "flippenterprise.net" in response.url or "flyerkit" in response.url:
                    flipp_urls_seen.append(response.url)

                # Check for Flipp products endpoint (dam.flippenterprise.net/flyerkit/publication/{id}/products)
                if "dam.flippenterprise.net" in response.url and "/flyerkit/publication/" in response.url and "/products" in response.url:
                    try:
                        data = response.json()
                        # Response is either a list of products or a dict with "products" key
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict) and "products" in data:
                            items = data["products"]
                        else:
                            items = []

                        if items:
                            log.info(f"{store}: Captured {len(items)} items from Flipp widget")
                            captured.extend(items)
                    except Exception as e:
                        log.debug(f"{store}: Failed to parse Flipp response: {e}")

            page.on("response", on_response)
            # Use domcontentloaded instead of networkidle to avoid timeouts from tracking scripts
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            # Wait for async widget to load and make its network request
            page.wait_for_timeout(3_000)
            # Try scrolling to trigger lazy-loaded content
            try:
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                page.wait_for_timeout(2_000)
            except Exception:
                pass
            browser.close()

    except Exception as e:
        log.error(f"Exception loading {store}: {e}")
        raise RuntimeError(f"Failed to load {store} flyer page: {e}")

    log.info(f"Captured {len(captured)} raw items from {store}")

    # Debug: log Flipp URLs seen
    if flipp_urls_seen:
        log.info(f"{store}: {len(flipp_urls_seen)} Flipp URLs seen. Sample: {flipp_urls_seen[0] if flipp_urls_seen else 'none'}")
    else:
        log.info(f"{store}: No Flipp URLs intercepted")

    if not captured:
        raise RuntimeError(f"No Flipp widget data captured from {store}")

    deals = _parse_items(store, captured)
    log.info(f"Parsed {len(deals)} deals from {store}")
    return deals
