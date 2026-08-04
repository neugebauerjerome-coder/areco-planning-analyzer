from __future__ import annotations

import pandas as pd

from .models import PlanningIssue


def validate_dataset(frame: pd.DataFrame, mapping: dict) -> list[PlanningIssue]:
    issues: list[PlanningIssue] = []

    if frame.empty:
        issues.append(
            PlanningIssue(
                severity="HIGH",
                category="EMPTY_DATASET",
                message="Aucune intervention après lecture et nettoyage.",
            )
        )
        return issues

    missing_technicians = int(frame[mapping["technician"]].isna().sum())
    if missing_technicians:
        issues.append(
            PlanningIssue(
                severity="HIGH",
                category="MISSING_TECHNICIAN",
                message=f"{missing_technicians} intervention(s) sans technicien.",
            )
        )

    invalid_duration = pd.to_numeric(frame[mapping["duration"]], errors="coerce").isna().sum()
    if invalid_duration:
        issues.append(
            PlanningIssue(
                severity="MEDIUM",
                category="INVALID_DURATION",
                message=f"{int(invalid_duration)} durée(s) non numériques.",
            )
        )

    return issues
