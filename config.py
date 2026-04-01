from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    postal_code: str
    email_from: str
    email_recipient: str
    mailtrap_username: str
    mailtrap_password: str
    spoonacular_api_key: str
    max_deals_per_store: int


def load_config() -> Config:
    load_dotenv()
    return Config(
        postal_code=os.environ["POSTAL_CODE"],
        email_from=os.environ.get("EMAIL_FROM", "noreply@grocerybot.local"),
        email_recipient=os.environ["EMAIL_RECIPIENT"],
        mailtrap_username=os.environ["MAILTRAP_USERNAME"],
        mailtrap_password=os.environ["MAILTRAP_PASSWORD"],
        spoonacular_api_key=os.environ["SPOONACULAR_API_KEY"],
        max_deals_per_store=int(os.getenv("MAX_DEALS_PER_STORE", "10")),
    )
