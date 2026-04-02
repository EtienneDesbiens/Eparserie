# Eparserie

Weekly grocery deal aggregator for Quebec stores. Scrapes flyers, matches deals to recipes, and sends a digest email.

## What it does

- Scrapes weekly flyers from **Maxi, IGA, Metro, and Provigo** via Playwright
- Filters deals to food items under $50, grouped by category
- Finds recipes using on-sale ingredients via the Spoonacular API
- Sends an HTML email digest with deals and recipe suggestions

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Fill in .env with your credentials
python main.py
```

## Environment variables

| Variable | Description |
|---|---|
| `POSTAL_CODE` | Canadian postal code for store location |
| `EMAIL_FROM` | Sender email address |
| `EMAIL_FROM_NAME` | Sender display name (optional) |
| `EMAIL_RECIPIENT` | Recipient(s), comma-separated |
| `MAILERSEND_EMAIL` | Mailersend SMTP username |
| `MAILERSEND_API_KEY` | Mailersend SMTP password |
| `SPOONACULAR_API_KEY` | Spoonacular API key |
| `MAX_DEALS_PER_STORE` | Max deals shown per store (default: 10) |

## Running tests

```bash
pytest
```

## Scheduling

Run `python main.py` daily via Task Scheduler (Windows) or cron (Linux/Mac).
