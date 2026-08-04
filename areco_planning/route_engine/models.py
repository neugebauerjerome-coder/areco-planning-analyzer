from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Coordinates:
    longitude: float
    latitude: float


@dataclass(frozen=True)
class RoutePoint:
    label: str
    coordinates: Coordinates


@dataclass(frozen=True)
class RouteLeg:
    origin: str
    destination: str
    distance_km: float
    duration_hours: float


@dataclass(frozen=True)
class RouteSummary:
    points: Sequence[RoutePoint]
    legs: Sequence[RouteLeg]
    distance_km: float
    duration_hours: float
