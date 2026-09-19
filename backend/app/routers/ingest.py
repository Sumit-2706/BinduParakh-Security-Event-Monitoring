"""
The endpoint an EXTERNAL website's backend calls to report activity to
BinduParakh -- authenticated by that site's API key (see /sites), not a
dashboard login. This is what makes BinduParakh "pluggable" into any
other application: add a few lines of code to your login handler that
POST here, and BinduParakh's detection engine + MITRE tagging + email
alerting all apply to YOUR site automatically.
"""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth, detection
from app.notifications import send_alert_email
from app.rate_limit import rate_limit

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/log", response_model=schemas.EventOut)
def ingest_event(
    payload: schemas.EventIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    site: models.Site = Depends(auth.get_current_site),
    _: None = Depends(rate_limit(max_hits=120, window_seconds=60)),
):
    event = models.Event(**payload.model_dump(), site_id=site.id)
    db.add(event)
    db.commit()
    db.refresh(event)

    new_alerts = detection.run_all_rules(db, event)
    for alert in new_alerts:
        # Route the email to THIS site's contact -- not a shared inbox --
        # so the team that owns the affected website is the one notified.
        # Sent in the background so a slow SMTP server can't make the
        # monitored app's request block.
        background_tasks.add_task(
            send_alert_email,
            alert.rule_name,
            alert.severity,
            alert.description,
            recipient=site.contact_email,
        )

    return event