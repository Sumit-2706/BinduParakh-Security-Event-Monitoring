"""
Manage the list of external websites/applications BinduParakh is
monitoring. Each site gets a unique API key (for their backend to send
events with) and a contact email (so THEIR alerts go to THEM, not one
shared inbox).
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=schemas.SiteOut)
def create_site(
    payload: schemas.SiteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_admin),
):
    site = models.Site(name=payload.name, contact_email=payload.contact_email)
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("", response_model=List[schemas.SiteOut])
def list_sites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return db.query(models.Site).order_by(models.Site.created_at.desc()).all()
