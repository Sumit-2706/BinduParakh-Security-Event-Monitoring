"""
seed_demo.py -- populates BinduParakh with realistic-looking demo events so
the dashboard has something to show immediately, instead of starting empty.

Usage (after the stack is running):
    python seed_demo.py

Logs in as the admin account that the backend auto-creates from your
environment variables, registers a demo site, and ingests the sample
events through the SAME public API-key endpoint (POST /ingest/log) that a
real monitored website uses -- so the demo exercises the exact production
integration path.

Simulates:
  - a normal login
  - a brute-force burst (5+ failed logins -> triggers rapid_failed_logins)
  - an impossible-travel pair of logins (Delhi then London, 10 min apart)
  - a scanner user-agent request (triggers suspicious_user_agent)
  - a credential-stuffing burst (one device, many accounts)
"""
import os
import time
import requests

API = "http://localhost:8000"

# These must match backend/.env (or the app's documented fallback values).
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-password")
SITE_NAME = os.getenv("SITE_NAME", "Demo Site")
SITE_CONTACT_EMAIL = os.getenv("SITE_CONTACT_EMAIL", "demo-owner@example.com")


def admin_token():
    resp = requests.post(
        f"{API}/auth/login",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def ensure_demo_site(token: str) -> str:
    """Creates the demo monitored site and returns its API key -- the same
    key a real website's backend would use. The API key is only returned
    by the create call, so re-running this seed just creates a fresh site
    each time."""
    r = requests.post(
        f"{API}/sites",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": SITE_NAME, "contact_email": SITE_CONTACT_EMAIL},
    )
    r.raise_for_status()
    return r.json()["api_key"]


def log_event(api_key: str, payload: dict):
    r = requests.post(
        f"{API}/ingest/log",
        json=payload,
        headers={"X-API-Key": api_key},
    )
    r.raise_for_status()
    return r.json()


def main():
    token = admin_token()
    api_key = ensure_demo_site(token)
    if not api_key:
        raise SystemExit("Could not obtain a demo site API key -- see messages above.")
    print(f"Logged in as admin ({ADMIN_EMAIL}). Seeding events via /ingest/log ...")

    # 1. Normal login
    log_event(api_key, {
        "event_type": "login_success", "identity": "priya@example.com",
        "ip_address": "103.21.4.10", "user_agent": "Mozilla/5.0 (Windows NT 10.0)",
        "latitude": 28.6139, "longitude": 77.2090,
    })

    # 2. Brute force burst -> rapid_failed_logins
    for _ in range(6):
        log_event(api_key, {
            "event_type": "login_failure", "identity": "admin@example.com",
            "ip_address": "185.220.101.5", "user_agent": "python-requests/2.31",
        })
        time.sleep(0.2)

    # 3. Impossible travel -> two logins for same identity, far apart, close in time
    log_event(api_key, {
        "event_type": "login_success", "identity": "rahul@example.com",
        "ip_address": "103.21.4.20", "user_agent": "Mozilla/5.0 (Macintosh)",
        "latitude": 28.6139, "longitude": 77.2090,  # Delhi
    })
    log_event(api_key, {
        "event_type": "login_success", "identity": "rahul@example.com",
        "ip_address": "51.15.10.20", "user_agent": "Mozilla/5.0 (Macintosh)",
        "latitude": 51.5072, "longitude": -0.1276,  # London, ~10 min "later" in real time
    })

    # 4. Suspicious scanner user-agent -> suspicious_user_agent
    log_event(api_key, {
        "event_type": "http_request", "ip_address": "45.155.205.1",
        "user_agent": "sqlmap/1.7.2#stable (http://sqlmap.org)",
    })

    # 5. Credential stuffing -> one device, many identities
    for i in range(5):
        log_event(api_key, {
            "event_type": "login_failure", "identity": f"user{i}@example.com",
            "ip_address": "192.0.2.55", "user_agent": "curl/8.1.2",
        })
        time.sleep(0.2)

    print("Done. Log in to the dashboard with your admin account:")
    print(f"  email:    {ADMIN_EMAIL}")
    print(f"  password: {ADMIN_PASSWORD}")

    if not os.getenv("ADMIN_PASSWORD"):
        print("  (You didn't set ADMIN_PASSWORD in backend/.env, so the app's")
        print("   documented fallback 'change-this-password' was used above.)")


if __name__ == "__main__":
    main()