"""
Loads MITRE's real Enterprise ATT&CK data (app/data/attack_data.json,
generated from MITRE's own published STIX dataset -- see
scripts/refresh_attack_data.py for how it was produced) into the
database.

Idempotent: running this repeatedly upserts rows rather than duplicating
them, so it's safe to call on every app startup.
"""
import json
import logging
import os

from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger("binduparakh.attack_loader")

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "attack_data.json")


def load_attack_data(db: Session) -> None:
    if not os.path.exists(DATA_PATH):
        logger.warning("ATT&CK data file not found at %s -- skipping import.", DATA_PATH)
        return

    with open(DATA_PATH) as f:
        data = json.load(f)

    # Skip re-importing if already populated -- keeps startup fast after
    # the first run instead of re-upserting ~700 rows every restart.
    existing_count = db.query(models.Technique).count()
    if existing_count >= len(data["techniques"]):
        logger.info("ATT&CK data already loaded (%d techniques) -- skipping.", existing_count)
        return

    for t in data["tactics"]:
        tactic = db.get(models.Tactic, t["shortname"])
        if tactic is None:
            tactic = models.Tactic(shortname=t["shortname"])
            db.add(tactic)
        tactic.name = t["name"]
        tactic.description = t["description"]

    for t in data["techniques"]:
        technique = db.get(models.Technique, t["technique_id"])
        if technique is None:
            technique = models.Technique(technique_id=t["technique_id"])
            db.add(technique)
        technique.name = t["name"]
        technique.description = t["description"]
        technique.detection = t["detection"]
        technique.is_subtechnique = t["is_subtechnique"]
        technique.platforms = t["platforms"]
        technique.tactics = t["tactics"]
        technique.mitigations = t["mitigations"]

    db.commit()
    logger.info(
        "Loaded %d tactics and %d techniques from MITRE ATT&CK.",
        len(data["tactics"]), len(data["techniques"]),
    )
