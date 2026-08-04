from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .cache import RouteCache
from .models import RoutePoint, RouteSummary
from .ors_client import OpenRouteServiceClient
from .planner import nearest_neighbor_order


class RouteProvider(Protocol):
    def geocode(self, address: str): ...
    def route(self, points): ...


class RouteService:
    def __init__(self, provider: RouteProvider):
        self.provider = provider

    def build_route(
        self,
        start_address: str,
        stop_addresses: list[str],
        return_address: str | None = None,
        optimize_order: bool = True,
    ) -> RouteSummary:
        start = RoutePoint(start_address, self.provider.geocode(start_address))
        stops = [RoutePoint(address, self.provider.geocode(address)) for address in stop_addresses]
        if optimize_order:
            stops = nearest_neighbor_order(start, stops)

        points = [start, *stops]
        if return_address:
            points.append(RoutePoint(return_address, self.provider.geocode(return_address)))
        return self.provider.route(points)


def build_ors_route_service(api_key: str, cache_path: Path) -> tuple[RouteService, RouteCache]:
    cache = RouteCache(cache_path)
    client = OpenRouteServiceClient(api_key=api_key, cache=cache)
    return RouteService(client), cache
