"""
Database models for BinduParakh.

Core tables:
- User: who can log into the dashboard
- Event: a raw security-relevant event ingested from a monitored app
  (e.g. a login attempt, an HTTP request)
- Alert: something the detection engine decided was suspicious enough
  to surface to an analyst
- Tactic / Technique: the real MITRE ATT&CK Enterprise matrix, imported
  from MITRE's own published dataset (see app/attack_loader.py). Alerts
  link to a real Technique row instead of a free-text label, so every
  alert carries genuine, verifiable ATT&CK context.
"""
import datetime
import uuid

from sqlalchemy import Column, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="analyst")  # admin | analyst
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Tactic(Base):
    """One of the 15 MITRE ATT&CK Enterprise tactics (Reconnaissance,
    Execution, Persistence, ...). Sourced directly from MITRE's published
    STIX data, not hand-typed."""
    __tablename__ = "tactics"

    shortname = Column(String, primary_key=True)  # e.g. "credential-access"
    name = Column(String, nullable=False)          # e.g. "Credential Access"
    description = Column(Text, nullable=True)


class Technique(Base):
    """A single MITRE ATT&CK technique or sub-technique (e.g. T1110,
    T1110.004), imported verbatim from MITRE's Enterprise ATT&CK dataset."""
    __tablename__ = "techniques"

    technique_id = Column(String, primary_key=True)  # e.g. "T1110" or "T1110.004"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    detection = Column(Text, nullable=True)
    is_subtechnique = Column(Boolean, default=False)
    platforms = Column(JSON, nullable=True)     # list[str]
    tactics = Column(JSON, nullable=True)       # list[str] of tactic shortnames
    mitigations = Column(JSON, nullable=True)   # list[str] of mitigation names

    alerts = relationship("Alert", back_populates="technique")


class Site(Base):
    """A website/application being monitored. Each site gets its own API
    key (for that site's backend to send events with, no dashboard login
    needed) and its own contact email (so alerts for THAT site go to the
    team that actually owns it, not a single global inbox).

    owner_user_id ties a site to the admin account that registered it, so
    analyst accounts only ever see events/alerts for the sites they own
    (plus BinduParakh's own self-monitoring activity)."""
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False, default=lambda: uuid.uuid4().hex)
    owner_user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    events = relationship("Event", back_populates="site")


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    site_id = Column(UUID(as_uuid=False), ForeignKey("sites.id"), nullable=True)
    event_type = Column(String, index=True, nullable=False)  # e.g. login_failure
    identity = Column(String, index=True, nullable=True)     # e.g. an email/username
    ip_address = Column(String, index=True, nullable=True)
    user_agent = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    raw_payload = Column(Text, nullable=True)  # JSON string of anything extra
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    alerts = relationship("Alert", back_populates="event")
    site = relationship("Site", back_populates="events")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    event_id = Column(UUID(as_uuid=False), ForeignKey("events.id"), nullable=False)
    technique_id = Column(String, ForeignKey("techniques.technique_id"), nullable=True)
    rule_name = Column(String, index=True, nullable=False)
    severity = Column(String, index=True, nullable=False)  # low | medium | high | critical
    description = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    event = relationship("Event", back_populates="alerts")
    technique = relationship("Technique", back_populates="alerts")
