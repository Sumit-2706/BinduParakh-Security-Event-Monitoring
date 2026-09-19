# BinduParakh · Security Event Monitoring

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-21%20passing-4fae8c)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A self-hosted **security event monitoring platform** with a live SOC-style
dashboard. BinduParakh ingests security events (logins, HTTP requests) from
**any application**, runs them through a real-time **detection engine**, and
surfaces suspicious activity tagged with the relevant **MITRE ATT&CK**
technique — and can email the site's own team when something high-severity
happens.

Built from scratch as a final-year cybersecurity project. Every detection rule
is original, unit-tested code (no forked/borrowed logic).

## Highlights

- **Real MITRE ATT&CK Enterprise matrix** (15 tactics, 700+ techniques) loaded
  into the database from MITRE's official STIX dataset — alerts link to real
  technique rows via foreign key.
- **Self-monitoring** — BinduParakh watches its *own* login page with the same
  detection engine, so a brute-force attempt against *you* shows up in your own
  Alerts tab.
- **Multi-site monitoring** — any website can register for an API key and route
  its alerts to **its own contact email**, not a shared inbox.
- **Hardened by default** — per-IP rate limiting on auth & ingest, security
  headers on every response, JWT auth with bcrypt, per-user data scoping, and a
  DB-aware `/ready` healthcheck for orchestrators.
- **Live threat news** — real headlines fetched from The Hacker News RSS feed,
  cached, with graceful degradation.
- **Cyber-native UI** — dark SOC console aesthetic: radar-badge logo, ATT&CK
  hub wheel, live news ticker, severity pills, and a LIVE/OFFLINE connection
  indicator.

## Table of Contents

