from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    postal_code: str
    email_from: str
    email_from_name: str
    email_recipients: list[str]
    mailersend_email: str
    mailersend_api_key: str
    spoonacular_api_key: str
    max_deals_per_store: int


def load_config() -> Config:
    load_dotenv()
    # Parse EMAIL_RECIPIENT as comma-separated list
    email_recipient_str = os.environ["EMAIL_RECIPIENT"]
    email_recipients = [e.strip() for e in email_recipient_str.split(",") if e.strip()]

    return Config(
        postal_code=os.environ["POSTAL_CODE"],
        email_from=os.environ.get("EMAIL_FROM", "noreply@grocerybot.local"),
        email_from_name=os.environ.get("EMAIL_FROM_NAME", "EparseRIE@bouffe.deal"),
        email_recipients=email_recipients,
        mailersend_email=os.environ["MAILERSEND_EMAIL"],
        mailersend_api_key=os.environ["MAILERSEND_API_KEY"],
        spoonacular_api_key=os.environ["SPOONACULAR_API_KEY"],
        max_deals_per_store=int(os.getenv("MAX_DEALS_PER_STORE", "10")),
    )
