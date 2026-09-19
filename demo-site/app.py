"""
DemoShop -- a tiny, standalone e-commerce-style login page.

This is a SEPARATE, unrelated application (its own Flask app, its own
process, nothing shared with BinduParakh's codebase) that genuinely
integrates with BinduParakh the way any real website would: on every
login attempt, it reports the outcome to BinduParakh's /ingest/log
endpoint using an API key. This proves the "add BinduParakh to any
website" concept for real, not just in a demo script.

Setup:
    pip install flask requests
    export BINDUPARAKH_API_KEY="paste-the-key-from-the-Monitored-Sites-tab"
    python app.py

Then open http://localhost:5000 and try logging in with wrong passwords
a few times -- watch the alert show up in BinduParakh's dashboard.
"""
import os
import secrets

import requests
from flask import Flask, request, render_template, redirect, session

app = Flask(__name__)
# Real deployments override this; if unset we generate a fresh random key
# every start (harmless for a toy app, and nothing is hardcoded in source).
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

BINDUPARAKH_URL = os.getenv("BINDUPARAKH_URL", "http://localhost:8000")
API_KEY = os.getenv("BINDUPARAKH_API_KEY", "")

# These two should match exactly what you typed into BinduParakh's
# "Register a website to monitor" form (Monitored Sites tab) -- shown on
# the page itself so it's obvious which registered site this app maps to
# and where its alerts are supposed to be routed.
SITE_NAME = os.getenv("SITE_NAME", "Demo Shop")
SITE_CONTACT_EMAIL = os.getenv("SITE_CONTACT_EMAIL", "shop-owner@example.com")

# Hardcoded demo account -- this is a toy app, not a real store.
DEMO_USER = {"email": "customer@demoshop.com", "password": "ShopPass123!"}


def report_to_binduparakh(event_type: str, identity: str):
    """Tells BinduParakh what just happened. Fails silently if BinduParakh
    isn't reachable or no API key is configured -- the demo store itself
    should keep working even if the monitoring integration is down,
    exactly like a real production integration should behave."""
    if not API_KEY:
        print("[DemoShop] No BINDUPARAKH_API_KEY set -- skipping report.")
        return
    try:
        requests.post(
            f"{BINDUPARAKH_URL}/ingest/log",
            headers={"X-API-Key": API_KEY},
            json={
                "event_type": event_type,
                "identity": identity,
                "ip_address": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
            },
            timeout=3,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[DemoShop] Could not report to BinduParakh: {exc}")


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        if email == DEMO_USER["email"] and password == DEMO_USER["password"]:
            report_to_binduparakh("login_success", email)
            session["logged_in"] = True
            return redirect("/account")
        else:
            report_to_binduparakh("login_failure", email)
            error = "Incorrect email or password."

    return render_template(
        "login.html",
        error=error,
        site_name=SITE_NAME,
        site_contact_email=SITE_CONTACT_EMAIL,
        monitored=bool(API_KEY),
    )


@app.route("/account")
def account():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("account.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1", use_reloader=False)
