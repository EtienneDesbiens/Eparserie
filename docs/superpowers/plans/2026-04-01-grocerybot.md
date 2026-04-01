# GroceryBot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python script that scrapes grocery deals from 5 Sherbrooke stores, scores recipes against those deals, and sends a formatted HTML email via Gmail.

**Architecture:** Two scrapers (Flipp API for Maxi/Provigo/IGA/Metro, Playwright for Costco) produce `Deal` objects. A recipe module queries Spoonacular and scores results to minimize store trips and favour Maxi. An email module renders a Jinja2 template and sends it via Gmail SMTP. `main.py` orchestrates the pipeline with per-scraper error isolation.

**Tech Stack:** Python 3.11+, `playwright`, `requests`, `jinja2`, `python-dotenv`, `pytest`

---

## File Map

| File | Responsibility |
|---|---|
| `models.py` | `Deal` and `Recipe` dataclasses |
| `config.py` | Load and validate `.env` into a `Config` dataclass |
| `scrapers/__init__.py` | Empty package marker |
| `scrapers/flipp.py` | Flipp API client → list of `Deal` |
| `scrapers/costco.py` | Playwright scraper → list of `Deal` |
| `recipes.py` | Ingredient extraction, Spoonacular API, recipe scoring |
| `email_sender.py` | Render Jinja2 template, send via Gmail SMTP |
| `templates/email.html` | Jinja2 HTML email template |
| `main.py` | Orchestrate pipeline end-to-end |
| `tests/conftest.py` | Shared pytest fixtures |
| `tests/test_models.py` | Model validation |
| `tests/test_config.py` | Config loading |
| `tests/test_flipp.py` | Flipp scraper with mocked HTTP |
| `tests/test_costco.py` | Costco pure functions + mocked page |
| `tests/test_recipes.py` | Ingredient extraction, scoring, mocked HTTP |
| `tests/test_email_sender.py` | Template rendering + mocked SMTP |
| `tests/test_main.py` | Full pipeline with all I/O mocked |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `tests/__init__.py`
- Create: `scrapers/__init__.py`

- [ ] **Step 1: Create `requirements.txt`**

```
requests==2.31.0
playwright==1.44.0
jinja2==3.1.4
python-dotenv==1.0.1
pytest==8.2.0
pytest-mock==3.14.0
```

- [ ] **Step 2: Create `.env.example`**

```
POSTAL_CODE=J1H2B4
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_RECIPIENT=you@gmail.com
SPOONACULAR_API_KEY=your_key_here
MAX_DEALS_PER_STORE=10
```

- [ ] **Step 3: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
grocerybot.log
.superpowers/
```

- [ ] **Step 4: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
```

- [ ] **Step 5: Create empty package markers**

Create `tests/__init__.py` and `scrapers/__init__.py` as empty files.

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: no errors, chromium downloads successfully.

- [ ] **Step 7: Commit**

```bash
git init
git add requirements.txt .env.example .gitignore pytest.ini tests/__init__.py scrapers/__init__.py
git commit -m "chore: project scaffolding"
```

---

## Task 2: Data Models

**Files:**
- Create: `models.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_models.py -v
```

Expected: `ImportError: No module named 'models'`

- [ ] **Step 3: Create `models.py`**

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Deal:
    store: str
    name: str
    description: str
    sale_price: float
    original_price: float | None
    discount_pct: float | None
    valid_until: str | None

@dataclass
class Recipe:
    name: str
    url: str
    image_url: str
    matched_deals: list[Deal]
    store_count: int
```

- [ ] **Step 4: Create `tests/conftest.py`**

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add models.py tests/conftest.py tests/test_models.py
git commit -m "feat: add Deal and Recipe dataclasses"
```

---

## Task 3: Config Loader

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_config.py`:

```python
import pytest
from unittest.mock import patch
from config import load_config, Config

VALID_ENV = {
    "POSTAL_CODE": "J1H2B4",
    "GMAIL_ADDRESS": "test@gmail.com",
    "GMAIL_APP_PASSWORD": "abcd-efgh-ijkl-mnop",
    "EMAIL_RECIPIENT": "me@gmail.com",
    "SPOONACULAR_API_KEY": "abc123",
    "MAX_DEALS_PER_STORE": "10",
}

