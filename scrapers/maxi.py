"""Maxi flyer scraper — uses shared headless Playwright approach."""
from __future__ import annotations
from models import Deal
from scrapers.store_flyer import fetch_store_deals


def fetch_maxi_deals() -> list[Deal]:
    """Fetch Maxi deals using the shared Playwright scraper."""
    return fetch_store_deals("Maxi")
