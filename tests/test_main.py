import pytest
from unittest.mock import patch, MagicMock
from models import Deal


def make_deal(store, name, disc=20.0):
    return Deal(store=store, name=name, description="1kg",
                sale_price=5.0, original_price=6.25, discount_pct=disc, valid_until=None)


FLIPP_DEALS = [make_deal("Maxi", "Ground beef", 38.0), make_deal("IGA", "Broccoli", 30.0)]
COSTCO_DEALS = [make_deal("Costco", "Salmon", None)]


@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_costco_deals", return_value=COSTCO_DEALS)
@patch("main.fetch_flipp_deals", return_value=FLIPP_DEALS)
@patch("main.load_config")
def test_run_happy_path(mock_cfg, mock_flipp, mock_costco, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        gmail_address="a@gmail.com", gmail_app_password="pw",
        email_recipient="b@gmail.com", max_deals_per_store=10,
    )
    from main import run
    run()
    mock_send.assert_called_once()
    args = mock_render.call_args[0]
    all_deals = args[0]
    stores = [d.store for d in all_deals]
    assert stores[0] == "Maxi"  # Maxi is first


@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_costco_deals", side_effect=Exception("Playwright error"))
@patch("main.fetch_flipp_deals", return_value=FLIPP_DEALS)
@patch("main.load_config")
def test_run_costco_failure_still_sends(mock_cfg, mock_flipp, mock_costco, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        gmail_address="a@gmail.com", gmail_app_password="pw",
        email_recipient="b@gmail.com", max_deals_per_store=10,
    )
    from main import run
    run()
    mock_send.assert_called_once()
    failed_stores = mock_render.call_args[0][2]
    assert "Costco" in failed_stores


@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_costco_deals", return_value=[make_deal("Costco", f"Item {i}") for i in range(20)])
@patch("main.fetch_flipp_deals", return_value=[])
@patch("main.load_config")
def test_run_respects_max_deals_per_store(mock_cfg, mock_flipp, mock_costco, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        gmail_address="a@gmail.com", gmail_app_password="pw",
        email_recipient="b@gmail.com", max_deals_per_store=5,
    )
    from main import run
    run()
    all_deals = mock_render.call_args[0][0]
    costco_deals = [d for d in all_deals if d.store == "Costco"]
    assert len(costco_deals) == 5
