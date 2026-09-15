"""
seed_demo.py -- populates BinduParakh with realistic-looking demo events so
the dashboard has something to show immediately, instead of starting empty.

Usage (after the stack is running):
    python seed_demo.py

Simulates:
  - a normal login
  - a brute-force burst (5+ failed logins -> triggers rapid_failed_logins)
  - an impossible-travel pair of logins (Delhi then London, 10 min apart)
  - a scanner user-agent request (triggers suspicious_user_agent)
  - a credential-stuffing burst (one device, many accounts)
"""
import time
import requests

API = "http://localhost:8000"
DEMO_EMAIL = "demo@binduparakh.local"
DEMO_PASSWORD = "DemoPass123!"


def ensure_demo_user():
    requests.post(f"{API}/auth/register", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    resp = requests.post(
        f"{API}/auth/login",
        data={"username": DEMO_EMAIL, "password": DEMO_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def log_event(token, payload):
    r = requests.post(
        f"{API}/events/log", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    r.raise_for_status()
    return r.json()


def main():
    token = ensure_demo_user()
    print("Logged in as demo user. Seeding events...")

    # 1. Normal login
    log_event(token, {
        "event_type": "login_success", "identity": "priya@example.com",
        "ip_address": "103.21.4.10", "user_agent": "Mozilla/5.0 (Windows NT 10.0)",
        "latitude": 28.6139, "longitude": 77.2090,
    })

    # 2. Brute force burst -> rapid_failed_logins
    for _ in range(6):
        log_event(token, {
            "event_type": "login_failure", "identity": "admin@example.com",
            "ip_address": "185.220.101.5", "user_agent": "python-requests/2.31",
        })
        time.sleep(0.2)

    # 3. Impossible travel -> two logins for same identity, far apart, close in time
    log_event(token, {
        "event_type": "login_success", "identity": "rahul@example.com",
        "ip_address": "103.21.4.20", "user_agent": "Mozilla/5.0 (Macintosh)",
        "latitude": 28.6139, "longitude": 77.2090,  # Delhi
    })
    log_event(token, {
        "event_type": "login_success", "identity": "rahul@example.com",
        "ip_address": "51.15.10.20", "user_agent": "Mozilla/5.0 (Macintosh)",
        "latitude": 51.5072, "longitude": -0.1276,  # London, ~10 min "later" in real time
    })

    # 4. Suspicious scanner user-agent -> suspicious_user_agent
    log_event(token, {
        "event_type": "http_request", "ip_address": "45.155.205.1",
        "user_agent": "sqlmap/1.7.2#stable (http://sqlmap.org)",
    })

    # 5. Credential stuffing -> one device, many identities
    for i in range(5):
        log_event(token, {
            "event_type": "login_failure", "identity": f"user{i}@example.com",
            "ip_address": "192.0.2.55", "user_agent": "curl/8.1.2",
        })
        time.sleep(0.2)

    print("Done. Log in to the dashboard with:")
    print(f"  email:    {DEMO_EMAIL}")
    print(f"  password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
