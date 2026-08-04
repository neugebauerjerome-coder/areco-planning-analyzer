from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class Technician:
    code: str
    name: str
    team: str = ""
    location: str = ""
    function: str = ""
    skills: str = ""
    is_nap: bool = False
    is_grand_itinerant: bool = False
    excluded: bool = False


@dataclass
class PlanningIssue:
    severity: str
    category: str
    message: str
    technician: str = ""
    intervention_number: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PlanningDataset:
    analysis_dates: list[date]
    interventions: Any
    technicians: dict[str, Technician]
    issues: list[PlanningIssue]
    metadata: dict[str, Any]
