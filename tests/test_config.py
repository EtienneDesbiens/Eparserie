import pytest
from unittest.mock import patch
from config import load_config, Config

VALID_ENV = {
    "POSTAL_CODE": "J1H2B4",
    "EMAIL_FROM": "noreply@grocerybot.local",
    "EMAIL_RECIPIENT": "me@example.com",
    "MAILERSEND_EMAIL": "noreply@example.com",
    "MAILERSEND_API_KEY": "test_api_key",
    "SPOONACULAR_API_KEY": "abc123",
    "MAX_DEALS_PER_STORE": "10",
}


def test_load_config_returns_config():
    with patch("config.load_dotenv"):
        with patch.dict("os.environ", VALID_ENV, clear=True):
            cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.postal_code == "J1H2B4"
    assert cfg.max_deals_per_store == 10


def test_load_config_default_max_deals():
    env = {k: v for k, v in VALID_ENV.items() if k != "MAX_DEALS_PER_STORE"}
    with patch("config.load_dotenv"):
        with patch.dict("os.environ", env, clear=True):
            cfg = load_config()
    assert cfg.max_deals_per_store == 10


def test_load_config_missing_required_key():
    # MAILTRAP_PASSWORD is required
    env = {k: v for k, v in VALID_ENV.items() if k != "SPOONACULAR_API_KEY"}
    with patch("config.load_dotenv"):
        with patch.dict("os.environ", env, clear=True):
            with pytest.raises(KeyError):
                load_config()


def test_load_config_single_email_recipient():
    with patch("config.load_dotenv"):
        with patch.dict("os.environ", VALID_ENV, clear=True):
            cfg = load_config()
    assert cfg.email_recipients == ["me@example.com"]


def test_load_config_multiple_email_recipients():
    env = VALID_ENV.copy()
    env["EMAIL_RECIPIENT"] = "alice@example.com, bob@example.com, charlie@example.com"
    with patch("config.load_dotenv"):
        with patch.dict("os.environ", env, clear=True):
            cfg = load_config()
    assert cfg.email_recipients == ["alice@example.com", "bob@example.com", "charlie@example.com"]


def test_load_config_email_from_name():
    env = VALID_ENV.copy()
    env["EMAIL_FROM_NAME"] = "GroceryBot"
    with patch("config.load_dotenv"):
        with patch.dict("os.environ", env, clear=True):
            cfg = load_config()
    assert cfg.email_from_name == "GroceryBot"


def test_load_config_email_from_name_optional():
    """EMAIL_FROM_NAME is not required in the environment."""
    with patch("config.load_dotenv"):
        with patch.dict("os.environ", VALID_ENV, clear=True):
            cfg = load_config()
    # Just verify it loads without raising, and returns a string
    assert isinstance(cfg.email_from_name, str)
