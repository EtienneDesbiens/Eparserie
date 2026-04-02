import pytest
from unittest.mock import patch, MagicMock
from models import Deal


def make_deal(store, name, disc=20.0):
    return Deal(store=store, name=name, description="1kg",
                sale_price=5.0, original_price=6.25, discount_pct=disc, valid_until=None)


MAXI_DEALS = [make_deal("Maxi", "Ground beef", 38.0)]
METRO_DEALS = []
IGA_DEALS = [make_deal("IGA", "Broccoli", 30.0)]
PROVIGO_DEALS = []


@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_provigo_deals", return_value=PROVIGO_DEALS)
@patch("main.fetch_iga_deals", return_value=IGA_DEALS)
@patch("main.fetch_metro_deals", return_value=METRO_DEALS)
@patch("main.fetch_maxi_deals", return_value=MAXI_DEALS)
@patch("main.load_config")
def test_run_happy_path(mock_cfg, mock_maxi, mock_metro, mock_iga, mock_provigo, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        email_from="noreply@grocerybot.local", mailersend_email="user@example.com", mailersend_api_key="pw",
        email_recipient="b@example.com", max_deals_per_store=10,
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
@patch("main.fetch_provigo_deals", side_effect=Exception("Blocked"))
@patch("main.fetch_iga_deals", side_effect=Exception("Blocked"))
@patch("main.fetch_metro_deals", side_effect=Exception("Blocked"))
@patch("main.fetch_maxi_deals", side_effect=Exception("Blocked"))
@patch("main.load_config")
def test_run_all_scrapers_fail_uses_demo_data(mock_cfg, mock_maxi, mock_metro, mock_iga, mock_provigo, mock_recipes, mock_render, mock_send):
    # When all scrapers fail, demo data is used
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        email_from="noreply@grocerybot.local", mailersend_email="user@example.com", mailersend_api_key="pw",
        email_recipient="b@example.com", max_deals_per_store=10,
    )
    from main import run
    run()
    mock_send.assert_called_once()
    # Demo data should have been used
    all_deals = mock_render.call_args[0][0]
    assert len(all_deals) > 0  # Demo data provides sample deals


@patch("main.send_email")
@patch("main.render_email", return_value="<html>test</html>")
@patch("main.fetch_recipes", return_value=[])
@patch("main.fetch_provigo_deals", return_value=[])
@patch("main.fetch_iga_deals", return_value=[])
@patch("main.fetch_metro_deals", return_value=[])
@patch("main.fetch_maxi_deals", return_value=[make_deal("Maxi", f"Item {i}") for i in range(20)])
@patch("main.load_config")
def test_run_respects_max_deals_per_store(mock_cfg, mock_maxi, mock_metro, mock_iga, mock_provigo, mock_recipes, mock_render, mock_send):
    mock_cfg.return_value = MagicMock(
        postal_code="J1H2B4", spoonacular_api_key="key",
        email_from="noreply@grocerybot.local", mailersend_email="user@example.com", mailersend_api_key="pw",
        email_recipient="b@example.com", max_deals_per_store=5,
    )
    from main import run
    run()
    all_deals = mock_render.call_args[0][0]
    maxi_deals = [d for d in all_deals if d.store == "Maxi"]
    assert len(maxi_deals) == 5
