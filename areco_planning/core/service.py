from __future__ import annotations

from pathlib import Path

from .arfitec_reader import read_arfitec
from .config import load_rules
from .models import PlanningDataset
from .rules_engine import apply_rules
from .technicians import load_technicians
from .validator import validate_dataset


def build_dataset(
    planning_path: Path,
    teams_path: Path,
    rules_path: Path,
) -> PlanningDataset:
    rules = load_rules(rules_path)
    technicians = load_technicians(teams_path, rules)
    frame, mapping = read_arfitec(planning_path)
    issues = validate_dataset(frame, mapping)
    enriched, rule_issues = apply_rules(frame, mapping, technicians, rules)
    issues.extend(rule_issues)

    dates = sorted(set(enriched[mapping["date"]].dt.date))
    metadata = {
        "source_file": str(planning_path),
        "source_sheet": enriched["_source_sheet"].iloc[0],
        "row_count": int(len(enriched)),
        "technician_count": int(enriched["_technician_code"].nunique()),
        "column_mapping": mapping,
        "rules_version": rules.get("version", ""),
        "route_engine_version": "4.0.2",
    }
    return PlanningDataset(
        analysis_dates=dates,
        interventions=enriched,
        technicians=technicians,
        issues=issues,
        metadata=metadata,
    )
