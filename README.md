# BinduParakh

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![MITRE ATT&CK](https://img.shields.io/badge/MITRE%20ATT%26CK-Enterprise%20v17-b71c1c)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A lightweight, self-hosted security event monitoring platform. It ingests
security-relevant events (logins, HTTP requests) from an application, runs
them through a real-time detection engine, and surfaces suspicious activity
on a live dashboard — tagged with the relevant MITRE ATT&CK technique, and
optionally emailed to an admin the moment something high-severity happens.

Built as a final-year cybersecurity project. Every detection rule below is
implemented from scratch in this repo — no forked code.

> **⚠️ Before you push this to a public repo or deploy it:** the default
> admin account is intentionally seeded with placeholder credentials
> (`admin@example.com` / `change-this-password`), not real ones. Set your
> own via `ADMIN_EMAIL` / `ADMIN_PASSWORD` in a local, untracked `.env`
> file — see [Configuration](#configuration). `.gitignore` already keeps
> `.env` out of git, so don't rename it into a tracked file.

## Table of Contents

- [MITRE ATT&CK Integration](#mitre-attck-integration)
- [Self-monitoring](#self-monitoring)
- [Monitoring other websites (multi-site)](#monitoring-other-websites-multi-site)
- [What it detects](#what-it-detects)
- [Architecture](#architecture)
- [Screenshots](#screenshots)
- [Running it locally (Docker)](#running-it-locally-docker--recommended-works-anywhere)
- [Running it without Docker](#running-it-without-docker-manual-setup)
- [Testing](#testing)
- [Configuration](#configuration)
- [Deploying publicly](#deploying-publicly-vercel--a-backend-host)
- [Known limitations](#known-limitations-intentional-scope-for-a-student-project)
- [License](#license)

## MITRE ATT&CK Integration

BinduParakh doesn't just tag alerts with a made-up label — it imports
MITRE's actual, official Enterprise ATT&CK dataset (published by MITRE at
[github.com/mitre-attack/attack-stix-data](https://github.com/mitre-attack/attack-stix-data))
directly into its own database:

- **15 tactics** (MITRE recently restructured "Defense Evasion" into two
  separate tactics — "Defense Impairment" and "Stealth" — this project
  reflects that current structure, not an outdated one)
- **697 techniques and sub-techniques**, each with MITRE's real
  description, detection guidance, and recommended mitigations
- Every alert links to a **real `Technique` database row** via foreign
  key — not a hardcoded string — so if MITRE updates a technique's
  description, re-running the loader updates it everywhere in the app
  automatically
- A full **ATT&CK Matrix page** in the dashboard to browse and search all
  697 techniques by tactic or keyword, exactly like the official
  attack.mitre.org site, but built into your own tool

Run `backend/scripts/refresh_attack_data.py` any time to re-download the
latest MITRE dataset and refresh the local copy.

## Self-monitoring

BinduParakh doesn't just watch other applications -- it watches its own
front door too. A failed login attempt against BinduParakh's own
dashboard runs through the exact same detection engine as everything
else, so someone brute-forcing your own BinduParakh login shows up in
your own Alerts tab, tagged with the correct MITRE technique.

## Monitoring other websites (multi-site)

Any website can be monitored by BinduParakh:

1. In the dashboard, go to **Monitored sites** and register a site with a
   name and a contact email.
2. Copy the API key it generates.
3. In that site's backend, call `POST /ingest/log` with header
   `X-API-Key: <the key>` whenever something worth watching happens
   (a login attempt, etc.) -- no BinduParakh account needed for the site
   itself.
4. Alerts for that site are emailed to **that site's own contact email**,
   not a shared inbox -- each monitored site's team gets notified about
   their own site.

### Try it end-to-end with the included demo site

`demo-site/` is a small, completely separate Flask app (its own login
page, its own process) that genuinely integrates with BinduParakh the
way any real website would:

```bash
cd demo-site
pip install -r requirements.txt --break-system-packages
export BINDUPARAKH_API_KEY="paste-the-key-from-Monitored-Sites-tab"
export SITE_NAME="Demo Shop"                       # optional -- must match what you typed when registering
export SITE_CONTACT_EMAIL="you@example.com"        # optional -- shown on the page for confirmation
python app.py
```

Open http://localhost:5000 -- the page header shows a green
"Monitored by BinduParakh · alerts go to <email>" badge once the API
key is set, confirming the connection before you even log in. Try the
wrong password a few times (demo login is `customer@demoshop.com` /
`ShopPass123!`), then check BinduParakh's Alerts tab -- a real alert
from a real, separate application will show up there, correctly
MITRE-tagged, and any alert email goes to the contact address you
registered for that specific site.

### Proving true multi-site isolation with a second demo app

`demo-site-2/` is a **second, unrelated** Flask app ("CloudDrive Admin" --
a different theme, different login flow, different port) included
specifically to prove the multi-site claim isn't just one integration
copy-pasted twice:

```bash
cd demo-site-2
pip install -r requirements.txt --break-system-packages
export BINDUPARAKH_API_KEY="the-key-for-a-SECOND-site-you-register"
export SITE_NAME="CloudDrive Admin"
export SITE_CONTACT_EMAIL="a-different-email@example.com"
export PORT=5001                              # demo-site already uses 5000
python app.py
```

Open http://localhost:5001 (demo login: `admin@clouddrive.io` /
`AdminPass456!`) and run the same brute-force test. Register both sites
with **different contact emails** in the Monitored Sites tab and you can
watch each one's alert route to its own inbox, from two apps running at
the same time -- that's the actual proof, not just a diagram of it.

## What it detects

| Rule | What it catches | MITRE ATT&CK |
|---|---|---|
| `rapid_failed_logins` | A burst of failed logins against one account in a short window (brute force) | T1110 - Brute Force |
| `impossible_travel` | Two successful logins for the same account, too far apart geographically to be the same person | T1078 - Valid Accounts |
| `suspicious_user_agent` | Requests carrying known scanner-tool signatures (sqlmap, nikto, nmap, etc.) | T1595 - Active Scanning |
| `vpn_proxy_login` | Logins originating from a known VPN/proxy/hosting IP (optional, needs a free IPQualityScore key) | T1090 - Proxy |
| `credential_stuffing` | One device (IP + user-agent) trying many different accounts in a short window | T1110.004 - Credential Stuffing |

Each of these 5 rules is only mapped to *one* technique each — but because
the full 697-technique matrix is loaded and browsable, extending detection
to cover a 6th, 7th, or 20th technique is just adding a new rule function
and pointing it at any real technique ID already sitting in the database.

## Architecture

```
Monitored app ──POST /events/log──► FastAPI backend ──► detection engine (5 rules)
                                          │                        │
                                          ▼                        ▼
                                     PostgreSQL              new Alert rows
                                                            (FK → real Technique row)
                                                                    │
                                                          (if severity is high enough)
                                                                    ▼
                                                            email notification
                                                                    │
React dashboard ◄──polls /events, /alerts every 5s────────────────┘
        │
        └── ATT&CK Matrix tab ──GET /attack/techniques──► full 697-technique browser
```

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, JWT auth
- **Frontend:** React + Vite, polling-based live updates
- **Detection:** pure Python functions, independently unit-tested (see `backend/tests/`)
- **Notifications:** SMTP email, fails gracefully if not configured
- **Threat intelligence:** MITRE ATT&CK Enterprise matrix, imported from MITRE's official published dataset

### Project structure

```
binduparakh/
├── backend/            # FastAPI app: auth, detection engine, ATT&CK data, email
│   ├── app/
│   ├── tests/          # pytest unit tests for detection + notifications
│   └── scripts/        # refresh_attack_data.py -- re-pull MITRE's dataset
├── frontend/            # React + Vite dashboard
├── demo-site/           # Standalone Flask app #1 -- proves real multi-site integration
├── demo-site-2/         # Standalone Flask app #2 -- proves per-site email routing
├── seed_demo.py          # Fires sample events so the dashboard isn't empty on first run
└── docker-compose.yml    # One command to run backend + frontend + Postgres together
```

## Screenshots

> Add your own screenshots here before publishing — put the image files in
> a `docs/screenshots/` folder in this repo and reference them like this:
>
> ```markdown
> ![Dashboard](docs/screenshots/dashboard.png)
> ![Alerts with MITRE tags](docs/screenshots/alerts.png)
> ![ATT&CK Matrix browser](docs/screenshots/attack-matrix.png)
> ```
>
> Good screenshots to include: the Alerts tab with at least one real
> alert, the ATT&CK Matrix wheel, and the Monitored Sites page with the
> API key flow.

## Running it locally (Docker — recommended, works anywhere)

Requires Docker + Docker Compose.

```bash
git clone <your-fork-url>
cd binduparakh
cp backend/.env.example backend/.env
docker compose up --build
```

Then open:
- Dashboard: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs

A default admin account is **created automatically on every backend
startup** (from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in your `backend/.env`),
so the dashboard is usable immediately without registering anything
first. Set those two values in `backend/.env` before your first
`docker compose up` — if you leave them unset, the seeded fallback login
is `admin@example.com` / `change-this-password` (intentionally not a real
credential, since `.env.example` is committed to this repo).

Log in at http://localhost:5173/login with whatever you set. (You can
still register additional accounts via the login screen's flow or
`POST /auth/register` — the **first account you register also becomes an
admin automatically** if no admin exists yet — but with the env-var seed
above, you no longer need to.)

### Populate demo data

To see the dashboard with realistic alerts immediately instead of starting
empty:

```bash
pip install requests --break-system-packages   # if not already installed
python seed_demo.py
```

This creates a demo user and fires events that trigger all five rules
(brute force, impossible travel, scanner detection, credential stuffing —
VPN detection only fires if you've configured `IPQUALITYSCORE_API_KEY`).

## Running it without Docker (manual setup)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Point DATABASE_URL at a local Postgres instance in .env, then:
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Testing

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

The test suite covers the detection engine's pure logic (distance math,
MITRE mapping completeness) and the notification module (mocked SMTP — no
real email account needed to run tests). These are fast, dependency-free
unit tests; testing the full HTTP flow requires a running Postgres instance
and is best done manually via the Swagger UI at `/docs` or with the
`seed_demo.py` script above.

## Configuration

All tunables (detection thresholds, SMTP, optional VPN API key) live in
`backend/.env` — see `backend/.env.example` for the full list with
explanations. Nothing is hardcoded, so the same code runs identically on
any machine or deployment target.

## Deploying publicly (Vercel + a backend host)

Vercel serves the React frontend well, but it does **not** run a
long-lived Python process + PostgreSQL database, so the backend needs a
separate host that does (e.g. Railway, Render, or Fly.io). The two pieces
talk to each other over plain HTTPS, so this is a two-deployment setup:

1. **Backend** — deploy `backend/` (with a managed Postgres add-on) to
   Railway/Render/Fly. Set these environment variables there:
   - `ADMIN_EMAIL` / `ADMIN_PASSWORD` — your real admin login. **Do not
     leave these as the source-code defaults on a public deployment** —
     anyone who can read this repo's `main.py` knows those fallback
     values.
   - `GUEST_EMAIL` / `GUEST_PASSWORD` — a shared, read-only demo login
     (role `analyst`) safe to publish alongside your live link, e.g. in a
     LinkedIn post: *"Demo login: guest@binduparakh.demo / guest1234"*.
     Guests can view Alerts/Events/the ATT&CK matrix/Threat news, but
     can't register sites or reach anything admin-only.
   - `FRONTEND_URL` — your deployed Vercel URL (e.g.
     `https://binduparakh.vercel.app`), so CORS allows it.
2. **Frontend** — deploy `frontend/` to Vercel, setting `VITE_API_URL` to
   your backend's public URL (see the frontend Dockerfile's `--build-arg
   VITE_API_URL` for how this is wired in locally).

Once both are live, share the guest login publicly and keep the admin
credentials private — that's the same admin/analyst split used locally,
just with real secrets instead of the local defaults.

## Known limitations (intentional scope for a student project)

- Live updates use polling (every 5s), not WebSockets — simpler to reason
  about and sufficient for a SOC dashboard at this scale; a real-time
  WebSocket push is a natural next step.
- `Base.metadata.create_all()` is used instead of Alembic migrations —
  fine for a single-developer project, but a production system should use
  proper migrations.
- VPN/proxy detection requires a free third-party API key and is skipped
  gracefully if not configured, rather than blocking the whole app on a
  missing credential.

## License

MIT
