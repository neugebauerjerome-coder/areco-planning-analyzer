from pathlib import Path

from areco_planning.core.config import load_rules
from areco_planning.core.rules_engine import classify_intervention


ROOT = Path(__file__).resolve().parents[1]
RULES = load_rules(ROOT / "areco_planning/config/rules_v4.json")


def test_lists_are_fixed():
    assert RULES["nap"] == ["BWI", "CLS", "DKA", "HMO", "JLN", "RMO", "SEL"]
    assert "CRO" not in RULES["grands_itinerants"]
    assert RULES["contronics"]["client_prefix"] == "B"


def test_classification():
    assert classify_intervention("05 DEP") == "Dépannage"
    assert classify_intervention("04 M2B") == "Maintenance"
    assert classify_intervention("06 INST") == "Installation"
    assert classify_intervention("02 AUDIT") == "Audit"
