from __future__ import annotations
import logging
from itertools import groupby

from config import load_config
from models import Deal
from scrapers.maxi import fetch_maxi_deals
from scrapers.metro import fetch_metro_deals
from scrapers.iga import fetch_iga_deals
from scrapers.provigo import fetch_provigo_deals
from recipes import fetch_recipes
from email_sender import render_email, send_email, STORE_ORDER

# Non-food product keywords to exclude
NON_FOOD_KEYWORDS = {
    "shampoo", "conditioner", "soap", "detergent", "laundry", "dish liquid",
    "paper towel", "tissue", "napkin", "toilet", "feminine", "deodorant",
    "toothpaste", "toothbrush", "mouthwash", "floss", "vitamin", "supplement",
    "medicine", "medication", "aspirin", "ibuprofen", "pain relief",
    "pet food", "dog food", "cat food", "pet treat", "pet", "animal", "animaux", "chat", "chien", "cat", "dog",
    "garbage bag", "plastic bag", "trash", "foil", "wrap", "parchment",
    "cleaning", "bleach", "disinfectant", "air freshener",
    "cookware", "ensemble", "table", "outil", "tool",
}


def _is_food_item(deal: Deal) -> bool:
    """Check if a deal is a food/beverage item by filtering non-food keywords."""
    text = f"{deal.name} {deal.description}".lower()
    return not any(keyword in text for keyword in NON_FOOD_KEYWORDS)


def _is_reasonable_price(deal: Deal, max_price: float = 50.0) -> bool:
    """Filter out items over a reasonable price threshold."""
    return deal.sale_price <= max_price


def _categorize_deal(deal: Deal) -> str:
    """Categorize a deal based on its name and description."""
    text = f"{deal.name} {deal.description}".lower()

    # Define category keywords
    categories = {
        "Produce": {
            "apple", "banana", "orange", "grape", "strawberry", "blueberry",
            "carrot", "broccoli", "spinach", "lettuce", "tomato", "onion",
            "potato", "pepper", "cucumber", "mushroom", "avocado", "lime",
            "lemon", "fruit", "vegetable", "veggie", "produce",
            "pomme", "banane", "orange", "fraise", "carotte", "brocoli",
            "tomate", "oignon", "patate", "legume",
        },
        "Meat & Seafood": {
            "chicken", "beef", "pork", "lamb", "veal", "turkey", "ham",
            "salmon", "tuna", "cod", "trout", "shrimp", "fish", "seafood",
            "steak", "ground", "breast", "wing", "leg",
            "poulet", "boeuf", "porc", "agneau", "veau", "dinde", "jambon",
            "saumon", "thon", "morue", "truite", "crevette", "poisson",
        },
        "Dairy & Eggs": {
            "milk", "cheese", "yogurt", "butter", "cream", "egg",
            "fromage", "lait", "beurre", "creme", "oeuf",
        },
        "Frozen": {
            "frozen", "ice", "fries", "pizza", "tv dinner", "popsicle",
            "surgele", "glace",
        },
        "Pantry": {
            "pasta", "rice", "bread", "cereal", "flour", "sugar", "oil",
            "sauce", "jam", "peanut butter", "canned", "beans", "lentils",
            "pates", "riz", "pain", "sucre", "huile",
        },
        "Beverages": {
            "juice", "milk", "coffee", "tea", "soda", "water", "wine",
            "beer", "smoothie", "drink",
            "jus", "cafe", "the", "eau",
        },
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "Other"


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

    # Filter to food items only
    food_deals = [d for d in all_deals if _is_food_item(d)]
    log.info("Filtered to %d food items (removed %d non-food)", len(food_deals), len(all_deals) - len(food_deals))

    # Filter to reasonable prices (under $50)
    priced_deals = [d for d in food_deals if _is_reasonable_price(d)]
    log.info("Filtered to %d reasonably priced items (removed %d over $50)", len(priced_deals), len(food_deals) - len(priced_deals))

    # Categorize deals
    for deal in priced_deals:
        deal.category = _categorize_deal(deal)

    all_deals = priced_deals

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

    html = render_email(trimmed, recipes, failed_stores, config.postal_code)
    send_email(html, config.email_from, config.mailersend_email, config.mailersend_api_key, config.email_recipients, config.email_from_name)
    log.info("Email sent successfully")


if __name__ == "__main__":
    run()
