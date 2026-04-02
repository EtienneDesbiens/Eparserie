"""Tests for the Maxi scraper."""
import pytest
from unittest.mock import patch
from models import Deal
from scrapers.maxi import fetch_maxi_deals


def test_fetch_maxi_deals_calls_store_flyer():
    """fetch_maxi_deals should call fetch_store_deals with 'Maxi'."""
    mock_deals = [
        Deal("Maxi", "Chicken breast", "1kg", 8.99, 13.99, 35.7, "2026-04-07"),
        Deal("Maxi", "Broccoli", "bunch", 1.49, None, None, "2026-04-07"),
    ]

    with patch("scrapers.maxi.fetch_store_deals", return_value=mock_deals) as mock_fetch:
        deals = fetch_maxi_deals()

    mock_fetch.assert_called_once_with("Maxi")
    assert deals == mock_deals


def test_fetch_maxi_deals_propagates_exceptions():
    """fetch_maxi_deals should propagate exceptions from fetch_store_deals."""
    with patch("scrapers.maxi.fetch_store_deals", side_effect=RuntimeError("No deals found")):
        with pytest.raises(RuntimeError, match="No deals found"):
            fetch_maxi_deals()
