"""
Per-user data visibility helpers.

Analyst accounts are read-only observers: they may inspect BinduParakh's
own self-monitoring activity (site_id IS NULL) plus events/alerts for
sites they own -- not every monitored organisation's data. Admins see
everything.
"""
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models


def owned_site_ids(db: Session, user: models.User) -> Optional[List[str]]:
    """Site UUIDs the user may see, or None if the user is an admin
    (which means: no filtering, they see everything)."""
    if user.role == "admin":
        return None
    return [
        row[0]
        for row in db.query(models.Site.id)
        .filter(models.Site.owner_user_id == user.id)
        .all()
    ]


def site_visibility_filter(owned_ids: List[str]):
    """SQLAlchemy filter expression for events/alerts rows: self-monitoring
    activity (site_id NULL) plus the caller's own sites. Meant to be used
    with a non-admin user (owned_ids is a list; empty list = only
    self-monitoring activity)."""
    site_id = models.Event.site_id
    if owned_ids:
        return or_(site_id.is_(None), site_id.in_(owned_ids))
    return site_id.is_(None)