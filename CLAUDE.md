# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Eparserie** is a Python-based web scraping project that collects grocery store deals and pricing information. It integrates with the Spoonacular API, uses Playwright for web scraping, and can send notifications via Gmail.

**Python Version:** 3.12.10

## Development Setup

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Configure Environment
Copy `.env.example` to `.env` and fill in:
- `POSTAL_CODE` — Canadian postal code for store location filtering
- `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` — Gmail credentials for sending deal notifications
- `EMAIL_RECIPIENT` — Where to send deal alerts
- `SPOONACULAR_API_KEY` — API key for ingredient/recipe data
- `MAX_DEALS_PER_STORE` — Limit for deal results per store

## Running Tests

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_file.py

# Run a specific test
pytest tests/test_file.py::test_function_name

# Run with verbose output
pytest -v
```

Test configuration is in `pytest.ini`.

## Project Structure

- **scrapers/** — Web scraping logic and data collection modules
- **tests/** — Unit and integration tests

## Key Dependencies

- **Playwright** — Browser automation for web scraping
- **requests** — HTTP requests for APIs
- **Jinja2** — Template rendering (likely for email notifications)
- **python-dotenv** — Environment variable management
- **pytest** — Testing framework with mocking support

## Architecture

**GroceryBot** is a daily deal aggregator that scrapes grocery stores and matches them to recipes:

1. **Flipp API Scraper** (`scrapers/flipp.py`) — Fetches deals from Maxi, Provigo, IGA, and Metro via the Flipp API
2. **Costco Playwright Scraper** (`scrapers/costco.py`) — Uses headless browser automation to scrape Costco's savings centre
3. **Recipe Finder** (`recipes.py`) — Extracts ingredients from deal names, queries Spoonacular API, and scores recipes by Maxi-priority and store-count minimization
4. **Email Renderer** (`email_sender.py`, `templates/email.html`) — Builds an HTML digest with recipes and deals organized by store
5. **Main Orchestrator** (`main.py`) — Coordinates all scrapers with error isolation, sorts deals, trims to max per store, and sends email via Gmail SMTP

Data Models:
- `Deal` — Store, name, description, prices, discount %, valid_until date
- `Recipe` — Name, URL, image, matched deals, store count
- `Config` — Loads all credentials/settings from `.env`

## Running the Bot

### Option 1: OAuth 2.0 (Recommended, Secure)

**One-time setup:**
1. Create Google Cloud project: https://console.cloud.google.com/
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download JSON credentials → save as `gmail_credentials.json`
5. First run: app opens browser for authentication
6. Tokens saved automatically for future runs

**Run:**
```bash
cp .env.example .env
pip install -r requirements.txt
python main.py
# Browser opens for Gmail authorization (first run only)
```

### Option 2: SMTP with App Password (Legacy, Deprecated in 2025+)

Only used as fallback if OAuth not available.

**Setup:**
1. Enable 2FA on Gmail account
2. Go to https://myaccount.google.com/apppasswords
3. Generate app password for "Mail" on "Windows Computer"
4. Add to `.env`: `GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx`

**Note:** Google phased out this method in 2025. OAuth is required for new users.

### Scheduling

The bot is designed to run once per day via system scheduler:
- **Windows:** Task Scheduler → create scheduled task → `python main.py`
- **Linux/Mac:** Cron → `0 8 * * * cd /path && python main.py`

**Logs:** Check `grocerybot.log` for execution details

## CodeGraph

This project uses CodeGraph for code exploration. Run `codegraph index` after adding new files to keep the symbol index updated.
