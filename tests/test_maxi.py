"""Tests for the Maxi HTTP scraper."""
import pytest
from unittest.mock import patch, MagicMock
from models import Deal
from scrapers.maxi import fetch_maxi_deals, _get_maxi_publications, _get_products


# --- Shared fixtures ---

FAKE_PUBLICATIONS_RESPONSE = [
    {"id": 2001, "merchant_name": "Maxi"},
    {"id": 2002, "merchant_name": "Maxi"},
    {"id": 3001, "merchant_name": "IGA"},
]

FAKE_PRODUCTS_LIST = [
    {
        "name": "Chicken breast",
        "description": "per kg",
        "price_text": "$8.99",
        "original_price": "13.99",
        "valid_to": "2026-04-07",
    },
    {
        "name": "Broccoli",
        "description": "bunch",
        "price_text": "$1.49",
        "original_price": None,
        "valid_to": "2026-04-07",
    },
    {
        "name": "No price item",
        "description": "",
        "price_text": None,
        "original_price": None,
        "valid_to": None,
    },
]

FAKE_PRODUCTS_DICT = {"products": FAKE_PRODUCTS_LIST}


def _mock_json_response(payload, content_type="application/json"):
    r = MagicMock()
    r.raise_for_status = MagicMock()
    r.headers = {"content-type": content_type}
    r.json.return_value = payload
    return r


# --- Unit tests for _get_maxi_publications ---

def test_get_maxi_publications_filters_to_maxi_only():
    with patch("scrapers.maxi.requests.get",
               return_value=_mock_json_response(FAKE_PUBLICATIONS_RESPONSE)):
        pubs = _get_maxi_publications("H2X2X3")
    assert len(pubs) == 2
    assert all(p["merchant_name"] == "Maxi" for p in pubs)
    assert all(p["id"] in (2001, 2002) for p in pubs)


def test_get_maxi_publications_raises_on_non_json():
    with patch("scrapers.maxi.requests.get",
               return_value=_mock_json_response({}, content_type="text/html")):
        with pytest.raises(RuntimeError, match="non-JSON"):
            _get_maxi_publications("H2X2X3")


def test_get_maxi_publications_raises_on_network_error():
    import requests as req
    with patch("scrapers.maxi.requests.get", side_effect=req.RequestException("timeout")):
        with pytest.raises(RuntimeError, match="Failed to reach Flipp publications API"):
            _get_maxi_publications("H2X2X3")


def test_get_maxi_publications_returns_empty_when_no_maxi():
    only_iga = [{"id": 3001, "merchant_name": "IGA"}]
    with patch("scrapers.maxi.requests.get",
               return_value=_mock_json_response(only_iga)):
        pubs = _get_maxi_publications("H2X2X3")
    assert pubs == []


# --- Unit tests for _get_products ---

def test_get_products_handles_list_response():
    with patch("scrapers.maxi.requests.get",
               return_value=_mock_json_response(FAKE_PRODUCTS_LIST)):
        items = _get_products(2001)
    assert len(items) == 3


def test_get_products_handles_dict_response():
    with patch("scrapers.maxi.requests.get",
               return_value=_mock_json_response(FAKE_PRODUCTS_DICT)):
        items = _get_products(2001)
    assert len(items) == 3


def test_get_products_handles_unexpected_shape():
    with patch("scrapers.maxi.requests.get",
               return_value=_mock_json_response({"unexpected_key": []})):
        items = _get_products(2001)
    assert items == []


# --- Integration-style tests for fetch_maxi_deals ---

def test_fetch_maxi_deals_happy_path():
    pub_resp = _mock_json_response(FAKE_PUBLICATIONS_RESPONSE)
    items_resp = _mock_json_response(FAKE_PRODUCTS_LIST)

    with patch("scrapers.maxi.requests.get",
               side_effect=[pub_resp, items_resp, items_resp]):
        deals = fetch_maxi_deals()

    # 2 valid items per publication × 2 publications = 4 deals
    assert len(deals) == 4
    assert all(d.store == "Maxi" for d in deals)


def test_fetch_maxi_deals_parses_price_text_format():
    pub_resp = _mock_json_response([{"id": 2001, "merchant_name": "Maxi"}])
    items_resp = _mock_json_response(FAKE_PRODUCTS_LIST)

    with patch("scrapers.maxi.requests.get", side_effect=[pub_resp, items_resp]):
        deals = fetch_maxi_deals()

    chicken = next(d for d in deals if d.name == "Chicken breast")
    assert chicken.sale_price == 8.99
    assert chicken.original_price == 13.99
    assert chicken.discount_pct == pytest.approx(35.7, abs=0.1)


def test_fetch_maxi_deals_raises_when_no_publications_found():
    pub_resp = _mock_json_response([{"id": 3001, "merchant_name": "IGA"}])
    with patch("scrapers.maxi.requests.get", return_value=pub_resp):
        with patch("scrapers.maxi._fetch_maxi_playwright",
                   side_effect=RuntimeError("No Flipp widget data")):
            with pytest.raises(RuntimeError):
                fetch_maxi_deals()


def test_fetch_maxi_deals_uses_env_postal_code(monkeypatch):
    monkeypatch.setenv("POSTAL_CODE", "G1V4G5")
    pub_resp = _mock_json_response([{"id": 2001, "merchant_name": "Maxi"}])
    items_resp = _mock_json_response(FAKE_PRODUCTS_LIST)

    with patch("scrapers.maxi.requests.get",
               side_effect=[pub_resp, items_resp]) as mock_get:
        fetch_maxi_deals()

    first_call_kwargs = mock_get.call_args_list[0]
    assert first_call_kwargs[1]["params"]["postal_code"] == "G1V4G5"


def test_fetch_maxi_deals_default_postal_code(monkeypatch):
    monkeypatch.delenv("POSTAL_CODE", raising=False)
    pub_resp = _mock_json_response([{"id": 2001, "merchant_name": "Maxi"}])
    items_resp = _mock_json_response(FAKE_PRODUCTS_LIST)

    with patch("scrapers.maxi.requests.get",
               side_effect=[pub_resp, items_resp]) as mock_get:
        fetch_maxi_deals()

    first_call_kwargs = mock_get.call_args_list[0]
    assert first_call_kwargs[1]["params"]["postal_code"] == "H2X2X3"


def test_fetch_maxi_deals_falls_back_to_playwright_on_http_failure():
    """When HTTP API is blocked, headed browser fallback is used."""
    # HTTP call returns HTML (blocked)
    blocked_resp = _mock_json_response({}, content_type="text/html")

    with patch("scrapers.maxi.requests.get", return_value=blocked_resp):
        with patch(
            "scrapers.maxi._fetch_maxi_playwright",
            return_value=[Deal("Maxi", "Chicken", "1kg", 8.99, 13.99, 35.7, None)],
        ) as mock_pw:
            deals = fetch_maxi_deals()

    mock_pw.assert_called_once()
    assert len(deals) == 1
    assert deals[0].store == "Maxi"
    assert deals[0].name == "Chicken"
