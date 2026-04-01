"""Tests for shared store flyer scraper."""
import pytest
from unittest.mock import patch, MagicMock
from scrapers.utils import _parse_price, _parse_items
from scrapers.store_flyer import fetch_store_deals

FAKE_ITEMS = [
    {
        "name": "Extra lean ground beef",
        "description": "1 kg",
        "current_price": 7.99,
        "original_price": 12.99,
        "valid_to": "2026-04-07",
    },
    {
        "name": "Broccoli",
        "description": "bunch",
        "current_price": 1.49,
        "original_price": 2.49,
        "valid_to": "2026-04-07",
    },
    {
        "name": "No price item",
        "description": "",
        "current_price": None,
        "original_price": None,
        "valid_to": None,
    },
]


def test_parse_price_with_dollar_sign():
    assert _parse_price("$12.99") == 12.99


def test_parse_price_with_comma():
    assert _parse_price("$1,299.99") == 1299.99


def test_parse_price_empty():
    assert _parse_price("") is None


def test_parse_price_none():
    assert _parse_price(None) is None


def test_parse_items_calculates_discount():
    deals = _parse_items("Maxi", FAKE_ITEMS)
    assert len(deals) == 2  # item with no price is skipped
    assert deals[0].store == "Maxi"
    assert deals[0].sale_price == 7.99
    assert deals[0].original_price == 12.99
    assert deals[0].discount_pct == pytest.approx(38.5, abs=0.1)


def test_parse_items_no_original_price():
    items = [{"name": "Chicken", "description": "2kg", "current_price": 9.99, "original_price": None, "valid_to": None}]
    deals = _parse_items("Metro", items)
    assert deals[0].original_price is None
    assert deals[0].discount_pct is None


def test_fetch_store_deals_captures_flipp_json():
    """Test that fetch_store_deals intercepts Flipp widget JSON responses."""
    mock_response = MagicMock()
    mock_response.url = "https://cdn.flipp.com/flyerkit/publications/12345/items"
    mock_response.json.return_value = FAKE_ITEMS

    with patch("scrapers.store_flyer.sync_playwright") as MockPlaywright:
        mock_context = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        MockPlaywright.return_value.__enter__.return_value = mock_context
        mock_context.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Simulate the on_response callback being called
        def simulate_response_handler(event_name, callback):
            if event_name == "response":
                callback(mock_response)

        mock_page.on.side_effect = simulate_response_handler
        mock_page.goto.return_value = None

        deals = fetch_store_deals("Maxi")

    assert len(deals) == 2
    assert deals[0].store == "Maxi"
    assert deals[0].name == "Extra lean ground beef"


def test_fetch_store_deals_empty_on_no_capture():
    """Test that fetch_store_deals raises error if no Flipp data captured."""
    with patch("scrapers.store_flyer.sync_playwright") as MockPlaywright:
        mock_context = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()

        MockPlaywright.return_value.__enter__.return_value = mock_context
        mock_context.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.on.return_value = None
        mock_page.goto.return_value = None

        with pytest.raises(RuntimeError, match="No Flipp widget data"):
            fetch_store_deals("Maxi")


def test_fetch_store_deals_invalid_store():
    """Test that invalid store name raises error."""
    with pytest.raises(ValueError, match="Unknown store"):
        fetch_store_deals("Walmart")
