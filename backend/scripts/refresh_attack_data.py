"""
refresh_attack_data.py

Regenerates backend/app/data/attack_data.json from MITRE's own published
Enterprise ATT&CK dataset. Run this occasionally to pick up new/updated
techniques as MITRE releases them -- the ATT&CK matrix is versioned and
updated a few times a year.

Source: https://github.com/mitre-attack/attack-stix-data (official MITRE
repository, STIX 2.1 format).

Usage:
    python scripts/refresh_attack_data.py
"""
import json
import os
import urllib.request

SOURCE_URL = (
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/"
    "master/enterprise-attack/enterprise-attack.json"
)

TACTIC_ORDER = [
    "reconnaissance", "resource-development", "initial-access", "execution",
    "persistence", "privilege-escalation", "defense-impairment", "stealth",
    "credential-access", "discovery", "lateral-movement", "collection",
    "command-and-control", "exfiltration", "impact",
]

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "attack_data.json")


def main():
    print(f"Downloading MITRE ATT&CK Enterprise dataset from {SOURCE_URL} ...")
    with urllib.request.urlopen(SOURCE_URL, timeout=120) as resp:
        stix_bundle = json.loads(resp.read())

    objects = stix_bundle["objects"]

    tactics = []
    for o in objects:
        if o.get("type") == "x-mitre-tactic":
            tactics.append({
                "shortname": o.get("x_mitre_shortname"),
                "name": o.get("name"),
                "description": (o.get("description") or "")[:400],
            })
    tactics.sort(key=lambda t: TACTIC_ORDER.index(t["shortname"]) if t["shortname"] in TACTIC_ORDER else 999)

    coa_names = {o["id"]: o.get("name") for o in objects if o.get("type") == "course-of-action"}
    technique_mitigations = {}
    for o in objects:
        if o.get("type") == "relationship" and o.get("relationship_type") == "mitigates":
            src, tgt = o.get("source_ref"), o.get("target_ref")
            if src in coa_names:
                technique_mitigations.setdefault(tgt, []).append(coa_names[src])

    techniques = []
    for o in objects:
        if o.get("type") != "attack-pattern":
            continue
        if o.get("revoked") or o.get("x_mitre_deprecated"):
            continue

        external_id = next(
            (r["external_id"] for r in o.get("external_references", [])
             if r.get("source_name") == "mitre-attack"),
            None,
        )
        if not external_id:
            continue

        tactic_shortnames = [
            kc["phase_name"] for kc in o.get("kill_chain_phases", [])
            if kc.get("kill_chain_name") == "mitre-attack"
        ]

        techniques.append({
            "technique_id": external_id,
            "name": o.get("name"),
            "description": (o.get("description") or "").strip().split("\n\n")[0].replace("\n", " ").strip()[:600],
            "detection": (o.get("x_mitre_detection") or "")[:500],
            "is_subtechnique": o.get("x_mitre_is_subtechnique", False),
            "platforms": o.get("x_mitre_platforms", []),
            "tactics": tactic_shortnames,
            "mitigations": sorted(set(technique_mitigations.get(o["id"], [])))[:5],
        })

    techniques.sort(key=lambda t: t["technique_id"])

    with open(OUTPUT_PATH, "w") as f:
        json.dump({"tactics": tactics, "techniques": techniques}, f, indent=1)

    print(f"Wrote {len(tactics)} tactics and {len(techniques)} techniques to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