def test_load_config_returns_config():
    with patch.dict("os.environ", VALID_ENV, clear=True):
        cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.postal_code == "J1H2B4"
    assert cfg.max_deals_per_store == 10

def test_load_config_default_max_deals():
    env = {k: v for k, v in VALID_ENV.items() if k != "MAX_DEALS_PER_STORE"}
    with patch.dict("os.environ", env, clear=True):
        cfg = load_config()
    assert cfg.max_deals_per_store == 10

def test_load_config_missing_required_key():
    env = {k: v for k, v in VALID_ENV.items() if k != "SPOONACULAR_API_KEY"}
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(KeyError):
            load_config()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_config.py -v
```

Expected: `ImportError: No module named 'config'`

- [ ] **Step 3: Create `config.py`**

```python
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    postal_code: str
    gmail_address: str
    gmail_app_password: str
    email_recipient: str
    spoonacular_api_key: str
    max_deals_per_store: int

def load_config() -> Config:
    load_dotenv()
    return Config(
        postal_code=os.environ["POSTAL_CODE"],
        gmail_address=os.environ["GMAIL_ADDRESS"],
        gmail_app_password=os.environ["GMAIL_APP_PASSWORD"],
        email_recipient=os.environ["EMAIL_RECIPIENT"],
        spoonacular_api_key=os.environ["SPOONACULAR_API_KEY"],
        max_deals_per_store=int(os.getenv("MAX_DEALS_PER_STORE", "10")),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_config.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add config loader"
```

---

## Task 4: Flipp Scraper

**Files:**
- Create: `scrapers/flipp.py`
- Create: `tests/test_flipp.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_flipp.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_flipp.py -v
```

Expected: `ImportError: No module named 'scrapers.flipp'`

- [ ] **Step 3: Create `scrapers/flipp.py`**

```python
from __future__ import annotations
import requests
from models import Deal

STORE_NAMES = {"Maxi", "Provigo", "IGA", "Metro"}
PUBLICATIONS_URL = "https://flipp.com/api/2/publications"
ITEMS_URL = "https://cdn.flipp.com/flyerkit/publications/{pub_id}/items"


def fetch_flipp_deals(postal_code: str) -> list[Deal]:
    publications = _get_publications(postal_code)
    deals: list[Deal] = []
    for pub in publications:
        if pub.get("merchant_name") in STORE_NAMES:
            items = _get_items(pub["id"])
            deals.extend(_parse_items(pub["merchant_name"], items))
    return deals


def _get_publications(postal_code: str) -> list[dict]:
    resp = requests.get(
        PUBLICATIONS_URL,
        params={"locale": "en-CA", "postal_code": postal_code},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def _get_items(pub_id: int) -> list[dict]:
    resp = requests.get(ITEMS_URL.format(pub_id=pub_id), timeout=10)
    resp.raise_for_status()
    return resp.json()


def _parse_items(store: str, items: list[dict]) -> list[Deal]:
    deals: list[Deal] = []
    for item in items:
        sale_price = item.get("current_price")
        if sale_price is None:
            continue
        original_price = item.get("original_price")
        discount_pct: float | None = None
        if original_price and float(original_price) > float(sale_price):
            discount_pct = round(
                (float(original_price) - float(sale_price)) / float(original_price) * 100, 1
            )
        deals.append(
            Deal(
                store=store,
                name=item.get("name", ""),
                description=item.get("description", ""),
                sale_price=float(sale_price),
                original_price=float(original_price) if original_price else None,
                discount_pct=discount_pct,
                valid_until=item.get("valid_to"),
            )
        )
    return deals
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_flipp.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add scrapers/flipp.py tests/test_flipp.py
git commit -m "feat: add Flipp API scraper"
```

---

## Task 5: Costco Scraper

**Files:**
- Create: `scrapers/costco.py`
- Create: `tests/test_costco.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_costco.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_costco.py -v
```

Expected: `ImportError: No module named 'scrapers.costco'`

- [ ] **Step 3: Create `scrapers/costco.py`**

```python
from __future__ import annotations
from playwright.sync_api import sync_playwright
from models import Deal

COSTCO_URL = "https://www.costco.ca/savings-centre.html"


def fetch_costco_deals() -> list[Deal]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(COSTCO_URL)
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_costco.py -v
```

Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add scrapers/costco.py tests/test_costco.py
git commit -m "feat: add Costco Playwright scraper"
```

---

## Task 6: Recipe Finder

**Files:**
- Create: `recipes.py`
- Create: `tests/test_recipes.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_recipes.py`:

```python
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

def test_fetch_recipes_returns_top_3(sample_deals):
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
    assert len(results) == 3

def test_fetch_recipes_empty_deals():
    results = fetch_recipes([], "fake-key")
    assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_recipes.py -v
```

Expected: `ImportError: No module named 'recipes'`

- [ ] **Step 3: Create `recipes.py`**

```python
from __future__ import annotations
import re
import requests
from models import Deal, Recipe

FILLER_WORDS = {
    "extra", "lean", "fresh", "organic", "frozen", "boneless", "skinless",
    "sliced", "diced", "chopped", "whole", "large", "medium", "small",
    "value", "family", "pack", "bag", "box", "jar", "can", "aged",
}
_QUANTITY_RE = re.compile(
    r"\b\d+(\.\d+)?\s*(kg|g|lb|lbs|ml|l|oz|pk|ct|x\d+)\b", re.IGNORECASE
)
SPOONACULAR_URL = "https://api.spoonacular.com/recipes/findByIngredients"


def extract_ingredient(name: str) -> str:
    if not name:
        return ""
    cleaned = _QUANTITY_RE.sub("", name)
    words = [w for w in cleaned.split() if w.isalpha() and w.lower() not in FILLER_WORDS]
    return " ".join(words[:3]).strip().lower()


def fetch_recipes(deals: list[Deal], api_key: str) -> list[Recipe]:
    if not deals:
        return []
    ingredients = list({extract_ingredient(d.name) for d in deals if extract_ingredient(d.name)})[:10]
    if not ingredients:
        return []
    resp = requests.get(
        SPOONACULAR_URL,
        params={"ingredients": ",".join(ingredients), "number": 10, "apiKey": api_key},
        timeout=10,
    )
    resp.raise_for_status()
    scored = [_score_recipe(r, deals) for r in resp.json()]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [recipe for _, recipe in scored[:3]]


def _score_recipe(raw: dict, deals: list[Deal]) -> tuple[float, Recipe]:
    used_names = {i["name"].lower() for i in raw.get("usedIngredients", [])}
    matched = [d for d in deals if any(u in d.name.lower() for u in used_names)]
    maxi_count = sum(1 for d in matched if d.store == "Maxi")
    stores = {d.store for d in matched}
    score = len(matched) * 10 - len(stores) * 5 + maxi_count * 3
    recipe_id = raw["id"]
    slug = raw["title"].lower().replace(" ", "-")
    return score, Recipe(
        name=raw["title"],
        url=f"https://spoonacular.com/recipes/{slug}-{recipe_id}",
        image_url=raw.get("image", ""),
        matched_deals=matched,
        store_count=len(stores),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_recipes.py -v
```

Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add recipes.py tests/test_recipes.py
git commit -m "feat: add recipe finder with Spoonacular scoring"
```

---

## Task 7: Email Template

**Files:**
- Create: `templates/email.html`

No tests for the template itself — rendering is tested in Task 8.

- [ ] **Step 1: Create `templates/` directory and `templates/email.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Weekly Grocery Deals</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif">
<div style="max-width:600px;margin:0 auto;background:#f4f6f9">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1a7f4b 0%,#2ecc71 100%);padding:30px 28px;color:white;overflow:hidden">
    <div style="font-size:28px;font-weight:800;letter-spacing:-0.5px">&#x1F6D2; Weekly Deals</div>
    <div style="font-size:13px;opacity:0.9;margin-top:6px">Sherbrooke, QC &middot; {{ date }}</div>
    <div style="margin-top:14px">
      <span style="background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;margin-right:6px">{{ total_stores }} stores</span>
      <span style="background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;margin-right:6px">{{ total_deals }} deals</span>
      <span style="background:rgba(255,255,255,0.2);padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600">{{ recipes|length }} recipes</span>
    </div>
  </div>

  <!-- Failed stores notice -->
  {% if failed_stores %}
  <div style="background:#fff3cd;padding:10px 20px;font-size:12px;color:#856404;border-bottom:1px solid #ffc107">
    &#x26A0;&#xFE0F; Deals unavailable this week: {{ failed_stores | join(', ') }}
  </div>
  {% endif %}

  <!-- Recipes -->
  {% if recipes %}
  <div style="padding:22px 20px 0">
    <div style="font-size:18px;font-weight:800;color:#1a1a1a;margin-bottom:4px">&#x1F37D;&#xFE0F; Suggested Recipes</div>
    <div style="font-size:12px;color:#888;margin-bottom:14px">Maximizing your Maxi deals</div>

    <!-- Featured recipe -->
    {% set featured = recipes[0] %}
    <div style="background:linear-gradient(135deg,#fff9e6,#fff3cc);border-radius:12px;padding:16px;margin-bottom:10px;border:1px solid #f5dc80;position:relative;overflow:hidden">
      <div style="position:absolute;top:0;right:0;background:#f5a623;color:white;font-size:10px;font-weight:700;padding:4px 10px;border-radius:0 12px 0 8px">&#x2B50; BEST PICK</div>
      <div style="font-weight:800;font-size:15px;color:#7b4a00;margin-bottom:3px">{{ featured.name }}</div>
      <div style="font-size:11px;color:#a06820;margin-bottom:10px">
        {{ featured.store_count }} store{% if featured.store_count != 1 %}s{% endif %} needed &middot; {{ featured.matched_deals|length }} deal{% if featured.matched_deals|length != 1 %}s{% endif %} used
      </div>
      <div style="margin-bottom:12px">
        {% for deal in featured.matched_deals %}
        <span style="display:inline-block;background:#fff;color:#2e7d32;font-size:11px;padding:4px 10px;border-radius:20px;border:1px solid #c8e6c9;font-weight:600;margin:2px">
          {{ deal.name }} &mdash; {{ deal.store }} ${{ "%.2f"|format(deal.sale_price) }}
        </span>
        {% endfor %}
      </div>
      <a href="{{ featured.url }}" style="display:inline-block;background:#f5a623;color:white;font-size:12px;font-weight:700;padding:7px 16px;border-radius:20px;text-decoration:none">View Recipe &#x2192;</a>
    </div>

    <!-- Other recipes (side by side) -->
    {% if recipes|length > 1 %}
    <table width="100%" cellspacing="0" cellpadding="0" style="margin-bottom:6px">
      <tr>
        {% for recipe in recipes[1:] %}
        <td width="50%" style="padding:0 {% if loop.first %}0 5px 0{% else %}5px 0 0{% endif %}; vertical-align:top">
          <div style="background:white;border-radius:12px;padding:14px;border:1px solid #e8e8e8">
            <div style="font-weight:700;font-size:13px;color:#333;margin-bottom:3px">{{ recipe.name }}</div>
            <div style="font-size:11px;color:#888;margin-bottom:8px">
              {{ recipe.store_count }} store{% if recipe.store_count != 1 %}s{% endif %} &middot; {{ recipe.matched_deals|length }} deal{% if recipe.matched_deals|length != 1 %}s{% endif %}
            </div>
            <div style="margin-bottom:10px">
              {% for deal in recipe.matched_deals %}
              {% set color = store_colors[deal.store]["main"] %}
              <span style="display:inline-block;background:#f0f0f0;color:#333;font-size:10px;padding:3px 7px;border-radius:10px;margin:2px">{{ deal.store }}</span>
              {% endfor %}
            </div>
            <a href="{{ recipe.url }}" style="font-size:11px;color:#1a7f4b;font-weight:700;text-decoration:none">View &#x2192;</a>
          </div>
        </td>
        {% endfor %}
      </tr>
    </table>
    {% endif %}
  </div>
  {% endif %}

  <!-- Deals by Store -->
  <div style="padding:18px 20px 6px">
    <div style="font-size:18px;font-weight:800;color:#1a1a1a">&#x1F3EA; Deals By Store</div>
  </div>

  {% for store, store_deals in deals_by_store.items() %}
  {% set color = store_colors[store]["main"] %}
  {% set light = store_colors[store]["light"] %}
  <div style="margin:8px 20px 6px;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
    <div style="background:{{ color }};padding:12px 16px">
      <span style="background:white;color:{{ color }};font-weight:900;font-size:13px;padding:3px 10px;border-radius:20px;margin-right:8px">{{ store.upper() }}</span>
      <span style="color:rgba(255,255,255,0.9);font-size:12px">{{ store_deals|length }} deal{% if store_deals|length != 1 %}s{% endif %} this week</span>
      {% if store == "Maxi" %}
      <span style="float:right;background:rgba(255,255,255,0.2);color:white;font-size:11px;padding:2px 8px;border-radius:10px">&#x2B50; Prioritized</span>
      {% endif %}
    </div>
    {% for deal in store_deals %}
    <div style="display:flex;align-items:center;padding:10px 16px;{% if not loop.last %}border-bottom:1px solid #f5f5f5{% endif %}">
      <div style="flex:1">
        <div style="font-weight:600;font-size:13px;color:#1a1a1a">{{ deal.name }}</div>
        <div style="color:#999;font-size:11px">{{ deal.description }}</div>
      </div>
      <div style="text-align:right">
        <span style="font-weight:800;font-size:15px;color:{{ color }}">${{ "%.2f"|format(deal.sale_price) }}</span>
        {% if deal.original_price %}
        <span style="color:#bbb;text-decoration:line-through;font-size:11px;margin-left:6px">${{ "%.2f"|format(deal.original_price) }}</span>
        {% endif %}
        {% if deal.discount_pct %}
        <div style="margin-top:2px">
          <span style="background:{{ light }};color:{{ color }};font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px">-{{ deal.discount_pct|int }}%</span>
        </div>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
  {% endfor %}

  <!-- Footer -->
  <div style="padding:20px 28px;text-align:center;font-size:11px;color:#aaa">
    GroceryBot &middot; Deals valid as of {{ date }} &middot; Sherbrooke, QC
  </div>

</div>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add templates/email.html
git commit -m "feat: add Jinja2 email template"
```

---

## Task 8: Email Sender

**Files:**
- Create: `email_sender.py`
- Create: `tests/test_email_sender.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_email_sender.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from email_sender import render_email, send_email, STORE_ORDER

def test_render_email_contains_store_name(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], [])
    assert "MAXI" in html
    assert "METRO" in html

def test_render_email_shows_failed_store(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], ["Costco"])
    assert "Costco" in html
    assert "unavailable" in html.lower()

