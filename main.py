from __future__ import annotations
import logging
from itertools import groupby

from config import load_config
from scrapers.flipp import fetch_flipp_deals
from scrapers.costco import fetch_costco_deals
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

    try:
        flipp_deals = fetch_flipp_deals(config.postal_code)
        all_deals.extend(flipp_deals)
        log.info("Fetched %d deals from Flipp", len(flipp_deals))
    except Exception as exc:
        log.error("Flipp scraper failed: %s", exc)
        log.warning("FLIPP API is currently inaccessible (blocking requests). Try: https://flipp.com manually to confirm.")
        failed_stores.extend(["Maxi", "Provigo", "IGA", "Metro"])

    # Temporarily disabled - Costco is blocking Playwright automation
    # try:
    #     costco_deals = fetch_costco_deals()
    #     all_deals.extend(costco_deals)
    #     log.info("Fetched %d deals from Costco", len(costco_deals))
    # except Exception as exc:
    #     log.error("Costco scraper failed: %s", exc)
    #     failed_stores.append("Costco")

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
    send_email(html, config.email_from, config.brevo_email, config.brevo_api_key, config.email_recipient)
    log.info("Email sent successfully")


if __name__ == "__main__":
    run()
