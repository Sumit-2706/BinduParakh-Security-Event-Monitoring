"""
Manage the list of external websites/applications BinduParakh is
monitoring. Each site gets a unique API key (for their backend to send
events with) and a contact email (so THEIR alerts go to THEM, not one
shared inbox).

Key safety: the api_key is returned ONLY by POST /sites to the admin who
just created it (so it can be copied once). GET /sites never includes
keys, and analysts never see the list of other organisations' sites.
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth
from app.rate_limit import rate_limit
from app.scoping import owned_site_ids

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=schemas.SiteAdminOut)
def create_site(
    payload: schemas.SiteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
    _: None = Depends(rate_limit(max_hits=10, window_seconds=60)),
):
    site = models.Site(
        name=payload.name,
        contact_email=payload.contact_email,
        owner_user_id=current_user.id,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("", response_model=List[schemas.SiteOut])
def list_sites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Site).order_by(models.Site.created_at.desc())

    # Analysts only see the sites they own; admins see all.
    owned = owned_site_ids(db, current_user)
    if owned is not None:
        query = query.filter(models.Site.id.in_(owned))

    return query.all()