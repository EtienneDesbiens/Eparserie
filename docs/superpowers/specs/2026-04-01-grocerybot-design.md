# GroceryBot Design Spec

**Date:** 2026-04-01
**Status:** Approved

## Overview

A Python script that runs once daily to fetch grocery deals from 5 stores in Sherbrooke, QC, matches deals to recipes, and sends a formatted HTML email to the user via Gmail.

---

## Architecture

```
GroceryBot/
├── main.py              # Orchestrator — runs the full pipeline
├── config.py            # Loads .env settings
├── models.py            # Deal and Recipe dataclasses
├── recipes.py           # Spoonacular API client + recipe scoring
├── email_sender.py      # Builds HTML email + sends via Gmail SMTP
├── scrapers/
│   ├── flipp.py         # Flipp API client (Maxi, Provigo, IGA, Metro)
│   └── costco.py        # Playwright scraper for Costco
├── templates/
│   └── email.html       # Jinja2 HTML email template
├── .env                 # Credentials (never committed)
├── .env.example         # Template for .env
└── grocerybot.log       # Runtime log file
```

---

## Data Models

```python
@dataclass
class Deal:
    store: str            # e.g. "Maxi"
    name: str             # e.g. "Extra lean ground beef"
    description: str      # e.g. "1 kg"
    sale_price: float
    original_price: float | None   # None if not available (e.g. Costco)
    discount_pct: float | None     # None if original_price is None
    valid_until: str | None   # ISO date string; None if store doesn't publish end date (e.g. Costco)

@dataclass
class Recipe:
    name: str
    url: str
    image_url: str
    matched_deals: list[Deal]
    store_count: int      # number of distinct stores needed
```

---

## Pipeline (`main.py`)

1. Load config from `.env`
2. Fetch deals from Flipp API for Maxi, Provigo, IGA, Metro → list of `Deal` objects
3. Scrape Costco with Playwright → more `Deal` objects
4. Sort all deals: Maxi first, then others alphabetically; within each store, sort by `discount_pct` descending (deals with `None` discount sort last)
5. Keep top `MAX_DEALS_PER_STORE` deals per store
6. Extract food keywords from deal names → query Spoonacular for recipes
7. Score and rank recipes; select top 3
8. Render `email.html` with Jinja2
9. Send via Gmail SMTP
10. Log outcome to `grocerybot.log`

---

## Scraping

### Flipp API (`scrapers/flipp.py`)

- Publications endpoint: `GET https://flipp.com/api/2/publications?locale=en-CA&postal_code={POSTAL_CODE}`
- Items endpoint: `GET https://cdn.flipp.com/flyerkit/publications/{id}/items`
- Returns structured JSON — no HTML parsing required
- Filter results by `merchant_name` to the 4 target stores
- All deal names returned in English via `locale=en-CA`

### Costco Scraper (`scrapers/costco.py`)

- Uses Playwright (headless Chromium) to load `costco.ca/savings-centre.html`
- Waits for deal cards to render, then extracts name, description, sale price, and original price from the DOM
- `original_price` and `discount_pct` stored as `None` if not shown

### Error Isolation

Each scraper runs in a `try/except` block. On failure:
- Logs the error to `grocerybot.log`
- Returns an empty list
- Pipeline continues with available deals
- Email notes which stores were unavailable (e.g. *"Costco deals unavailable this week."*)

---

## Recipes (`recipes.py`)

### Ingredient Extraction

Deal names are cleaned to extract core food keywords:
- Strip descriptions/quantities (e.g. "Extra lean ground beef 1 kg" → "ground beef")
- Pass up to 10 keywords to Spoonacular's `findByIngredients` endpoint

### Spoonacular API

```
GET https://api.spoonacular.com/recipes/findByIngredients
  ?ingredients=ground+beef,broccoli,...
  &number=10
  &apiKey={SPOONACULAR_API_KEY}
```

Free tier: 150 requests/day — well within budget for one run per day.

### Recipe Scoring

```python
score = (matched_deal_count * 10) - (distinct_store_count * 5) + (maxi_deal_count * 3)
```

- Maximizes ingredient overlap with current deals
- Penalizes recipes requiring many stores
- Rewards recipes that use Maxi deals specifically
- Top 3 recipes by score are included in the email

---

## Email (`email_sender.py` + `templates/email.html`)

### Layout (store-by-store, Maxi-prioritized)

1. **Header** — gradient banner with week date, store count, deal count, recipe count
2. **Recipes section** — top 3 recipes; best pick (highest score, Maxi-heavy) shown as featured card; other 2 shown as smaller side-by-side cards. Each recipe shows matched deals with store tags and links to the Spoonacular recipe page.
3. **Deals by store** — Maxi first, then remaining stores alphabetically. Each store has a coloured header bar (Maxi: red, Metro: blue, IGA: green, Provigo: orange, Costco: blue/red). Each deal row shows name, description, sale price, original price (strikethrough), and discount % badge.
4. **Footer** — date and location

### Sending

- Transport: Gmail SMTP (`smtp.gmail.com:587`, STARTTLS)
- Auth: Gmail App Password (not main account password)
- `email.mime.multipart.MIMEMultipart('alternative')` with both plain-text fallback and HTML parts

---

## Configuration (`.env`)

```
POSTAL_CODE=J1H2B4
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_RECIPIENT=you@gmail.com
SPOONACULAR_API_KEY=your_key_here
MAX_DEALS_PER_STORE=10
```

---

## Running

```bash
python main.py
```

One command runs the full pipeline and sends the email. The user is responsible for scheduling (e.g. Windows Task Scheduler).

---

## Dependencies

- `playwright` — Costco scraping
- `requests` — Flipp API + Spoonacular API
- `jinja2` — HTML email templating
- `python-dotenv` — `.env` loading
