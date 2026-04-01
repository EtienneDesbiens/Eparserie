from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    postal_code: str
    gmail_address: str
    gmail_app_password: str
    email_recipient: str
    spoonacular_api_key: str
    max_deals_per_store: int


def load_config() -> Config:
    load_dotenv()
    return Config(
        postal_code=os.environ["POSTAL_CODE"],
        gmail_address=os.environ["GMAIL_ADDRESS"],
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),  # Optional - OAuth preferred
        email_recipient=os.environ["EMAIL_RECIPIENT"],
        spoonacular_api_key=os.environ["SPOONACULAR_API_KEY"],
        max_deals_per_store=int(os.getenv("MAX_DEALS_PER_STORE", "10")),
    )
