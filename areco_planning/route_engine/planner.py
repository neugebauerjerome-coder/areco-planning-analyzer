from __future__ import annotations

import math
from collections.abc import Iterable

from .models import Coordinates, RoutePoint


def haversine_km(a: Coordinates, b: Coordinates) -> float:
    lon1, lat1 = map(math.radians, [a.longitude, a.latitude])
    lon2, lat2 = map(math.radians, [b.longitude, b.latitude])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def nearest_neighbor_order(start: RoutePoint, stops: Iterable[RoutePoint]) -> list[RoutePoint]:
    remaining = list(stops)
    ordered: list[RoutePoint] = []
    current = start

    while remaining:
        next_point = min(
            remaining,
            key=lambda candidate: haversine_km(current.coordinates, candidate.coordinates),
        )
        ordered.append(next_point)
        remaining.remove(next_point)
        current = next_point

    return ordered