- [MITRE ATT&CK Integration](#mitre-attck-integration)
- [Self-monitoring](#self-monitoring)
- [Multi-site monitoring](#multi-site-monitoring)
- [What it detects](#what-it-detects)
- [Security & Hardening](#security--hardening)
- [Architecture](#architecture)
- [Setup](#setup)
- [Testing](#testing)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Known limitations](#known-limitations)
- [License](#license)

## MITRE ATT&CK Integration

BinduParakh imports **MITRE's official Enterprise ATT&CK dataset** straight
into its own database — **15 tactics, 700+ techniques and sub-techniques**,
each with MITRE's real description, detection guidance, and mitigations. Every
alert links to a real `Technique` row via a foreign key, and the dashboard
includes a full **ATT&CK Matrix browser** with a tactic hub wheel and technique
search. Run `backend/scripts/refresh_attack_data.py` any time to re-pull the
latest dataset from MITRE.

## Self-monitoring

BinduParakh watches its own login page with the **same detection engine** used
for everything else. A failed dashboard login is ingested as a real event
(scoped as "internal"), runs through every rule, and — success or not — a
brute-force attempt against BinduParakh itself shows up in its own **Alerts**
tab, tagged with the matching MITRE technique. *Who watches the watchers? The
watchers.*

## Multi-site monitoring

Any website can be monitored:

1. In the dashboard, open **Monitored Sites** and register a site with a name
   and contact email.
2. Copy the generated API key (shown once, never in listings).
3. From that site's backend, call `POST /ingest/log` with header
   `X-API-Key: <key>` whenever something worth watching happens.
4. Alerts for that site are emailed to **that site's own contact email**, not a
   shared inbox.

Two standalone demo apps prove this end-to-end:

- `demo-site/` — a shop login page (port 5000)
- `demo-site-2/` — an unrelated admin panel, "CloudDrive Admin" (port 5001)

```bash
cd demo-site
pip install -r requirements.txt --break-system-packages
export BINDUPARAKH_API_KEY="key-from-Monitored-Sites-tab"
python app.py
```

Open http://localhost:5000, try a wrong password a few times (demo login:
`customer@demoshop.com` / `ShopPass123!`), then check BinduParakh's Alerts tab.
Run `demo-site-2/` the same way (`PORT=5001`, its own API key) to see two
sites' alerts route to two different inboxes at once.

## What it detects

| Rule | What it catches | MITRE ATT&CK |
|---|---|---|
| `rapid_failed_logins` | Burst of failed logins on one account (brute force) | T1110 |
| `impossible_travel` | Two logins for one account, too far apart geographically | T1078 |
| `suspicious_user_agent` | Known scanner-tool signatures (sqlmap, nikto, nmap) | T1595 |
| `vpn_proxy_login` | Login from a known VPN/proxy/hosting IP (optional) | T1090 |
| `credential_stuffing` | One IP/device trying many accounts in a short window | T1110.004 |

Every rule is isolated (a single rule crash can never break ingestion or the
remaining rules) and every rule maps to a real technique row.

## Security & Hardening

Applied out of the box, no extra config needed:

- **Rate limiting** — per-IP sliding windows on `/auth/login`, `/auth/register`,
  `/sites`, and `/ingest/log`, so brute force and ingestion spam get throttled
  (HTTP 429).
- **JWT auth with bcrypt** — passwords hashed with bcrypt (72-byte safe),
  tokens signed with `JWT_SECRET`, admin vs. analyst roles enforced on the
  backend, never just in the UI.
- **Per-user data scoping** — analysts see only BinduParakh's self-monitoring
  activity plus their own registered sites; they are read-only (no site
  registration, no alert resolution). Admins see everything.
- **API-key hygiene** — ingest keys are shown exactly once at creation, never
  in `GET /sites`, and analyst accounts never see other organisations' sites.
- **Security headers** — `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, strict `Referrer-Policy`, safe `Permissions-Policy`
  on every response.
- **Fail-safe defaults** — email/SMTP and VPN-intelligence keys are optional;
  the app runs perfectly without them and logs instead of crashing. Startup
  also logs a loud warning when running with well-known fallback credentials.
- **Docker hygiene** — `.dockerignore` keeps `*.env` and build artifacts out of
  image layers; docker-compose healthchecks order startup.
- **Health endpoints** — `/health` (liveness) and `/ready` (DB-aware
  readiness, HTTP 503 when the database is unreachable) for load balancers and
  container orchestrators.

## Architecture

```
Monitored app ──POST /ingest/log (X-API-Key)──► FastAPI backend ──► detection engine (5 rules)
                                                       │  ▲                    │
                                                       │  │ rate-limited       ▼
                                                       │  └── auth (bcrypt/JWT) PostgreSQL
                                                       ▼                           │
                                               security headers / /ready    new Alert rows
                                                                           (FK → Technique row)
                                                                                    │
                                                                     (if severity ≥ threshold)
                                                                                    ▼
                                                                            email notification
                                                                          (per-site contact)

React dashboard ◄──polls /events, /alerts every 5s─────────────────────────┘
(radar UI · LIVE/OFFLINE indicator · live threat news ticker · ATT&CK hub wheel)
```

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, bcrypt + JWT auth
- **Frontend:** React + Vite
- **Detection:** pure Python, unit-tested (`backend/tests/`, 21 tests)
- **Notifications:** SMTP, fails gracefully if unconfigured
- **External data:** MITRE ATT&CK (bundled) + The Hacker News RSS (live, cached)

```
binduparakh/
├── backend/           # FastAPI app: auth, detection engine, ATT&CK data, email
│   ├── app/
│   │   ├── detection.py       # 5 original detection rules + MITRE mapping
│   │   ├── routers/            # auth, events, alerts, attack, news, sites, ingest
│   │   ├── data/attack_data.json  # real MITRE ATT&CK Enterprise dataset
│   │   └── rate_limit.py      # dependency-free sliding-window limiter
│   └── tests/                 # 21 unit tests (no DB or network needed)
├── frontend/          # React + Vite SOC-style dashboard
├── demo-site/         # Standalone Flask app #1 (multi-site proof)
├── demo-site-2/       # Standalone Flask app #2 (multi-site proof)
├── seed_demo.py       # Fires sample events for a populated dashboard
└── docker-compose.yml
```

## Setup

Requires Docker + Docker Compose.

```bash
git clone https://github.com/Sumit-2706/BinduParakh-Security-Event-Monitoring.git
cd binduparakh
cp backend/.env.example backend/.env
```

Open `backend/.env` and set `ADMIN_EMAIL` / `ADMIN_PASSWORD` to your own login —
this account is auto-created on startup. Optionally set `GUEST_EMAIL` /
`GUEST_PASSWORD` for a public read-only demo login.

```bash
docker compose up --build
```

- Dashboard: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/ready

For a populated dashboard instead of an empty one:

```bash
python seed_demo.py
```

`seed_demo.py` logs in as the same admin you configured, registers a demo site
and feeds sample events through the **real** `POST /ingest/log` API-key path —
the exact production integration route a real monitored website would use.

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

**21 unit tests** covering the detection engine's pure logic, the MITRE
dataset integrity, the RSS parser (including namespace-robustness), rate-limit
behaviour, and the email notification module (mocked SMTP). No database or
internet access needed. The full HTTP flow can be exercised with
`python smoke_sites.py` (self-monitoring + multi-site) or `seed_demo.py`.

## Configuration

All tunables live in `backend/.env`. See `backend/.env.example` for the full
list; highlights:

| Variable | Purpose |
|---|---|
| `JWT_SECRET` | Signing key for auth tokens (must be overridden publicly) |
| `ALLOW_REGISTRATION` | `true` lets strangers create analyst accounts; set `false` on public deployments |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Auto-created admin account on startup |
| `GUEST_EMAIL` / `GUEST_PASSWORD` | Optional public read-only demo login (role `analyst`) |
| `FAILED_LOGIN_THRESHOLD` / `FAILED_LOGIN_WINDOW_MIN` | Brute-force rule tuning |
| `IMPOSSIBLE_TRAVEL_MAX_KMH` | Max plausible travel speed for geo rule |
| `MULTI_ACCOUNT_THRESHOLD` / `MULTI_ACCOUNT_WINDOW_MIN` | Credential-stuffing rule tuning |
| `IPQUALITYSCORE_API_KEY` | Optional VPN/proxy intelligence (rule is skipped when blank) |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | Email alerts (app still works when blank) |
| `ALERT_EMAIL_TO` / `ALERT_EMAIL_MIN_SEVERITY` | Global recipient + severity gate |
| `FRONTEND_URL` | Your deployed frontend URL, for CORS |

## Deployment

The React frontend can be hosted on static hosts (e.g. Vercel); the backend
(FastAPI + PostgreSQL) needs a long-lived process host such as Railway, Render,
or Fly.io.

1. **Backend** — deploy with a managed Postgres add-on. Set `ADMIN_EMAIL`,
   `ADMIN_PASSWORD`, `JWT_SECRET`, `FRONTEND_URL` (your Vercel URL, for CORS),
   and optionally `GUEST_EMAIL`/`GUEST_PASSWORD` for a public read-only demo
   login. Healthchecks: use `/ready`.
2. **Frontend** — deploy to Vercel with `VITE_API_URL` pointing at the backend.

## Known limitations

- Live updates use polling (5s), not WebSockets.
- `Base.metadata.create_all()` is used instead of Alembic migrations.
- VPN/proxy detection needs a free third-party API key and is skipped if
  unconfigured.
- JWT tokens are stored in `localStorage` for simplicity; a production system
  could move them to `httpOnly` cookies. Never put non-demo credentials in a
  publicly deployed instance.
- Rate limits are tracked per-process; multi-worker deployments behind a load
  balancer should swap `rate_limit.py` for a shared store (Redis) — the
  interface stays the same.

## License

MIT