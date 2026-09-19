from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.scoping import owned_site_ids, site_visibility_filter

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=List[schemas.EventOut])
def list_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Event).order_by(models.Event.created_at.desc())

    # Analysts see only self-monitoring activity + their own sites;
    # admins see everything. Site scoping also means one monitored
    # organisation's events can't be enumerated by another's analyst.
    owned = owned_site_ids(db, current_user)
    if owned is not None:
        query = query.filter(site_visibility_filter(owned))

    return query.limit(limit).all()