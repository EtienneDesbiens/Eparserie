from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    postal_code: str
    email_from: str
    email_recipient: str
    mailersend_email: str
    mailersend_api_key: str
    spoonacular_api_key: str
    max_deals_per_store: int


def load_config() -> Config:
    load_dotenv()
    return Config(
        postal_code=os.environ["POSTAL_CODE"],
        email_from=os.environ.get("EMAIL_FROM", "noreply@grocerybot.local"),
        email_recipient=os.environ["EMAIL_RECIPIENT"],
        mailersend_email=os.environ["MAILERSEND_EMAIL"],
        mailersend_api_key=os.environ["MAILERSEND_API_KEY"],
        spoonacular_api_key=os.environ["SPOONACULAR_API_KEY"],
        max_deals_per_store=int(os.getenv("MAX_DEALS_PER_STORE", "10")),
    )
