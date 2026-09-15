"""
BinduParakh -- main FastAPI application entrypoint.

Creates the database tables on startup (fine for a student/portfolio
project; a production system would use Alembic migrations instead),
imports the real MITRE ATT&CK dataset into the database, and wires up
the auth/events/alerts/attack routers behind CORS so the React dashboard
can call it from a different origin during local development.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import Base, engine, SessionLocal
from app.routers import auth, events, alerts, attack, news, sites, ingest
from app.attack_loader import load_attack_data
from app import models, auth as auth_module

Base.metadata.create_all(bind=engine)

# Import MITRE's real ATT&CK matrix (14 tactics, ~700 techniques) into the
# database on startup. Idempotent -- safe to run on every restart.
with SessionLocal() as _db:
    load_attack_data(_db)


def _ensure_admin_account() -> None:
    """Guarantees a known admin account always exists on startup, so the
    dashboard is usable immediately without relying on "the first person
    to register becomes admin" (which is easy to accidentally break by
    registering twice). Idempotent: if the account already exists, its
    role is corrected to admin but its password is left untouched so a
    manually-changed password isn't silently reset on every restart.

    IMPORTANT if you deploy this publicly (Vercel/Railway/Render/etc.):
    override ADMIN_EMAIL and ADMIN_PASSWORD via your hosting platform's
    environment-variable settings rather than relying on the fallback
    values below. Those fallbacks are convenient for local development
    but are visible to anyone who can read this source file, so they
    must NOT be the real credentials on a public deployment."""
    # Generic, safe-to-publish placeholders. Real deployments MUST override
    # both via .env / hosting-platform environment variables -- see
    # README.md "Configuration" and "Deploying publicly" sections. These
    # fallbacks intentionally are NOT real credentials, because this
    # source file is meant to be pushed to a public GitHub repo.
    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "change-this-password")

    with SessionLocal() as _db:
        existing = _db.query(models.User).filter(models.User.email == admin_email).first()
        if existing is None:
            _db.add(models.User(
                email=admin_email,
                hashed_password=auth_module.hash_password(admin_password),
                role="admin",
            ))
            _db.commit()
        elif existing.role != "admin":
            existing.role = "admin"
            _db.commit()


def _ensure_guest_account() -> None:
    """Seeds a fixed, publicly-shareable read-only demo login (role
    "analyst" -- can view Alerts/Events/ATT&CK matrix/Threat news, but
    cannot register sites or reach anything admin-only). Meant to be
    published alongside a live demo link (e.g. in a LinkedIn post or
    README) so visitors can log in immediately without registering an
    account or being handed the real admin password. Safe to publish
    because an analyst account has no destructive or sensitive
    capabilities -- worst case a stranger resolves a demo alert."""
    guest_email = os.getenv("GUEST_EMAIL", "guest@binduparakh.demo")
    guest_password = os.getenv("GUEST_PASSWORD", "guest1234")

    with SessionLocal() as _db:
        existing = _db.query(models.User).filter(models.User.email == guest_email).first()
        if existing is None:
            _db.add(models.User(
                email=guest_email,
                hashed_password=auth_module.hash_password(guest_password),
                role="analyst",
            ))
            _db.commit()


_ensure_admin_account()
_ensure_guest_account()

app = FastAPI(
    title="BinduParakh API",
    description=(
        "A security event monitoring and threat-detection API with a "
        "full, real MITRE ATT&CK Enterprise matrix built in."
    ),
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    # Wildcard "*" is invalid when allow_credentials=True (browsers block it),
    # so list explicit origins the frontend can run on. Local dev origins
    # are always allowed; add your deployed frontend's real URL via the
    # FRONTEND_URL env var when hosting this publicly (e.g. on Vercel) --
    # otherwise the deployed dashboard's requests will be blocked by CORS
    # exactly like the local one was before this origin was added.
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        *(
            [os.getenv("FRONTEND_URL")]
            if os.getenv("FRONTEND_URL")
            else []
        ),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(alerts.router)
app.include_router(attack.router)
app.include_router(news.router)
app.include_router(sites.router)
app.include_router(ingest.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
