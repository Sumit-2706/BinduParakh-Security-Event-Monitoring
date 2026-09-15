"""
Tests for the email notification module. Uses monkeypatching so no real
SMTP server or credentials are needed to run the test suite.
"""
from unittest.mock import patch

from app import notifications
from app.config import settings


def test_send_alert_email_skips_when_smtp_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "")
    sent = notifications.send_alert_email("rapid_failed_logins", "high", "test description")
    assert sent is False


def test_send_alert_email_skips_below_min_severity(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_USER", "user@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pw")
    monkeypatch.setattr(settings, "ALERT_EMAIL_TO", "admin@example.com")
    monkeypatch.setattr(settings, "ALERT_EMAIL_MIN_SEVERITY", "critical")

    sent = notifications.send_alert_email("suspicious_user_agent", "medium", "test description")
    assert sent is False


def test_send_alert_email_sends_when_configured_and_severe(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_USER", "user@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "pw")
    monkeypatch.setattr(settings, "ALERT_EMAIL_TO", "admin@example.com")
    monkeypatch.setattr(settings, "ALERT_EMAIL_MIN_SEVERITY", "high")

    with patch("smtplib.SMTP") as mock_smtp:
        instance = mock_smtp.return_value.__enter__.return_value
        sent = notifications.send_alert_email(
            "rapid_failed_logins", "high", "5 failed logins detected"
        )
        assert sent is True
        instance.login.assert_called_once()
        instance.send_message.assert_called_once()
