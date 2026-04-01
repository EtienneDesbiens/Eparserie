import pytest
from scrapers.costco import _parse_price, _parse_deal, _extract_deals


def test_parse_price_with_dollar_sign():
    assert _parse_price("$12.99") == 12.99


def test_parse_price_with_comma():
    assert _parse_price("$1,299.99") == 1299.99


def test_parse_price_empty():
    assert _parse_price("") is None


def test_parse_price_none():
    assert _parse_price(None) is None


def test_parse_deal_with_both_prices():
    raw = {
        "name": "Atlantic Salmon Fillet",
        "description": "2 kg",
        "sale_price": "$29.99",
        "original_price": "$39.99",
    }
    deal = _parse_deal(raw)
    assert deal.store == "Costco"
    assert deal.sale_price == 29.99
    assert deal.original_price == 39.99
    assert deal.discount_pct == pytest.approx(25.0, abs=0.1)
    assert deal.valid_until is None


def test_parse_deal_without_original_price():
    raw = {
        "name": "Kirkland Olive Oil",
        "description": "3 L",
        "sale_price": "$18.99",
        "original_price": "",
    }
    deal = _parse_deal(raw)
    assert deal.original_price is None
    assert deal.discount_pct is None


def test_extract_deals_skips_empty_names():
    class FakeElement:
        def __init__(self, text):
            self._text = text
        def inner_text(self):
            return self._text

    class FakeTile:
        def __init__(self, name, price, orig, desc):
            self._name = name
            self._price = price
            self._orig = orig
            self._desc = desc
        def query_selector(self, selector):
            mapping = {
                ".description": FakeElement(self._name) if self._name else None,
                ".your-price .value": FakeElement(self._price) if self._price else None,
                ".original-price .value": FakeElement(self._orig) if self._orig else None,
                ".unit-quantity": FakeElement(self._desc) if self._desc else None,
            }
            return mapping.get(selector)

    class FakePage:
        def query_selector_all(self, selector):
            return [
                FakeTile("Salmon", "$29.99", "$39.99", "2 kg"),
                FakeTile("", "$5.00", "", ""),  # no name — should be skipped
            ]

    results = _extract_deals(FakePage())
    assert len(results) == 1
    assert results[0]["name"] == "Salmon"
