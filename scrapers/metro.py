"""Metro flyer scraper."""
from __future__ import annotations
from scrapers.store_flyer import fetch_store_deals
from models import Deal


def fetch_metro_deals() -> list[Deal]:
    """Fetch deals from Metro flyer page."""
    return fetch_store_deals("Metro")
