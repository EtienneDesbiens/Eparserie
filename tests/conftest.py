import pytest
from models import Deal, Recipe


@pytest.fixture
def maxi_deal():
    return Deal(
        store="Maxi",
        name="Extra lean ground beef",
        description="1 kg",
        sale_price=7.99,
        original_price=12.99,
        discount_pct=38.5,
        valid_until="2026-04-07",
    )


@pytest.fixture
def metro_deal():
    return Deal(
        store="Metro",
        name="Aged cheddar",
        description="400 g",
        sale_price=4.49,
        original_price=6.99,
        discount_pct=35.8,
        valid_until="2026-04-07",
    )


@pytest.fixture
def costco_deal():
    return Deal(
        store="Costco",
        name="Atlantic salmon fillet",
        description="2 kg",
        sale_price=29.99,
        original_price=None,
        discount_pct=None,
        valid_until=None,
    )


@pytest.fixture
def sample_deals(maxi_deal, metro_deal, costco_deal):
    return [maxi_deal, metro_deal, costco_deal]


@pytest.fixture
def sample_recipe(maxi_deal):
    return Recipe(
        name="Beef Stir Fry",
        url="https://spoonacular.com/recipes/beef-stir-fry-123456",
        image_url="https://img.example.com/1.jpg",
        matched_deals=[maxi_deal],
        store_count=1,
    )
