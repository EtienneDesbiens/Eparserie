import pytest
from unittest.mock import patch, MagicMock
from models import Deal
from recipes import extract_ingredient, _score_recipe, fetch_recipes


def make_deal(store, name, desc="1kg", sale=5.0, orig=8.0):
    disc = round((orig - sale) / orig * 100, 1) if orig else None
    return Deal(store=store, name=name, description=desc,
                sale_price=sale, original_price=orig, discount_pct=disc, valid_until=None)


def test_extract_ingredient_strips_quantity():
    assert extract_ingredient("Extra lean ground beef 1 kg") == "ground beef"


def test_extract_ingredient_strips_filler_words():
    assert extract_ingredient("Fresh organic broccoli") == "broccoli"


def test_extract_ingredient_empty():
    assert extract_ingredient("") == ""


def test_score_recipe_all_maxi():
    deals = [make_deal("Maxi", "ground beef"), make_deal("Maxi", "broccoli")]
    raw = {
        "id": 1,
        "title": "Beef Stir Fry",
        "image": "https://img.example.com/1.jpg",
        "usedIngredients": [{"name": "ground beef"}, {"name": "broccoli"}],
        "missedIngredients": [],
    }
    score, recipe = _score_recipe(raw, deals)
    # 2 matched * 10 - 1 store * 5 + 2 maxi * 3 = 20 - 5 + 6 = 21
    assert score == 21
    assert recipe.store_count == 1
    assert len(recipe.matched_deals) == 2


def test_score_recipe_penalizes_multiple_stores():
    deals = [make_deal("Maxi", "ground beef"), make_deal("Metro", "cheddar")]
    raw = {
        "id": 2,
        "title": "Cheeseburger",
        "image": "",
        "usedIngredients": [{"name": "ground beef"}, {"name": "cheddar"}],
        "missedIngredients": [],
    }
    score, recipe = _score_recipe(raw, deals)
    # 2 matched * 10 - 2 stores * 5 + 1 maxi * 3 = 20 - 10 + 3 = 13
    assert score == 13
    assert recipe.store_count == 2


def test_fetch_recipes_returns_top_10(sample_deals):
    fake_response = [
        {"id": i, "title": f"Recipe {i}", "image": "",
         "usedIngredients": [{"name": "beef"}], "missedIngredients": []}
        for i in range(10)
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = fake_response
    mock_resp.raise_for_status = MagicMock()
    with patch("recipes.requests.get", return_value=mock_resp):
        results = fetch_recipes(sample_deals, "fake-key")
    assert len(results) == 10


def test_fetch_recipes_empty_deals():
    results = fetch_recipes([], "fake-key")
    assert results == []
