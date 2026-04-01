from models import Deal, Recipe


def test_deal_with_discount():
    deal = Deal(
        store="Maxi",
        name="Extra lean ground beef",
        description="1 kg",
        sale_price=7.99,
        original_price=12.99,
        discount_pct=38.5,
        valid_until="2026-04-07",
    )
    assert deal.store == "Maxi"
    assert deal.sale_price == 7.99
    assert deal.discount_pct == 38.5


def test_deal_without_original_price():
    deal = Deal(
        store="Costco",
        name="Atlantic salmon",
        description="2 kg",
        sale_price=29.99,
        original_price=None,
        discount_pct=None,
        valid_until=None,
    )
    assert deal.original_price is None
    assert deal.discount_pct is None
    assert deal.valid_until is None


def test_recipe_fields():
    deal = Deal("Maxi", "beef", "1kg", 7.99, 12.99, 38.5, "2026-04-07")
    recipe = Recipe(
        name="Beef Stir Fry",
        url="https://spoonacular.com/recipes/beef-stir-fry-123",
        image_url="https://img.example.com/1.jpg",
        matched_deals=[deal],
        store_count=1,
    )
    assert recipe.store_count == 1
    assert len(recipe.matched_deals) == 1
