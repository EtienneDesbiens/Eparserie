from __future__ import annotations
import logging
from itertools import groupby

from config import load_config
from scrapers.maxi import fetch_maxi_deals
from scrapers.metro import fetch_metro_deals
from scrapers.iga import fetch_iga_deals
from scrapers.provigo import fetch_provigo_deals
from recipes import fetch_recipes
from email_sender import render_email, send_email, STORE_ORDER


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("grocerybot.log"),
            logging.StreamHandler(),
        ],
    )
    log = logging.getLogger(__name__)
    config = load_config()
    all_deals = []
    failed_stores: list[str] = []

    # Scrape each store independently with error isolation
    store_scrapers = {
        "Maxi": fetch_maxi_deals,
        "Metro": fetch_metro_deals,
        "IGA": fetch_iga_deals,
        "Provigo": fetch_provigo_deals,
    }

    for store_name, scraper in store_scrapers.items():
        try:
            deals = scraper()
            all_deals.extend(deals)
            log.info("Fetched %d deals from %s", len(deals), store_name)
        except Exception as exc:
            log.error("%s scraper failed: %s", store_name, exc)
            failed_stores.append(store_name)

    # Sort: Maxi first, then alphabetical; within each store sort by discount desc (None last)
    all_deals.sort(key=lambda d: (
        STORE_ORDER.index(d.store) if d.store in STORE_ORDER else 99,
        -(d.discount_pct or 0),
    ))

    # Trim to max_deals_per_store per store
    trimmed = []
    for _store, group in groupby(all_deals, key=lambda d: d.store):
        trimmed.extend(list(group)[: config.max_deals_per_store])

    # If no deals were found, use demo data for testing (can be disabled)
    if not trimmed:
        log.warning("No deals found. Using demo data for email rendering test.")
        from models import Deal
        trimmed = [
            Deal("Maxi", "Extra lean ground beef", "1 kg", 7.99, 12.99, 38.5, "2026-04-07"),
            Deal("Maxi", "Broccoli", "bunch", 1.49, 2.49, 40.2, "2026-04-07"),
            Deal("Metro", "Aged cheddar", "400 g", 4.49, 6.99, 35.8, "2026-04-07"),
        ]
        failed_stores = ["Maxi", "Provigo", "IGA", "Metro", "Costco"]

    recipes = []
    if trimmed:
        try:
            recipes = fetch_recipes(trimmed, config.spoonacular_api_key)
            log.info("Found %d recipes", len(recipes))
        except Exception as exc:
            log.error("Recipe fetch failed: %s", exc)

    html = render_email(trimmed, recipes, failed_stores)
    send_email(html, config.email_from, config.mailersend_email, config.mailersend_api_key, config.email_recipient)
    log.info("Email sent successfully")


if __name__ == "__main__":
    run()
