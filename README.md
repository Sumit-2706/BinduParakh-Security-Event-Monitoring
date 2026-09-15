# BinduParakh

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A self-hosted security event monitoring platform. It ingests security events
(logins, HTTP requests) from any application, runs them through a real-time
detection engine, and surfaces suspicious activity on a live dashboard —
tagged with the relevant MITRE ATT&CK technique, and optionally emailed to
an admin when something high-severity happens.

Built as a final-year cybersecurity project. Every detection rule is
implemented from scratch — no forked code.

## Table of Contents

- [MITRE ATT&CK Integration](#mitre-attck-integration)
- [Self-monitoring](#self-monitoring)
- [Multi-site monitoring](#multi-site-monitoring)
- [What it detects](#what-it-detects)
- [Architecture](#architecture)
- [Setup](#setup)
- [Testing](#testing)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Known limitations](#known-limitations)
- [License](#license)

## MITRE ATT&CK Integration

BinduParakh imports MITRE's official Enterprise ATT&CK dataset directly
into its own database — **15 tactics, 697 techniques and sub-techniques**,
each with MITRE's real description, detection guidance, and mitigations.
Every alert links to a real `Technique` row via foreign key, and the
dashboard includes a full ATT&CK Matrix browser. Run
`backend/scripts/refresh_attack_data.py` any time to re-pull the latest
dataset.

## Self-monitoring

BinduParakh watches its own login page with the same detection engine used
for everything else — a brute-force attempt against BinduParakh itself
shows up in its own Alerts tab.

## Multi-site monitoring

Any website can be monitored:

1. In the dashboard, go to **Monitored Sites** and register a site with a
   name and contact email.
2. Copy the generated API key.
3. From that site's backend, call `POST /ingest/log` with header
   `X-API-Key: <key>` whenever something worth watching happens.
4. Alerts for that site are emailed to **that site's own contact email**,
   not a shared inbox.

Two standalone demo apps are included to prove this end-to-end:

- `demo-site/` — a shop login page (port 5000)
- `demo-site-2/` — an unrelated admin panel, "CloudDrive Admin" (port 5001)

```bash
cd demo-site
pip install -r requirements.txt --break-system-packages
export BINDUPARAKH_API_KEY="key-from-Monitored-Sites-tab"
python app.py
```

Open http://localhost:5000, try a wrong password a few times (demo login:
`customer@demoshop.com` / `ShopPass123!`), then check BinduParakh's Alerts
tab. Run `demo-site-2/` the same way (`PORT=5001`, its own API key) to see
two sites' alerts route to two different inboxes at once.

## What it detects

| Rule | What it catches | MITRE ATT&CK |
|---|---|---|
| `rapid_failed_logins` | Burst of failed logins on one account (brute force) | T1110 |
| `impossible_travel` | Two logins for one account, too far apart geographically | T1078 |
| `suspicious_user_agent` | Known scanner-tool signatures (sqlmap, nikto, nmap) | T1595 |
| `vpn_proxy_login` | Login from a known VPN/proxy/hosting IP (optional) | T1090 |
| `credential_stuffing` | One IP/device trying many accounts in a short window | T1110.004 |

## Architecture

```
Monitored app ──POST /ingest/log──► FastAPI backend ──► detection engine (5 rules)
                                         │                        │
                                         ▼                        ▼
                                    PostgreSQL              new Alert rows
                                                           (FK → Technique row)
                                                                   │
                                                        (if severity ≥ threshold)
                                                                   ▼
                                                           email notification

React dashboard ◄──polls /events, /alerts every 5s──────────────┘
```

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, JWT auth
- **Frontend:** React + Vite
- **Detection:** pure Python, unit-tested (`backend/tests/`)
- **Notifications:** SMTP, fails gracefully if unconfigured

```
binduparakh/
├── backend/          # FastAPI app: auth, detection engine, ATT&CK data, email
├── frontend/         # React + Vite dashboard
├── demo-site/        # Standalone Flask app #1 (multi-site proof)
├── demo-site-2/      # Standalone Flask app #2 (multi-site proof)
├── seed_demo.py       # Fires sample events for a populated dashboard
└── docker-compose.yml
```

## Setup

Requires Docker + Docker Compose.

```bash
git clone <your-fork-url>
cd binduparakh
cp backend/.env.example backend/.env
```

Open `backend/.env` and set `ADMIN_EMAIL` / `ADMIN_PASSWORD` to your own
login — this account is auto-created on startup.

```bash
docker compose up --build
```

- Dashboard: http://localhost:5173
- API docs: http://localhost:8000/docs

For a populated dashboard instead of an empty one:

```bash
pip install requests --break-system-packages
python seed_demo.py
```

**Without Docker:**

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install && cp .env.example .env
npm run dev
```

## Testing

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

Covers the detection engine's logic and the notification module (mocked
SMTP). The full HTTP flow is best tested manually via `/docs` or
`seed_demo.py`.

## Configuration

All tunables — detection thresholds, SMTP, optional VPN API key, admin/guest
credentials — live in `backend/.env`. See `backend/.env.example` for the
full list.

## Deployment

Vercel hosts the React frontend; the backend (FastAPI + PostgreSQL) needs a
host that runs long-lived processes, e.g. Railway, Render, or Fly.io.

1. **Backend** — deploy with a managed Postgres add-on. Set `ADMIN_EMAIL`,
   `ADMIN_PASSWORD`, `FRONTEND_URL` (your Vercel URL, for CORS), and
   optionally `GUEST_EMAIL`/`GUEST_PASSWORD` for a public read-only demo
   login.
2. **Frontend** — deploy to Vercel with `VITE_API_URL` pointing at the
   backend.

## Known limitations

- Live updates use polling (5s), not WebSockets.
- `Base.metadata.create_all()` is used instead of Alembic migrations.
- VPN/proxy detection needs a free third-party API key and is skipped if
  unconfigured.

## License

MIT
