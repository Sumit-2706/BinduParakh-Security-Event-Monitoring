"""
Detection engine.

Each rule is a small, independently-testable function that takes the
current event plus recent history from the DB, and returns an Alert (or
None if nothing suspicious was found). run_all_rules() is the single entry
point called after every event is ingested.

Every rule is mapped to a real MITRE ATT&CK technique so alerts carry
industry-standard context, not just a made-up label.
"""
import datetime
import logging
import math
from dataclasses import dataclass
from typing import Optional, List

import requests
from sqlalchemy.orm import Session

from app import models
from app.config import settings

logger = logging.getLogger("binduparakh.detection")

# --- MITRE ATT&CK mapping -------------------------------------------------
# Maps each rule to a real MITRE ATT&CK technique ID. The full technique
# name, description, detection guidance, and mitigations are NOT
# hardcoded here -- they're looked up from the `techniques` table, which
# is imported from MITRE's own published dataset (see attack_loader.py).
# This keeps a single source of truth: if MITRE renames or updates a
# technique, re-running the loader updates it everywhere automatically.
RULE_TO_MITRE = {
    "rapid_failed_logins": "T1110",
    "impossible_travel": "T1078",
    "suspicious_user_agent": "T1595",
    "vpn_proxy_login": "T1090",
    "credential_stuffing": "T1110.004",
}

KNOWN_SCANNER_SIGNATURES = [
    "nikto", "sqlmap", "masscan", "nmap", "gobuster", "dirbuster", "acunetix", "nessus",
]


@dataclass
class RuleResult:
    rule_name: str
    severity: str
    description: str


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance between two lat/lon points, in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# --- Individual rules -------------------------------------------------------

def rule_rapid_failed_logins(db: Session, event: models.Event) -> Optional[RuleResult]:
    """Flags a burst of failed logins for the same identity in a short window.

    Scoped to the same site as the event so one tenant's traffic can never
    trigger (or inflate) another tenant's alert."""
    if event.event_type != "login_failure" or not event.identity:
        return None

    window_start = datetime.datetime.utcnow() - datetime.timedelta(
        minutes=settings.FAILED_LOGIN_WINDOW_MIN
    )
    count = (
        db.query(models.Event)
        .filter(
            models.Event.event_type == "login_failure",
            models.Event.identity == event.identity,
            models.Event.site_id == event.site_id,
            models.Event.created_at >= window_start,
        )
        .count()
    )
    if count >= settings.FAILED_LOGIN_THRESHOLD:
        return RuleResult(
            rule_name="rapid_failed_logins",
            severity="high",
            description=(
                f"{count} failed login attempts for '{event.identity}' "
                f"in the last {settings.FAILED_LOGIN_WINDOW_MIN} minutes."
            ),
        )
    return None


def rule_impossible_travel(db: Session, event: models.Event) -> Optional[RuleResult]:
    """
    Flags two successful logins for the same identity that are geographically
    too far apart to have been done by the same person in the elapsed time.
    """
    if event.event_type != "login_success" or not event.identity:
        return None
    if event.latitude is None or event.longitude is None:
        return None

    prev = (
        db.query(models.Event)
        .filter(
            models.Event.event_type == "login_success",
            models.Event.identity == event.identity,
            models.Event.site_id == event.site_id,
            models.Event.id != event.id,
            models.Event.latitude.isnot(None),
            models.Event.longitude.isnot(None),
        )
        .order_by(models.Event.created_at.desc())
        .first()
    )
    if not prev:
        return None

    elapsed_hours = (event.created_at - prev.created_at).total_seconds() / 3600.0
    if elapsed_hours <= 0:
        return None

    distance_km = _haversine_km(prev.latitude, prev.longitude, event.latitude, event.longitude)
    required_speed_kmh = distance_km / elapsed_hours

    if required_speed_kmh > settings.IMPOSSIBLE_TRAVEL_MAX_KMH:
        return RuleResult(
            rule_name="impossible_travel",
            severity="critical",
            description=(
                f"'{event.identity}' logged in {distance_km:.0f} km apart within "
                f"{elapsed_hours:.2f} hours (implied speed {required_speed_kmh:.0f} km/h)."
            ),
        )
    return None


