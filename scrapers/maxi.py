"""Maxi flyer scraper."""
from __future__ import annotations
from scrapers.store_flyer import fetch_store_deals
from models import Deal


def fetch_maxi_deals() -> list[Deal]:
    """Fetch deals from Maxi flyer page."""
    return fetch_store_deals("Maxi")
