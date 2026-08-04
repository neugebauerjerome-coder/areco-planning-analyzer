from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any

@dataclass
class DailyTechnicianAnalysis:
    technician: str
    technician_name: str
    day: date
    intervention_count: int
    intervention_hours: float
    travel_hours: float
    total_hours: float
    distance_km: float
    nap: bool
    grand_itinerant: bool
    status: str
    route_points: list[str]
    route_legs: list[dict[str, Any]]
