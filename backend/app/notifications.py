"""
Email notifications for high-severity alerts.

Designed to fail gracefully: if SMTP isn't configured (e.g. running the
project locally without setting up an email account), the app still works
normally -- it just skips sending and logs a message instead of crashing.
This is what makes the project runnable "anywhere" without extra setup.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("binduparakh.notifications")

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def send_alert_email(rule_name: str, severity: str, description: str, recipient: str = None) -> bool:
    """
    Sends an email if:
      1. SMTP is configured (host/user/password all set), AND
      2. a recipient is available (either the `recipient` argument -- used
         for site-specific alerts -- or the global ALERT_EMAIL_TO fallback
         for BinduParakh's own self-monitoring), AND
      3. the alert severity meets or exceeds ALERT_EMAIL_MIN_SEVERITY.
    Returns True if an email was actually sent, False otherwise (never raises --
    a failed notification should never break the request that triggered it).
    """
    to_address = recipient or settings.ALERT_EMAIL_TO
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD, to_address]):
        logger.info("SMTP not configured or no recipient -- skipping email for alert '%s'", rule_name)
        return False

    min_rank = SEVERITY_RANK.get(settings.ALERT_EMAIL_MIN_SEVERITY, 2)
    if SEVERITY_RANK.get(severity, 0) < min_rank:
        return False

    subject = f"[BinduParakh] {severity.upper()} alert: {rule_name}"
    body = f"Rule: {rule_name}\nSeverity: {severity}\n\n{description}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_address

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Alert email sent for rule '%s' to %s", rule_name, to_address)
        return True
    except Exception as exc:  # noqa: BLE001 -- notification failure must not crash the app
        logger.error("Failed to send alert email: %s", exc)
        return False
