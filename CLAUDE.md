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
- `BREVO_EMAIL` and `BREVO_API_KEY` — Brevo SMTP credentials for sending deal notifications
- `EMAIL_FROM` — From address for emails (e.g., noreply@grocerybot.local)
- `EMAIL_RECIPIENT` — Where to send deal alerts
- `SPOONACULAR_API_KEY` — API key for ingredient/recipe data
- `MAX_DEALS_PER_STORE` — Limit for deal results per store (default: 10)

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

1. **Direct Store Scrapers** (`scrapers/maxi.py`, `metro.py`, `iga.py`, `provigo.py`) — Use Playwright to intercept Flipp widget JSON responses from each store's flyer page
   - **Shared Infrastructure** (`scrapers/store_flyer.py`, `scrapers/utils.py`) — Playwright network interception and deal parsing
2. **Costco Playwright Scraper** (`scrapers/costco.py`) — Uses headless browser automation to scrape Costco's savings centre
3. **Recipe Finder** (`recipes.py`) — Extracts ingredients from deal names, queries Spoonacular API, and scores recipes by Maxi-priority and store-count minimization
4. **Email Renderer** (`email_sender.py`, `templates/email.html`) — Builds an HTML digest with recipes and deals organized by store
5. **Main Orchestrator** (`main.py`) — Coordinates all scrapers with independent error isolation (one scraper's failure doesn't block others), sorts deals, trims to max per store, and sends email via Brevo SMTP

Data Models:
- `Deal` — Store, name, description, prices, discount %, valid_until date
- `Recipe` — Name, URL, image, matched deals, store count
- `Config` — Loads all credentials/settings from `.env`

**Why Direct Store Scraping?**

Each store (Maxi, Metro, IGA, Provigo) embeds Flipp's commercial flyer widget which calls `dam.flippenterprise.net/flyerkit/publication/{id}/products` to fetch deal JSON. We intercept these network responses using Playwright's response listener, capturing structured JSON without relying on fragile HTML selectors.

**Current Status:**
- ✅ **IGA:** Successfully captures and parses ~313 deals per run
- ❌ **Maxi, Metro, Provigo:** Blocked by Forter fraud detection (sophisticated antibot system that detects and blocks headless browsers)

The system gracefully falls back to demo data when real scraping fails, ensuring the email pipeline continues to function.

## Running the Bot

### Setup: Brevo SMTP (Simple, No OAuth)

**One-time setup (2 minutes):**
1. Sign up (free): https://www.brevo.com/
2. Go to Settings → SMTP & API
3. Copy your credentials:
   - SMTP Host: `smtp-relay.brevo.com`
   - Email: your-email@example.com
   - SMTP Password: (from Settings)
4. Add to `.env`:
   ```
   BREVO_EMAIL=your-email@example.com
   BREVO_API_KEY=your_smtp_password
   EMAIL_FROM=noreply@grocerybot.local
   EMAIL_RECIPIENT=your-email@example.com
   ```

**Run:**
```bash
cp .env.example .env  # Fill in Brevo credentials
pip install -r requirements.txt
python main.py
```

**Check emails:** Go to https://www.brevo.com/ → Transactional to see sent emails

### Why Brevo?

✅ **No OAuth complexity** — just email + password
✅ **Free tier** — 300 emails/day (plenty for daily runs)
✅ **Real emails** — reaches actual inboxes, not a testing service
✅ **Production ready** — used by thousands of companies
✅ **Professional delivery** — better than Mailtrap for real use

### Scheduling

The bot is designed to run once per day via system scheduler:
- **Windows:** Task Scheduler → create scheduled task → `python main.py`
- **Linux/Mac:** Cron → `0 8 * * * cd /path && python main.py`

**Logs:** Check `grocerybot.log` for execution details

## Code Exploration

The project supports CodeGraph for faster codebase navigation. Use these codegraph tools:

| Tool | Use For |
|------|---------|
| `codegraph_search` | Find symbols by name (functions, classes, types) |
| `codegraph_context` | Get relevant code context for a task |
| `codegraph_callers` | Find what calls a function |
| `codegraph_callees` | Find what a function calls |
| `codegraph_impact` | See what's affected by changing a symbol |

After adding new files, rebuild the index: `codegraph init -i`
