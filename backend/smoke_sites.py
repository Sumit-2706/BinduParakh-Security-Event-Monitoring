import os
os.environ["DATABASE_URL"] = "sqlite:///./smoke_sites.db"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Importing app.main seeds the admin account from the same env defaults the
# app uses, so log in as that admin rather than registering (registration
# never grants admin anymore).
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-password")

print("1. Login as the auto-seeded admin...")
r = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                headers={"Content-Type": "application/x-www-form-urlencoded"})
assert r.status_code == 200, r.text
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("   OK")

print("\n2. SELF-MONITORING: brute-force BinduParakh's own login 6 times...")
for i in range(6):
    r = client.post("/auth/login", data={"username": ADMIN_EMAIL, "password": "wrong_password"},
                     headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 401
print("   6 failed logins sent, all correctly rejected with 401")

r = client.get("/alerts", headers=headers)
self_alerts = [a for a in r.json() if a["rule_name"] == "rapid_failed_logins"]
assert len(self_alerts) >= 1, "Expected BinduParakh to detect the brute-force attempt against ITSELF"
print("   OK: BinduParakh detected the attack on its OWN login ->", self_alerts[0]["description"])
assert self_alerts[0]["technique"]["technique_id"] == "T1110"
print("   OK: self-monitoring alert is correctly tagged with T1110")

print("\n3. MULTI-SITE: register an external website...")
r = client.post("/sites", json={"name": "Demo Shop", "contact_email": "shopowner@example.com"}, headers=headers)
assert r.status_code == 200, r.text
site = r.json()
api_key = site["api_key"]
print("   OK: site created ->", site["name"], "| API key:", api_key[:8] + "...")

print("\n4. Simulate the external site reporting a brute-force attack via API key (no JWT)...")
for i in range(6):
    r = client.post("/ingest/log",
                     json={"event_type": "login_failure", "identity": "customer@demoshop.com", "ip_address": "5.5.5.5"},
                     headers={"X-API-Key": api_key})
    assert r.status_code == 200, r.text
print("   OK: 6 events ingested via API key, no dashboard login needed")

print("\n5. Confirm the alert exists and is tied to the SITE's event, not the dashboard...")
r = client.get("/alerts", headers=headers)
site_alerts = [a for a in r.json() if "customer@demoshop.com" in a["description"]]
assert len(site_alerts) >= 1
print("   OK: alert generated from the external site's traffic ->", site_alerts[0]["description"])

print("\n6. Confirm wrong API key is rejected...")
r = client.post("/ingest/log", json={"event_type": "login_failure"}, headers={"X-API-Key": "not-a-real-key"})
assert r.status_code == 401
print("   OK: invalid API key correctly rejected with 401")

print("\n*** ALL SELF-MONITORING + MULTI-SITE CHECKS PASSED ***")
