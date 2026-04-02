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
    # coverage = 2/2 = 1.0 → 100 + 2 maxi * 3 - (1-1)*5 = 106
    assert score == pytest.approx(106.0)
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
    # coverage = 2/2 = 1.0 → 100 + 1 maxi * 3 - (2-1)*5 = 98
    assert score == pytest.approx(98.0)
    assert recipe.store_count == 2


def test_score_recipe_coverage_beats_absolute_count():
    """A recipe with 3/4 ingredients on sale beats one with 2/10."""
    deals_a = [make_deal("Maxi", "chicken"), make_deal("Maxi", "broccoli"), make_deal("Maxi", "garlic")]
    raw_a = {
        "id": 10, "title": "Chicken Stir Fry", "image": "",
        "usedIngredients": [{"name": "chicken"}, {"name": "broccoli"}, {"name": "garlic"}],
        "missedIngredients": [{"name": "soy sauce"}],  # 3/4 = 75% coverage
    }
    deals_b = [make_deal("Maxi", "beef"), make_deal("Maxi", "onion")]
    raw_b = {
        "id": 11, "title": "Complex Beef Stew", "image": "",
        "usedIngredients": [{"name": "beef"}, {"name": "onion"}],
        "missedIngredients": [{"name": x} for x in ["wine", "herbs", "carrots", "stock", "bay leaf", "flour", "butter", "tomato paste"]],  # 2/10 = 20%
    }
    all_deals = deals_a + deals_b
    score_a, _ = _score_recipe(raw_a, all_deals)
    score_b, _ = _score_recipe(raw_b, all_deals)
    assert score_a > score_b


def test_score_recipe_deduplicates_matched_deals():
    """Multiple deals matching the same ingredient should only produce one entry."""
    deals = [
        make_deal("Maxi", "chicken breast", sale=7.99, orig=12.99),
        make_deal("Maxi", "chicken thighs", sale=5.99, orig=9.99),
        make_deal("Maxi", "chicken wings", sale=9.99, orig=14.99),
    ]
    raw = {
        "id": 3, "title": "Roast Chicken", "image": "",
        "usedIngredients": [{"name": "chicken"}],
        "missedIngredients": [],
    }
    _, recipe = _score_recipe(raw, deals)
    # Should only have one deal per ingredient (the best one)
    assert len(recipe.matched_deals) == 1


def test_fetch_recipes_returns_top_5(sample_deals):
    # Simulate 5 API calls each returning 20 unique recipes (100 total candidates)
    call_count = 0
    def fake_get(*args, **kwargs):
        nonlocal call_count
        offset = call_count * 20
        call_count += 1
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [
            {"id": offset + i, "title": f"Recipe {offset + i}", "image": "",
             "usedIngredients": [{"name": "beef"}], "missedIngredients": []}
            for i in range(20)
        ]
        return mock_resp

    with patch("recipes.requests.get", side_effect=fake_get):
        results = fetch_recipes(sample_deals, "fake-key")
    assert len(results) == 5


def test_fetch_recipes_empty_deals():
    results = fetch_recipes([], "fake-key")
    assert results == []
