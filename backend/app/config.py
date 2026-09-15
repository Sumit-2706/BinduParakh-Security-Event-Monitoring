"""
Centralized configuration, read from environment variables (with sane
local-dev defaults). Keeping all config in one place makes the app portable
across machines/deployments -- nothing is hardcoded.
"""
import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://binduparakh:binduparakh@localhost:5432/binduparakh",
    )
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-this-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # Detection thresholds -- tunable without touching code
    FAILED_LOGIN_THRESHOLD: int = int(os.getenv("FAILED_LOGIN_THRESHOLD", "5"))
    FAILED_LOGIN_WINDOW_MIN: int = int(os.getenv("FAILED_LOGIN_WINDOW_MIN", "5"))
    IMPOSSIBLE_TRAVEL_MAX_KMH: float = float(os.getenv("IMPOSSIBLE_TRAVEL_MAX_KMH", "900"))
    MULTI_ACCOUNT_THRESHOLD: int = int(os.getenv("MULTI_ACCOUNT_THRESHOLD", "4"))
    MULTI_ACCOUNT_WINDOW_MIN: int = int(os.getenv("MULTI_ACCOUNT_WINDOW_MIN", "10"))

    # Optional third-party VPN/proxy intelligence lookup.
    # If no key is set, the VPN detection rule is skipped gracefully
    # instead of crashing -- important for "works anywhere" portability.
    IPQUALITYSCORE_API_KEY: str = os.getenv("IPQUALITYSCORE_API_KEY", "")

    # Email (SMTP) settings for alert notifications
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    ALERT_EMAIL_TO: str = os.getenv("ALERT_EMAIL_TO", "")
    ALERT_EMAIL_MIN_SEVERITY: str = os.getenv("ALERT_EMAIL_MIN_SEVERITY", "high")


settings = Settings()
