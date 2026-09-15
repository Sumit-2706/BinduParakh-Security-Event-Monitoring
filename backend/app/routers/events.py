from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, detection
from app.notifications import send_alert_email

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/log", response_model=schemas.EventOut)
def log_event(
    payload: schemas.EventIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Ingests a single security-relevant event (e.g. a login attempt from a
    monitored application), then immediately runs the detection engine
    against it. In production this endpoint would typically be called by
    an application's own backend/middleware, authenticated with a
    per-organization API key -- for this project scope, dashboard-user
    JWT auth is used to keep the moving parts learnable.
    """
    event = models.Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)

    new_alerts = detection.run_all_rules(db, event)
    for alert in new_alerts:
        send_alert_email(alert.rule_name, alert.severity, alert.description)

    return event


@router.get("", response_model=List[schemas.EventOut])
def list_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Event)
        .order_by(models.Event.created_at.desc())
        .limit(limit)
        .all()
    )
