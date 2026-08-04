from __future__ import annotations

from typing import Iterable
import requests

from .cache import RouteCache
from .models import Coordinates, RouteLeg, RoutePoint, RouteSummary


class RouteEngineError(RuntimeError):
    pass


class OpenRouteServiceClient:
    GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
    ROUTE_URL = "https://api.openrouteservice.org/v2/directions/driving-car/json"

    def __init__(self, api_key: str, cache: RouteCache, timeout_seconds: int = 45):
        if not api_key.strip():
            raise RouteEngineError("Clé OpenRouteService manquante.")
        self.api_key = api_key.strip()
        self.cache = cache
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def geocode(self, address: str) -> Coordinates:
        cached = self.cache.get(address)
        if cached:
            return cached

        response = self.session.get(
            self.GEOCODE_URL,
            params={"api_key": self.api_key, "text": address, "size": 1},
            timeout=self.timeout_seconds,
        )
        if response.status_code == 429:
            raise RouteEngineError("Quota OpenRouteService dépassé.")
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            raise RouteEngineError(f"Adresse introuvable : {address}")

        longitude, latitude = features[0]["geometry"]["coordinates"][:2]
        coordinates = Coordinates(float(longitude), float(latitude))
        self.cache.put(address, coordinates)
        return coordinates

    def route(self, points: Iterable[RoutePoint]) -> RouteSummary:
        point_list = list(points)
        if len(point_list) < 2:
            return RouteSummary(
                points=point_list,
                legs=[],
                distance_km=0.0,
                duration_hours=0.0,
            )

        legs: list[RouteLeg] = []
        total_distance = 0.0
        total_duration = 0.0

        for origin, destination in zip(point_list, point_list[1:]):
            response = self.session.post(
                self.ROUTE_URL,
                headers={"Authorization": self.api_key, "Content-Type": "application/json"},
                json={
                    "coordinates": [
                        [origin.coordinates.longitude, origin.coordinates.latitude],
                        [destination.coordinates.longitude, destination.coordinates.latitude],
                    ],
                    "instructions": False,
                    "geometry": False,
                    "units": "km",
                },
                timeout=self.timeout_seconds,
            )
            if response.status_code == 429:
                raise RouteEngineError("Quota OpenRouteService dépassé.")
            response.raise_for_status()
            summary = response.json()["routes"][0]["summary"]
            distance = float(summary["distance"])
            if distance > 100000:
                distance /= 1000.0
            duration = float(summary["duration"]) / 3600.0
            legs.append(
                RouteLeg(
                    origin=origin.label,
                    destination=destination.label,
                    distance_km=round(distance, 2),
                    duration_hours=round(duration, 2),
                )
            )
            total_distance += distance
            total_duration += duration

        return RouteSummary(
            points=point_list,
            legs=legs,
            distance_km=round(total_distance, 2),
            duration_hours=round(total_duration, 2),
        )
