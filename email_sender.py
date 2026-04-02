from __future__ import annotations
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from itertools import groupby
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

# Category display order
CATEGORY_ORDER = ["Produce", "Meat & Seafood", "Dairy & Eggs", "Frozen", "Pantry", "Beverages", "Other"]


def _group_deals_by_category(deals: list[Deal]) -> dict[str, list[Deal]]:
    """Group deals by category with consistent ordering."""
    grouped = {}
    for category in CATEGORY_ORDER:
        category_deals = [d for d in deals if d.category == category]
        if category_deals:
            grouped[category] = category_deals
    return grouped


def render_email(
    deals: list[Deal],
    recipes: list[Recipe],
    failed_stores: list[str],
    postal_code: str = "QC",
) -> str:
    stores_present = sorted(
        {d.store for d in deals},
        key=lambda s: (STORE_ORDER.index(s) if s in STORE_ORDER else 99, s),
    )
    deals_by_store = {
        store: [d for d in deals if d.store == store]
        for store in stores_present
    }

    # Group deals by category within each store
    deals_by_store_category = {
        store: _group_deals_by_category(store_deals)
        for store, store_deals in deals_by_store.items()
    }

    # Calculate total savings per store
    store_savings = {}
    for store, store_deals in deals_by_store.items():
        total_savings = sum(
            (d.original_price or d.sale_price) - d.sale_price
            for d in store_deals
            if d.original_price
        )
        store_savings[store] = total_savings

    template = _jinja_env.get_template("email.html")
    return template.render(
        deals_by_store=deals_by_store,
        deals_by_store_category=deals_by_store_category,
        recipes=recipes,
        store_colors=STORE_COLORS,
        store_savings=store_savings,
        failed_stores=failed_stores,
        date=date.today().strftime("%B %d, %Y"),
        total_deals=len(deals),
        total_stores=len(stores_present),
        postal_code=postal_code,
    )


def send_email(
    html: str,
    email_from: str,
    mailersend_email: str,
    mailersend_api_key: str,
    email_recipient: str,
) -> None:
    """
    Send email via Mailersend SMTP.
    """
    subject = f"\U0001f6d2 Weekly Grocery Deals \u2014 {date.today().strftime('%B %d, %Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_from
    msg["To"] = email_recipient

    # Plain text fallback
    msg.attach(MIMEText("Grocery deals this week. Enable HTML to view the full email.", "plain"))
    # HTML version
    msg.attach(MIMEText(html, "html"))

    # Send via Mailersend SMTP
    with smtplib.SMTP("smtp.mailersend.net", 587) as server:
        server.starttls()
        server.login(mailersend_email, mailersend_api_key)
        server.sendmail(email_from, email_recipient, msg.as_string())

    print(f"Email sent successfully to {email_recipient} via Mailersend")