def rule_suspicious_user_agent(db: Session, event: models.Event) -> Optional[RuleResult]:
    """Flags requests carrying a known security-scanner user-agent string."""
    if not event.user_agent:
        return None
    ua_lower = event.user_agent.lower()
    for signature in KNOWN_SCANNER_SIGNATURES:
        if signature in ua_lower:
            return RuleResult(
                rule_name="suspicious_user_agent",
                severity="medium",
                description=f"Request from IP {event.ip_address} used scanner tool signature '{signature}'.",
            )
    return None


def rule_vpn_proxy_login(db: Session, event: models.Event) -> Optional[RuleResult]:
    """
    Flags a login originating from a known VPN/proxy/hosting IP.
    Uses IPQualityScore's free-tier API if a key is configured; otherwise
    this rule silently no-ops so the app still runs without the key.
    """
    if event.event_type not in ("login_success", "login_failure") or not event.ip_address:
        return None
    if not settings.IPQUALITYSCORE_API_KEY:
        return None

    try:
        resp = requests.get(
            f"https://ipqualityscore.com/api/json/ip/{settings.IPQUALITYSCORE_API_KEY}/{event.ip_address}",
            params={"strictness": 1},
            timeout=3,
        )
        data = resp.json()
    except Exception:
        return None  # network/API failure must never break event ingestion

    if data.get("proxy") or data.get("vpn") or data.get("tor"):
        return RuleResult(
            rule_name="vpn_proxy_login",
            severity="medium",
            description=f"Login for '{event.identity}' originated from a VPN/proxy IP ({event.ip_address}).",
        )
    return None


def rule_credential_stuffing(db: Session, event: models.Event) -> Optional[RuleResult]:
    """
    Flags a single device (IP + user-agent fingerprint) attempting logins
    against many different accounts in a short window -- classic
    credential-stuffing behavior, as opposed to one account being
    brute-forced (that's rule_rapid_failed_logins).
    """
    if event.event_type not in ("login_success", "login_failure"):
        return None
    if not event.ip_address or not event.user_agent:
        return None

    window_start = datetime.datetime.utcnow() - datetime.timedelta(
        minutes=settings.MULTI_ACCOUNT_WINDOW_MIN
    )
    distinct_identities = (
        db.query(models.Event.identity)
        .filter(
            models.Event.ip_address == event.ip_address,
            models.Event.user_agent == event.user_agent,
            models.Event.site_id == event.site_id,
            models.Event.created_at >= window_start,
            models.Event.identity.isnot(None),
        )
        .distinct()
        .count()
    )
    if distinct_identities >= settings.MULTI_ACCOUNT_THRESHOLD:
        return RuleResult(
            rule_name="credential_stuffing",
            severity="high",
            description=(
                f"Device at {event.ip_address} attempted logins against "
                f"{distinct_identities} different accounts within "
                f"{settings.MULTI_ACCOUNT_WINDOW_MIN} minutes."
            ),
        )
    return None


ALL_RULES = [
    rule_rapid_failed_logins,
    rule_impossible_travel,
    rule_suspicious_user_agent,
    rule_vpn_proxy_login,
    rule_credential_stuffing,
]


def run_all_rules(db: Session, event: models.Event) -> List[models.Alert]:
    """Runs every detection rule against a freshly-ingested event and
    persists any resulting alerts. Returns the list of new Alert rows.

    Each rule is wrapped in its own try/except so a single rule crashing
    (e.g. a surprise network error or data quirk) can never abort the
    remaining rules or fail the ingest request that triggered them."""
    new_alerts: List[models.Alert] = []
    for rule_fn in ALL_RULES:
        try:
            result = rule_fn(db, event)
        except Exception:  # noqa: BLE001 -- rule isolation, see docstring
            logger.exception("Detection rule '%s' failed on event %s", rule_fn.__name__, event.id)
            continue
        if result is None:
            continue
        technique_id = RULE_TO_MITRE.get(result.rule_name)
        alert = models.Alert(
            event_id=event.id,
            technique_id=technique_id,
            rule_name=result.rule_name,
            severity=result.severity,
            description=result.description,
        )
        db.add(alert)
        new_alerts.append(alert)
    if new_alerts:
        db.commit()
        for a in new_alerts:
            db.refresh(a)
    return new_alerts
