"""IGA flyer scraper."""
from __future__ import annotations
from scrapers.store_flyer import fetch_store_deals
from models import Deal


def fetch_iga_deals() -> list[Deal]:
    """Fetch deals from IGA flyer page."""
    return fetch_store_deals("IGA")
