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

### Setup: Mailtrap SMTP (Simple, No OAuth)

**One-time setup (2 minutes):**
1. Sign up (free): https://mailtrap.io/
2. Create an inbox (Projects → New Project → New Inbox)
3. Go to SMTP settings (Integration → SMTP)
4. Copy your credentials:
   - SMTP Host: `live.smtp.mailtrap.io`
   - Username: `your_mailtrap_username`
   - Password: `your_mailtrap_password`
5. Add to `.env`:
   ```
   MAILTRAP_USERNAME=your_mailtrap_username
   MAILTRAP_PASSWORD=your_mailtrap_password
   EMAIL_RECIPIENT=your-email@example.com
   ```

**Run:**
```bash
cp .env.example .env  # Fill in Mailtrap credentials
pip install -r requirements.txt
python main.py
```

**Check emails:** Go to https://mailtrap.io/ → your inbox to see sent emails

### Why Mailtrap?

✅ **No OAuth complexity** — just username + password
✅ **Free tier** — 500 test emails/month, perfect for development
✅ **Works from anywhere** — no Google Cloud setup needed
✅ **Great for testing** — see HTML rendering in inbox
✅ **Production ready** — upgrade plan for real sending when needed

### Scheduling

The bot is designed to run once per day via system scheduler:
- **Windows:** Task Scheduler → create scheduled task → `python main.py`
- **Linux/Mac:** Cron → `0 8 * * * cd /path && python main.py`

**Logs:** Check `grocerybot.log` for execution details

## CodeGraph

This project uses CodeGraph for code exploration. Run `codegraph index` after adding new files to keep the symbol index updated.
