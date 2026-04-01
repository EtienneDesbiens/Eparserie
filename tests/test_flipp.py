import pytest
from unittest.mock import patch, MagicMock
from scrapers.flipp import fetch_flipp_deals, _parse_items

FAKE_PUBLICATIONS = [
    {"id": 1001, "merchant_name": "Maxi"},
    {"id": 1002, "merchant_name": "IGA"},
    {"id": 1003, "merchant_name": "Walmart"},  # should be filtered out
]

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


def test_fetch_flipp_deals_filters_stores():
    pub_response = MagicMock()
    pub_response.json.return_value = FAKE_PUBLICATIONS
    pub_response.raise_for_status = MagicMock()

    items_response = MagicMock()
    items_response.json.return_value = FAKE_ITEMS
    items_response.raise_for_status = MagicMock()

    with patch("scrapers.flipp.requests.get", side_effect=[pub_response, items_response, items_response]) as mock_get:
        deals = fetch_flipp_deals("J1H2B4")

    # 3 publications returned but only Maxi and IGA pass the filter → 2 items calls
    assert mock_get.call_count == 3  # 1 publications + 2 items
    stores = {d.store for d in deals}
    assert "Walmart" not in stores
    assert "Maxi" in stores
    assert "IGA" in stores
