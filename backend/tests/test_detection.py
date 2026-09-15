"""
Unit tests for the detection engine's pure, DB-independent logic.

These run with zero external dependencies (no Postgres needed) -- just
`pip install -r requirements.txt` and `pytest`. This is deliberate: fast,
dependency-free tests are what you actually run on every save while
developing; slower end-to-end tests against a real database belong in a
separate integration-test pass (see README's "Testing" section for how
to run those against the docker-compose stack).
"""
import math

from app.detection import _haversine_km, RULE_TO_MITRE, ALL_RULES


def test_haversine_known_distance():
    # Delhi (28.6139, 77.2090) to Mumbai (19.0760, 72.8777) is ~1150 km
    dist = _haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
    assert 1100 < dist < 1200


def test_haversine_zero_distance_for_same_point():
    dist = _haversine_km(10.0, 20.0, 10.0, 20.0)
    assert math.isclose(dist, 0.0, abs_tol=1e-6)


def test_every_rule_has_a_mitre_mapping():
    """Every rule function's name must have a corresponding MITRE ATT&CK
    tag, otherwise alerts would silently show 'Unmapped'."""
    rule_names = {rule_fn.__name__.replace("rule_", "") for rule_fn in ALL_RULES}
    mapped_names = set(RULE_TO_MITRE.keys())
    assert rule_names == mapped_names, (
        f"Rules missing a MITRE mapping: {rule_names - mapped_names}"
    )


def test_mitre_tags_look_like_real_technique_ids():
    for tag in RULE_TO_MITRE.values():
        assert tag.startswith("T"), f"'{tag}' doesn't look like a MITRE technique ID"
