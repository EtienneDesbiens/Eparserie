import pytest
import sys
from unittest.mock import patch, MagicMock
from email_sender import render_email, send_email, STORE_ORDER


def test_render_email_contains_store_name(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], [])
    assert "MAXI" in html
    assert "METRO" in html


def test_render_email_shows_failed_store(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], ["Costco"])
    assert "Costco" in html
    assert "unavailable" in html.lower()


def test_render_email_no_recipes(sample_deals):
    html = render_email(sample_deals, [], [])
    assert "Suggested Recipes" not in html


def test_render_email_maxi_first(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], [])
    maxi_pos = html.find("MAXI")
    metro_pos = html.find("METRO")
    assert maxi_pos < metro_pos


def test_render_email_shows_discount(sample_deals, sample_recipe):
    html = render_email(sample_deals, [sample_recipe], [])
    assert "-38%" in html  # maxi_deal has 38.5% → int = 38


def test_send_email_mailtrap(sample_deals, sample_recipe):
    """Test that Mailtrap SMTP is called correctly."""
    html = render_email(sample_deals, [sample_recipe], [])

    with patch("email_sender.smtplib.SMTP") as MockSMTP:
        mock_instance = MagicMock()
        MockSMTP.return_value.__enter__ = MagicMock(return_value=mock_instance)
        MockSMTP.return_value.__exit__ = MagicMock(return_value=False)

        send_email(html, "noreply@grocerybot.local", "user", "pass", "recipient@example.com")

    # Verify Mailtrap SMTP server was used
    MockSMTP.assert_called_once_with("live.smtp.mailtrap.io", 587)
    mock_instance.starttls.assert_called_once()
    mock_instance.login.assert_called_once_with("user", "pass")
    mock_instance.sendmail.assert_called_once()