def test_render_email_no_recipes(sample_deals):
    html = render_email(sample_deals, [], [])
    assert "Suggested Recipes" not in html

def test_render_email_maxi_first(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], [])
    maxi_pos = html.find("MAXI")
    metro_pos = html.find("METRO")
    assert maxi_pos < metro_pos

def test_render_email_shows_discount(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], [])
    assert "-38%" in html  # maxi_deal has 38.5% → int = 38

def test_send_email_uses_starttls(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], [])
    mock_server = MagicMock()
    mock_smtp = MagicMock(return_value=__import__("contextlib").nullcontext(mock_server))

    with patch("email_sender.smtplib.SMTP") as MockSMTP:
        mock_instance = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)
        send_email(html, "from@gmail.com", "pass", "to@gmail.com")

    mock_instance.starttls.assert_called_once()
    mock_instance.login.assert_called_once_with("from@gmail.com", "pass")
    mock_instance.sendmail.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_email_sender.py -v
```

Expected: `ImportError: No module named 'email_sender'`

- [ ] **Step 3: Create `email_sender.py`**

```python
from __future__ import annotations
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from models import Deal, Recipe

STORE_COLORS: dict[str, dict[str, str]] = {
    "Maxi":    {"main": "#e63333", "light": "#fff0f0"},
    "Metro":   {"main": "#0055a5", "light": "#e8f0fb"},
    "IGA":     {"main": "#00833e", "light": "#e8f5e9"},
    "Provigo": {"main": "#f47920", "light": "#fff3e0"},
    "Costco":  {"main": "#005daa", "light": "#e3f2fd"},
}
STORE_ORDER = ["Maxi", "IGA", "Metro", "Provigo", "Costco"]

