"""
Endpoints for browsing the full, real MITRE ATT&CK Enterprise matrix that's
loaded into the database -- 15 tactics and 700+ techniques/sub-techniques,
each with MITRE's own description, detection guidance, and mitigations.
This backs the frontend's ATT&CK Matrix page.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

router = APIRouter(prefix="/attack", tags=["mitre-attack"])


@router.get("/tactics", response_model=List[schemas.TacticOut])
def list_tactics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Returns all 15 MITRE ATT&CK Enterprise tactics, in kill-chain order."""
    return db.query(models.Tactic).all()


@router.get("/techniques", response_model=List[schemas.TechniqueOut])
def list_techniques(
    tactic: Optional[str] = Query(None, description="Filter by tactic shortname, e.g. 'credential-access'"),
    search: Optional[str] = Query(None, description="Case-insensitive search over technique name"),
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Browse/search the full technique matrix. Used to power the ATT&CK
    Matrix page and to let an analyst manually look up a technique while
    investigating an alert.
    """
    query = db.query(models.Technique)
    if search:
        query = query.filter(models.Technique.name.ilike(f"%{search}%"))
    results = query.order_by(models.Technique.technique_id).limit(limit if not tactic else 5000).all()

    if tactic:
        results = [t for t in results if t.tactics and tactic in t.tactics][:limit]

    return results


@router.get("/techniques/{technique_id}", response_model=schemas.TechniqueOut)
def get_technique(
    technique_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    technique = db.get(models.Technique, technique_id)
    if not technique:
        raise HTTPException(status_code=404, detail="Technique not found")
    return technique


@router.get("/stats")
def attack_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Quick counts for a dashboard summary widget."""
    return {
        "total_tactics": db.query(models.Tactic).count(),
        "total_techniques": db.query(models.Technique).filter(models.Technique.is_subtechnique == False).count(),
        "total_subtechniques": db.query(models.Technique).filter(models.Technique.is_subtechnique == True).count(),
        "techniques_actively_detected": len(set(
            r[0] for r in db.query(models.Alert.technique_id).filter(models.Alert.technique_id.isnot(None)).distinct()
        )),
    }
