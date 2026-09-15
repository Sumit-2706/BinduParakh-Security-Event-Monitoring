"""
Verifies the bundled MITRE ATT&CK dataset (app/data/attack_data.json) is
present, complete, and contains real-looking data -- not empty or
placeholder content. This guards against the seed file getting corrupted
or accidentally stripped in a future edit.
"""
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "attack_data.json")


def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def test_data_file_exists():
    assert os.path.exists(DATA_PATH)


def test_has_all_15_current_mitre_tactics():
    data = load_data()
    shortnames = {t["shortname"] for t in data["tactics"]}
    expected = {
        "reconnaissance", "resource-development", "initial-access", "execution",
        "persistence", "privilege-escalation", "defense-impairment", "stealth",
        "credential-access", "discovery", "lateral-movement", "collection",
        "command-and-control", "exfiltration", "impact",
    }
    assert shortnames == expected


def test_has_hundreds_of_real_techniques():
    data = load_data()
    assert len(data["techniques"]) > 600, "Expected the full ATT&CK matrix, not a trimmed subset"


def test_known_technique_ids_present_with_real_names():
    data = load_data()
    by_id = {t["technique_id"]: t for t in data["techniques"]}
    known = {
        "T1110": "Brute Force",
        "T1566": "Phishing",
        "T1059": "Command and Scripting Interpreter",
        "T1078": "Valid Accounts",
    }
    for tid, expected_name in known.items():
        assert tid in by_id, f"{tid} missing from dataset"
        assert by_id[tid]["name"] == expected_name

def test_techniques_have_nonempty_descriptions():
    data = load_data()
    empty = [t["technique_id"] for t in data["techniques"] if not t["description"] or len(t["description"]) < 20]
    assert len(empty) == 0, f"Techniques with suspiciously short/empty descriptions: {empty[:10]}"
