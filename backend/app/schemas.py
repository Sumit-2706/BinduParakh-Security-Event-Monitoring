"""Pydantic schemas — define the shape of data going in and out of the API."""
import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ---- Auth ----

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Events ----

class EventIn(BaseModel):
    event_type: str = Field(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=64)
    identity: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=64)
    user_agent: Optional[str] = Field(default=None, max_length=512)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    raw_payload: Optional[str] = Field(default=None, max_length=20000)


class EventOut(BaseModel):
    id: str
    event_type: str
    site_id: Optional[str]
    identity: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---- Monitored Sites ----

class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_email: EmailStr


class SiteOut(BaseModel):
    """A monitored site as seen by any logged-in user -- deliberately does
    NOT include the api_key, so analyst accounts can't harvest ingestion
    keys for sites they don't own."""
    id: str
    name: str
    contact_email: EmailStr
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class SiteAdminOut(SiteOut):
    """Like SiteOut but with the api_key -- returned ONLY to the admin who
    just created the site, so the key can be copied once."""
    api_key: str


# ---- Alerts ----

class TechniqueSummary(BaseModel):
    """Compact technique info embedded inside an alert response."""
    technique_id: str
    name: str
    tactics: list[str] = []

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: str
    event_id: str
    rule_name: str
    severity: str
    description: str
    resolved: bool
    created_at: datetime.datetime
    technique_id: Optional[str] = None
    technique: Optional[TechniqueSummary] = None

    class Config:
        from_attributes = True


# ---- MITRE ATT&CK ----

class TacticOut(BaseModel):
    shortname: str
    name: str
    description: Optional[str]

    class Config:
        from_attributes = True


class TechniqueOut(BaseModel):
    technique_id: str
    name: str
    description: Optional[str]
    detection: Optional[str]
    is_subtechnique: bool
    platforms: list[str] = []
    tactics: list[str] = []
    mitigations: list[str] = []

    class Config:
        from_attributes = True
