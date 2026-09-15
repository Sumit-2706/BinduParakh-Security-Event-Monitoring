"""Pydantic schemas — define the shape of data going in and out of the API."""
import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ---- Auth ----

class UserCreate(BaseModel):
    email: EmailStr
    password: str


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
    event_type: str
    identity: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    raw_payload: Optional[str] = None


class EventOut(BaseModel):
    id: str
    event_type: str
    identity: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---- Monitored Sites ----

class SiteCreate(BaseModel):
    name: str
    contact_email: EmailStr


class SiteOut(BaseModel):
    id: str
    name: str
    contact_email: EmailStr
    api_key: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


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
