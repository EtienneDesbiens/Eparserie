from __future__ import annotations
import re
import requests
import logging
from models import Deal, Recipe

log = logging.getLogger(__name__)

FILLER_WORDS = {
    "extra", "lean", "fresh", "organic", "frozen", "boneless", "skinless",
    "sliced", "diced", "chopped", "whole", "large", "medium", "small",
    "value", "family", "pack", "bag", "box", "jar", "can", "aged",
}
_QUANTITY_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(kg|g|lb|lbs|ml|l|oz|pk|ct|x\d+)\b", re.IGNORECASE
)
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/findByIngredients"

# Try to import translation library, fall back gracefully if not available
try:
    from googletrans import Translator
    _translator = Translator()
    _has_translator = True
except ImportError:
    _translator = None
    _has_translator = False

def _translate_to_english(text: str) -> str:
    """Translate text to English using Google Translate."""
    if not text:
        return text

    if _has_translator:
        try:
            result = _translator.translate(text, src_lang="fr", dest_lang="en")
            translated = result.text if hasattr(result, "text") else str(result)
            return translated.lower()
        except Exception as e:
            log.debug("Translation failed for '%s': %s", text, e)

    return text.lower()


def extract_ingredient(name: str) -> str:
    if not name:
        return ""
    cleaned = _QUANTITY_RE.sub("", name)
    words = [w for w in cleaned.split() if w.isalpha() and w.lower() not in FILLER_WORDS]
    return " ".join(words[:3]).strip().lower()


def fetch_recipes(deals: list[Deal], api_key: str) -> list[Recipe]:
    if not deals:
        return []

    # Use all unique extracted ingredients (not capped at 10) so Spoonacular
    # has the full picture of what's on sale
    raw_ingredients = list({extract_ingredient(d.name) for d in deals if extract_ingredient(d.name)})
    if not raw_ingredients:
        return []

    # Translate ingredients to English for Spoonacular API
    translated_ingredients = list({_translate_to_english(ing) for ing in raw_ingredients if _translate_to_english(ing)})
    if any(ing != trans for ing, trans in zip(raw_ingredients, translated_ingredients)):
        log.info("Translated %d ingredients from French to English", len(raw_ingredients))

    # Spoonacular findByIngredients caps at 100 ingredients max
    translated_ingredients = translated_ingredients[:100]

    resp = requests.get(
        SPOONACULAR_URL,
        params={
            "ingredients": ",".join(translated_ingredients),
            "number": 100,
            "ranking": 2,
            "ignorepantry": "true",
            "apiKey": api_key,
        },
        timeout=10,
    )
    resp.raise_for_status()
    scored = [_score_recipe(r, deals) for r in resp.json() if _is_meal_recipe(r)]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [recipe for _, recipe in scored[:10]]


def _is_meal_recipe(raw: dict) -> bool:
    """Filter to meal recipes, excluding desserts, snacks, and drinks."""
    dish_types = raw.get("dishTypes", [])
    if not dish_types:
        return True

    exclude_types = {"dessert", "snack", "appetizer", "drink", "beverage", "sauce", "condiment"}
    # Check if any dishType is in the exclude list
    if any(dt.lower() in exclude_types for dt in dish_types):
        return False

    return True


def _score_recipe(raw: dict, deals: list[Deal]) -> tuple[float, Recipe]:
    used_ingredients = raw.get("usedIngredients", [])
    missed_ingredients = raw.get("missedIngredients", [])
    total_ingredients = len(used_ingredients) + len(missed_ingredients)

    # For each used ingredient, find the single best matching deal
    # (highest discount, or lowest price if no discount). This prevents
    # one ingredient from inflating the list with duplicate deal entries.
    matched_deals: list[Deal] = []
    for ingredient in used_ingredients:
        ing_name = ingredient["name"].lower()
        best_deal = _best_matching_deal(ing_name, deals)
        if best_deal is not None:
            matched_deals.append(best_deal)

    # Deduplicate deals — the same deal can match multiple ingredients
    seen_ids = set()
    unique_deals: list[Deal] = []
    for d in matched_deals:
        key = (d.store, d.name, d.sale_price)
        if key not in seen_ids:
            seen_ids.add(key)
            unique_deals.append(d)

    # Coverage-based scoring: what fraction of the recipe's ingredients are on sale?
    # A recipe where 8/10 ingredients are on sale beats one where 2/4 are.
    coverage = len(unique_deals) / total_ingredients if total_ingredients else 0
    maxi_count = sum(1 for d in unique_deals if d.store == "Maxi")
    stores = {d.store for d in unique_deals}
    store_penalty = (len(stores) - 1) * 5 if stores else 0

    score = coverage * 100 + maxi_count * 3 - store_penalty

    recipe_id = raw["id"]
    slug = raw["title"].lower().replace(" ", "-")
    return score, Recipe(
        name=raw["title"],
        url=f"https://spoonacular.com/recipes/{slug}-{recipe_id}",
        image_url=raw.get("image", ""),
        matched_deals=unique_deals,
        store_count=len(stores),
    )


def _best_matching_deal(ingredient: str, deals: list[Deal]) -> Deal | None:
    """Return the best deal (highest discount) matching an ingredient, or None."""
    candidates = [
        d for d in deals
        if _ingredient_matches(ingredient, f"{d.name} {d.description}".lower())
    ]
    if not candidates:
        return None
    # Prefer deals with a discount; among those, pick highest discount
    return max(candidates, key=lambda d: d.discount_pct or 0)


def _ingredient_matches(ingredient: str, deal_text: str) -> bool:
    """Check if an ingredient matches a deal by word overlap."""
    # Split ingredient and deal text into words
    ingredient_words = set(ingredient.split())
    deal_words = set(deal_text.split())
    # Match if there's any word overlap (excluding single letters)
    overlap = ingredient_words & deal_words
    return any(len(word) > 1 for word in overlap)
