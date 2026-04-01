import pytest
from unittest.mock import patch
from config import load_config, Config

VALID_ENV = {
    "POSTAL_CODE": "J1H2B4",
    "GMAIL_ADDRESS": "test@gmail.com",
    "GMAIL_APP_PASSWORD": "abcd-efgh-ijkl-mnop",
    "EMAIL_RECIPIENT": "me@gmail.com",
    "SPOONACULAR_API_KEY": "abc123",
    "MAX_DEALS_PER_STORE": "10",
}


def test_load_config_returns_config():
    with patch.dict("os.environ", VALID_ENV, clear=True):
        cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.postal_code == "J1H2B4"
    assert cfg.max_deals_per_store == 10


def test_load_config_default_max_deals():
    env = {k: v for k, v in VALID_ENV.items() if k != "MAX_DEALS_PER_STORE"}
    with patch.dict("os.environ", env, clear=True):
        cfg = load_config()
    assert cfg.max_deals_per_store == 10


def test_load_config_missing_required_key():
    env = {k: v for k, v in VALID_ENV.items() if k != "SPOONACULAR_API_KEY"}
    with patch.dict("os.environ", env, clear=True):
        with pytest.raises(KeyError):
            load_config()
