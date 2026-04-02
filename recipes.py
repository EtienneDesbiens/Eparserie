from __future__ import annotations
import re
import requests
from models import Deal, Recipe

FILLER_WORDS = {
    "extra", "lean", "fresh", "organic", "frozen", "boneless", "skinless",
    "sliced", "diced", "chopped", "whole", "large", "medium", "small",
    "value", "family", "pack", "bag", "box", "jar", "can", "aged",
}
_QUANTITY_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(kg|g|lb|lbs|ml|l|oz|pk|ct|x\d+)\b", re.IGNORECASE
)
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/findByIngredients"


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
    resp = requests.get(
        SPOONACULAR_URL,
        params={
            "ingredients": ",".join(ingredients),
            "number": 10,
            "ranking": 1,
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
    used_names = {i["name"].lower() for i in raw.get("usedIngredients", [])}
    matched = [d for d in deals if any(u in d.name.lower() for u in used_names)]
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
