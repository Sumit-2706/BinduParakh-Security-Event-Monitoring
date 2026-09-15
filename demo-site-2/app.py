"""
CloudDrive Admin -- a second, completely separate demo application.

This exists specifically to prove BinduParakh's *multi-site* claim for
real: that two different websites can each be registered as their own
"Site" in BinduParakh, each with its own API key, and each with alerts
routed to its own contact email -- not a shared inbox.

This app is intentionally themed and structured differently from
demo-site/ (that one is a shop login, this one is a fake admin-panel
login) so it's visually obvious in a demo that these are two unrelated
applications, not the same app copy-pasted.

Setup:
    pip install -r requirements.txt --break-system-packages
    export BINDUPARAKH_API_KEY="paste-the-key-for-THIS-site-from-Monitored-Sites-tab"
    export PORT=5001                      # demo-site already uses 5000
    python app.py

Then open http://localhost:5001 and try a few wrong passwords -- the
resulting alert will show up in BinduParakh tagged with THIS site's name,
and (if you configured a different contact email when registering it)
routed to a different inbox than demo-site's alerts.
"""
import os
import requests
from flask import Flask, request, render_template, redirect, session

app = Flask(__name__)
app.secret_key = "clouddrive-admin-not-for-production"

BINDUPARAKH_URL = os.getenv("BINDUPARAKH_URL", "http://localhost:8000")
API_KEY = os.getenv("BINDUPARAKH_API_KEY", "")

# Should match exactly what you typed into BinduParakh's "Register a
# website to monitor" form for THIS site -- shown on the page itself so
# it's obvious which registered site this app corresponds to.
SITE_NAME = os.getenv("SITE_NAME", "CloudDrive Admin")
SITE_CONTACT_EMAIL = os.getenv("SITE_CONTACT_EMAIL", "deepaksumitamr@gmail.com")

# Hardcoded demo admin account -- this is a toy app, not a real product.
DEMO_USER = {"email": "admin@clouddrive.io", "password": "AdminPass456!"}


def report_to_binduparakh(event_type: str, identity: str):
    """Tells BinduParakh what just happened. Fails silently if BinduParakh
    isn't reachable or no API key is configured -- this app should keep
    working even if the monitoring integration is down, exactly like a
    real production integration should behave."""
    if not API_KEY:
        print("[CloudDrive] No BINDUPARAKH_API_KEY set -- skipping report.")
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
        print(f"[CloudDrive] Could not report to BinduParakh: {exc}")


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        if email == DEMO_USER["email"] and password == DEMO_USER["password"]:
            report_to_binduparakh("login_success", email)
            session["logged_in"] = True
            return redirect("/panel")
        else:
            report_to_binduparakh("login_failure", email)
            error = "Invalid administrator credentials."

    return render_template(
        "login.html",
        error=error,
        site_name=SITE_NAME,
        site_contact_email=SITE_CONTACT_EMAIL,
        monitored=bool(API_KEY),
    )


@app.route("/panel")
def panel():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("panel.html", site_name=SITE_NAME)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