_jinja_env = Environment(loader=FileSystemLoader("templates"), autoescape=True)


def render_email(
    deals: list[Deal],
    recipes: list[Recipe],
    failed_stores: list[str],
) -> str:
    stores_present = sorted(
        {d.store for d in deals},
        key=lambda s: (STORE_ORDER.index(s) if s in STORE_ORDER else 99, s),
    )
    deals_by_store = {
        store: [d for d in deals if d.store == store]
        for store in stores_present
    }
    template = _jinja_env.get_template("email.html")
    return template.render(
        deals_by_store=deals_by_store,
        recipes=recipes,
        store_colors=STORE_COLORS,
        failed_stores=failed_stores,
        date=date.today().strftime("%B %d, %Y"),
        total_deals=len(deals),
        total_stores=len(stores_present),
    )


def send_email(
    html: str,
    gmail_address: str,
    app_password: str,
    recipient: str,
) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"\U0001f6d2 Weekly Grocery Deals \u2014 {date.today().strftime('%B %d, %Y')}"
    msg["From"] = gmail_address
    msg["To"] = recipient
    msg.attach(MIMEText("Grocery deals this week. Enable HTML to view the full email.", "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, recipient, msg.as_string())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_email_sender.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add email_sender.py tests/test_email_sender.py
git commit -m "feat: add email renderer and Gmail sender"
```

---

## Task 9: Main Orchestrator

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_main.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from models import Deal

def make_deal(store, name, disc=20.0):
    return Deal(store=store, name=name, description="1kg",
                sale_price=5.0, original_price=6.25, discount_pct=disc, valid_until=None)

FLIPP_DEALS = [make_deal("Maxi", "Ground beef", 38.0), make_deal("IGA", "Broccoli", 30.0)]
COSTCO_DEALS = [make_deal("Costco", "Salmon", None)]

@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_costco_deals", return_value=COSTCO_DEALS)
@patch("main.fetch_flipp_deals", return_value=FLIPP_DEALS)
@patch("main.load_config")
def test_run_happy_path(mock_cfg, mock_flipp, mock_costco, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        gmail_address="a@gmail.com", gmail_app_password="pw",
        email_recipient="b@gmail.com", max_deals_per_store=10,
    )
    from main import run
    run()
    mock_send.assert_called_once()
    args = mock_render.call_args[0]
    all_deals = args[0]
    stores = [d.store for d in all_deals]
    assert stores[0] == "Maxi"  # Maxi is first

@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_costco_deals", side_effect=Exception("Playwright error"))
@patch("main.fetch_flipp_deals", return_value=FLIPP_DEALS)
@patch("main.load_config")
def test_run_costco_failure_still_sends(mock_cfg, mock_flipp, mock_costco, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        gmail_address="a@gmail.com", gmail_app_password="pw",
        email_recipient="b@gmail.com", max_deals_per_store=10,
    )
    from main import run
    run()
    mock_send.assert_called_once()
    failed_stores = mock_render.call_args[0][2]
    assert "Costco" in failed_stores

@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_costco_deals", return_value=[make_deal("Costco", f"Item {i}") for i in range(20)])
@patch("main.fetch_flipp_deals", return_value=[])
@patch("main.load_config")
def test_run_respects_max_deals_per_store(mock_cfg, mock_flipp, mock_costco, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        gmail_address="a@gmail.com", gmail_app_password="pw",
        email_recipient="b@gmail.com", max_deals_per_store=5,
    )
    from main import run
    run()
    all_deals = mock_render.call_args[0][0]
    costco_deals = [d for d in all_deals if d.store == "Costco"]
    assert len(costco_deals) == 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError: No module named 'main'`

- [ ] **Step 3: Create `main.py`**

```python
from __future__ import annotations
import logging
from itertools import groupby

from config import load_config
from scrapers.flipp import fetch_flipp_deals
from scrapers.costco import fetch_costco_deals
from recipes import fetch_recipes
from email_sender import render_email, send_email, STORE_ORDER


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("grocerybot.log"),
            logging.StreamHandler(),
        ],
    )
    log = logging.getLogger(__name__)
    config = load_config()
    all_deals = []
    failed_stores: list[str] = []

    try:
        flipp_deals = fetch_flipp_deals(config.postal_code)
        all_deals.extend(flipp_deals)
        log.info("Fetched %d deals from Flipp", len(flipp_deals))
    except Exception as exc:
        log.error("Flipp scraper failed: %s", exc)
        failed_stores.extend(["Maxi", "Provigo", "IGA", "Metro"])

    try:
        costco_deals = fetch_costco_deals()
        all_deals.extend(costco_deals)
        log.info("Fetched %d deals from Costco", len(costco_deals))
    except Exception as exc:
        log.error("Costco scraper failed: %s", exc)
        failed_stores.append("Costco")

    # Sort: Maxi first, then alphabetical; within each store sort by discount desc (None last)
    all_deals.sort(key=lambda d: (
        STORE_ORDER.index(d.store) if d.store in STORE_ORDER else 99,
        -(d.discount_pct or 0),
    ))

    # Trim to max_deals_per_store per store
    trimmed = []
    for _store, group in groupby(all_deals, key=lambda d: d.store):
        trimmed.extend(list(group)[: config.max_deals_per_store])

    recipes = []
    if trimmed:
        try:
            recipes = fetch_recipes(trimmed, config.spoonacular_api_key)
            log.info("Found %d recipes", len(recipes))
        except Exception as exc:
            log.error("Recipe fetch failed: %s", exc)

    html = render_email(trimmed, recipes, failed_stores)
    send_email(html, config.gmail_address, config.gmail_app_password, config.email_recipient)
    log.info("Email sent successfully")


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Run the full test suite**

```bash
pytest -v
```

Expected: All tests PASSED

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main orchestrator"
```

---

## Task 10: Smoke Test End-to-End

- [ ] **Step 1: Create `.env` from `.env.example`**

Copy `.env.example` to `.env` and fill in real values:
- `POSTAL_CODE` — your Sherbrooke postal code (e.g. `J1H2B4`)
- `GMAIL_ADDRESS` — your Gmail address
- `GMAIL_APP_PASSWORD` — generate at https://myaccount.google.com/apppasswords (requires 2FA enabled)
- `EMAIL_RECIPIENT` — where to send the digest
- `SPOONACULAR_API_KEY` — sign up free at https://spoonacular.com/food-api

- [ ] **Step 2: Run the bot**

```bash
python main.py
```

Expected output (in terminal and `grocerybot.log`):
```
2026-04-01 10:00:00 INFO Fetched N deals from Flipp
2026-04-01 10:00:05 INFO Fetched N deals from Costco
2026-04-01 10:00:06 INFO Found 3 recipes
2026-04-01 10:00:07 INFO Email sent successfully
```

- [ ] **Step 3: Verify the email**

Check your inbox. Confirm:
- Header shows correct date and store/deal counts
- Maxi section appears first with red header bar
- Recipes section shows "Best Pick" card + 2 smaller cards
- Deal rows show sale price, original price (strikethrough), and discount % badge

- [ ] **Step 4: If Costco selectors need adjustment**

If Costco returns 0 deals, the CSS selectors in `scrapers/costco.py` likely need updating. To debug:

```python
# Run this snippet to inspect the live DOM
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # visible window
    page = browser.new_page()
    page.goto("https://www.costco.ca/savings-centre.html")
    input("Press Enter after inspecting the page...")
    browser.close()
```

Update the selectors in `_extract_deals()` to match the actual DOM, re-run the tests, and commit.

- [ ] **Step 5: Final commit**

```bash
git add .env.example
git commit -m "chore: finalize smoke test notes"
```
