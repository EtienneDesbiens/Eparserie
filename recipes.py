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

# Common French-to-English grocery terms for fallback
_FRENCH_ENGLISH_FOODS = {
    "poulet": "chicken",
    "porc": "pork",
    "boeuf": "beef",
    "veau": "veal",
    "agneau": "lamb",
    "poisson": "fish",
    "saumon": "salmon",
    "truite": "trout",
    "morue": "cod",
    "oeufs": "eggs",
    "oeuf": "egg",
    "fromage": "cheese",
    "lait": "milk",
    "yogourt": "yogurt",
    "beurre": "butter",
    "pain": "bread",
    "riz": "rice",
    "pates": "pasta",
    "patates": "potatoes",
    "pommes": "apples",
    "oranges": "oranges",
    "bananes": "bananas",
    "fraises": "strawberries",
    "bleuets": "blueberries",
    "brocoli": "broccoli",
    "chou": "cabbage",
    "carrotes": "carrots",
    "carotte": "carrot",
    "oignons": "onions",
    "oignon": "onion",
    "tomates": "tomatoes",
    "tomate": "tomato",
    "laitue": "lettuce",
    "epinards": "spinach",
    "haricots": "beans",
    "pois": "peas",
    "mais": "corn",
    "champignons": "mushrooms",
    "champignon": "mushroom",
    "cerises": "cherries",
    "raisins": "grapes",
}


def _translate_to_english(text: str) -> str:
    """Translate French text to English, with fallback to manual mapping."""
    if not text:
        return text

    lower_text = text.lower()

    # Try manual mapping first (fastest, most reliable)
    if lower_text in _FRENCH_ENGLISH_FOODS:
        return _FRENCH_ENGLISH_FOODS[lower_text]

    # Try googletrans if available
    if _has_translator:
        try:
            # googletrans API: result has .text attribute
            result = _translator.translate(text, src_lang="fr", dest_lang="en")
            translated = result.text if hasattr(result, "text") else str(result)
            return translated.lower()
        except Exception as e:
            log.debug("Translation failed for '%s': %s", text, e)
            return lower_text

    return lower_text


def extract_ingredient(name: str) -> str:
    if not name:
        return ""
    cleaned = _QUANTITY_RE.sub("", name)
    words = [w for w in cleaned.split() if w.isalpha() and w.lower() not in FILLER_WORDS]
    return " ".join(words[:3]).strip().lower()


def fetch_recipes(deals: list[Deal], api_key: str) -> list[Recipe]:
    if not deals:
        return []
    ingredients = list({extract_ingredient(d.name) for d in deals if extract_ingredient(d.name)})[:10]
    if not ingredients:
        return []

    # Translate ingredients to English for Spoonacular API
    translated_ingredients = [_translate_to_english(ing) for ing in ingredients]
    if any(ing != trans for ing, trans in zip(ingredients, translated_ingredients)):
        log.info("Translated ingredients from French: %s -> %s", ingredients, translated_ingredients)

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
    used_names = {i["name"].lower() for i in used_ingredients}

    # Match deals: check if any ingredient word appears in deal name
    matched = []
    for deal in deals:
        deal_text = f"{deal.name} {deal.description}".lower()
        # Check if any ingredient appears in the deal text
        if any(_ingredient_matches(u, deal_text) for u in used_names):
            matched.append(deal)

    maxi_count = sum(1 for d in matched if d.store == "Maxi")
    stores = {d.store for d in matched}
    score = len(matched) * 10 - len(stores) * 5 + maxi_count * 3
    recipe_id = raw["id"]
    slug = raw["title"].lower().replace(" ", "-")
    return score, Recipe(
        name=raw["title"],
        url=f"https://spoonacular.com/recipes/{slug}-{recipe_id}",
        image_url=raw.get("image", ""),
        matched_deals=matched,
        store_count=len(stores),
    )


def _ingredient_matches(ingredient: str, deal_text: str) -> bool:
    """Check if an ingredient matches a deal by word overlap."""
    # Split ingredient and deal text into words
    ingredient_words = set(ingredient.split())
    deal_words = set(deal_text.split())
    # Match if there's any word overlap (excluding single letters)
    overlap = ingredient_words & deal_words
    return any(len(word) > 1 for word in overlap)
