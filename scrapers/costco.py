from __future__ import annotations
from playwright.sync_api import sync_playwright
from models import Deal

COSTCO_URL = "https://www.costco.ca/savings-centre.html"


def fetch_costco_deals() -> list[Deal]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page.goto(COSTCO_URL, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector(".savings-tile", timeout=30_000)
        raw_deals = _extract_deals(page)
        browser.close()
    return [_parse_deal(d) for d in raw_deals]


def _extract_deals(page) -> list[dict]:
    """Extract raw deal dicts from a Playwright page. Testable without a real browser."""
    tiles = page.query_selector_all(".savings-tile")
    raw: list[dict] = []
    for tile in tiles:
        name_el = tile.query_selector(".description")
        price_el = tile.query_selector(".your-price .value")
        orig_el = tile.query_selector(".original-price .value")
        desc_el = tile.query_selector(".unit-quantity")
        name = name_el.inner_text() if name_el else ""
        sale_price = price_el.inner_text() if price_el else ""
        if not name.strip() or not sale_price.strip():
            continue
        raw.append({
            "name": name.strip(),
            "description": desc_el.inner_text().strip() if desc_el else "",
            "sale_price": sale_price.strip(),
            "original_price": orig_el.inner_text().strip() if orig_el else "",
        })
    return raw


def _parse_price(price_str: str | None) -> float | None:
    if not price_str:
        return None
    try:
        return float(price_str.replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def _parse_deal(raw: dict) -> Deal:
    sale_price = _parse_price(raw["sale_price"]) or 0.0
    original_price = _parse_price(raw["original_price"])
    discount_pct: float | None = None
    if original_price and original_price > sale_price:
        discount_pct = round((original_price - sale_price) / original_price * 100, 1)
    return Deal(
        store="Costco",
        name=raw["name"],
        description=raw["description"],
        sale_price=sale_price,
        original_price=original_price,
        discount_pct=discount_pct,
        valid_until=None,
    )
