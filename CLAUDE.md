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
- `MAILERSEND_EMAIL` — Mailersend SMTP username (from Settings → SMTP)
- `MAILERSEND_API_KEY` — Mailersend SMTP password (from Settings → SMTP)
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

1. **Flipp-based Scrapers** — Leverage Flipp's commercial flyer system (used by Maxi, Metro, IGA, Provigo)
   - **Maxi** (`scrapers/maxi.py`) — Two-tier approach: 
     1. HTTP scraper (fast) — calls Flipp API for publication IDs, then fetches items directly
     2. Fallback: headed Playwright with persistent profile (`browser_profiles/maxi/`) — when HTTP is blocked, uses a real browser window that Forter can't detect as headless
   - **IGA/Metro/Provigo** (`scrapers/iga.py`, `metro.py`, `provigo.py`) — Use headless Playwright to intercept Flipp widget responses from store pages
   - **Shared Infrastructure** (`scrapers/store_flyer.py`, `scrapers/utils.py`) — Playwright network interception and deal parsing
2. **Costco Playwright Scraper** (`scrapers/costco.py`) — Uses headless browser automation to scrape Costco's savings centre
3. **Recipe Finder** (`recipes.py`) — Extracts ingredients from deal names, queries Spoonacular API, and scores recipes by Maxi-priority and store-count minimization
4. **Email Renderer** (`email_sender.py`, `templates/email.html`) — Builds an HTML digest with recipes and deals organized by store (10 recipes per email)
5. **Main Orchestrator** (`main.py`) — Coordinates all scrapers with independent error isolation (one scraper's failure doesn't block others), sorts deals, trims to max per store, and sends email via Mailersend SMTP

Data Models:
- `Deal` — Store, name, description, prices, discount %, valid_until date
- `Recipe` — Name, URL, image, matched deals, store count
- `Config` — Loads all credentials/settings from `.env`

**Why Multiple Scraping Approaches?**

Different stores have different antibot protection levels:
- **Maxi:** Uses Forter fraud detection which blocks Playwright entirely. HTTP API approach gets the publication ID from Flipp's public API, then fetches items directly from the CDN — Forter-free.
- **IGA:** No Forter protection; Flipp widget loads normally; Playwright intercepts widget responses successfully.
- **Metro/Provigo:** Have Forter protection (like Maxi), but their upstream APIs are also blocked. Fallback to demo data.

**Current Status:**
- ✅ **IGA:** Successfully captures and parses ~313 deals per run via Playwright network interception
- ⚠️ **Maxi:** 
  - HTTP API blocked (returns HTML)
  - Headed browser fallback implemented; successfully loads page without Forter blocking
  - Challenge: Maxi uses proprietary Loblaws JavaScript to dynamically load deal data (not via interceptable HTTP API)
  - Requires either: reverse-engineering Loblaws API, DOM parsing, or access to undocumented endpoints
- ❌ **Metro, Provigo:** Blocked by Forter fraud detection (headless browser detection); would need similar headed browser approach

The system gracefully falls back to demo data when real scraping fails, ensuring the email pipeline continues to function reliably. With 313 deals/run from IGA and robust fallback behavior, the system delivers value despite Forter antibot protections.

## Running the Bot

### Setup: Mailersend SMTP

**One-time setup (5 minutes):**

1. **Create a Mailersend account** (free): https://www.mailersend.com/
   - Sign up and verify your email

2. **Add a sender domain:**
   - Go to Senders & Domains → Domains
   - Click "Add Domain"
   - Enter a domain you own (e.g., `grocerybot.example.com`)
   - Follow DNS verification steps
   - **Alternative:** Use Mailersend's test domain `trial-z9md6ol9rp5k78.mlsnd.net` for testing

3. **Get SMTP credentials:**
   - Go to Settings → SMTP
   - You'll see:
     - SMTP Host: `smtp.mailersend.net`
     - SMTP Port: `587`
     - SMTP Username: (usually your email or a generated username)
     - SMTP Password: (generate one or use your account password)
   - Copy these credentials

4. **Configure `.env` file:**
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and fill in:
   ```
   POSTAL_CODE=J1H2B4
   EMAIL_FROM=noreply@grocerybot.local
   EMAIL_RECIPIENT=your-personal-email@gmail.com
   MAILERSEND_EMAIL=your-smtp-username
   MAILERSEND_API_KEY=your-smtp-password
   SPOONACULAR_API_KEY=your_spoonacular_api_key
   MAX_DEALS_PER_STORE=10
   ```

5. **Install dependencies and run:**
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

6. **Verify emails were sent:**
   - Go to https://www.mailersend.com/ → Activity/Dashboard
   - Look for sent emails in the log

### Mailersend SMTP Credentials Reference

| Credential | Value |
|---|---|
| SMTP Host | `smtp.mailersend.net` |
| SMTP Port | `587` |
| TLS | Required |
| Username | (from Mailersend Settings → SMTP) |
| Password | (SMTP password from Mailersend Settings) |

### Why Mailersend?

✅ **Simple SMTP auth** — username + password, no OAuth
✅ **Free tier** — 1000 emails/month (plenty for daily runs)
✅ **Real emails** — reaches actual inboxes, professional delivery
✅ **Production ready** — trusted by many projects
✅ **Easy setup** — 5 minutes to get credentials

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
