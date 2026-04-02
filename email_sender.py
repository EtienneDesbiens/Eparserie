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
    email_from: str,
    brevo_email: str,
    brevo_api_key: str,
    email_recipient: str,
) -> None:
    """
    Send email via Brevo SMTP (simple, no OAuth needed).
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

    # Send via Brevo SMTP
    with smtplib.SMTP("smtp-relay.brevo.com", 587) as server:
        server.starttls()
        server.login(brevo_email, brevo_api_key)
        server.sendmail(email_from, email_recipient, msg.as_string())

    print(f"Email sent successfully to {email_recipient} via Brevo")
