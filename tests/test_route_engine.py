from pathlib import Path

from areco_planning.route_engine.cache import RouteCache
from areco_planning.route_engine.models import Coordinates, RouteLeg, RoutePoint, RouteSummary
from areco_planning.route_engine.planner import nearest_neighbor_order
from areco_planning.route_engine.service import RouteService


class FakeProvider:
    def __init__(self):
        self.coordinates = {
            "Domicile": Coordinates(2.0, 48.0),
            "Magasin A": Coordinates(2.1, 48.0),
            "Magasin B": Coordinates(3.0, 48.0),
        }

    def geocode(self, address):
        return self.coordinates[address]

    def route(self, points):
        points = list(points)
        legs = []
        for a, b in zip(points, points[1:]):
            legs.append(RouteLeg(a.label, b.label, 10.0, 0.25))
        return RouteSummary(points, legs, 10.0 * len(legs), 0.25 * len(legs))


def test_cache_roundtrip(tmp_path: Path):
    cache = RouteCache(tmp_path / "cache.sqlite")
    cache.put("1 rue Test, Paris", Coordinates(2.35, 48.85))
    assert cache.get("  1 RUE test,   paris ") == Coordinates(2.35, 48.85)
    cache.close()


def test_nearest_neighbor():
    start = RoutePoint("Domicile", Coordinates(2.0, 48.0))
    a = RoutePoint("A", Coordinates(2.1, 48.0))
    b = RoutePoint("B", Coordinates(3.0, 48.0))
    assert [p.label for p in nearest_neighbor_order(start, [b, a])] == ["A", "B"]


def test_route_service_with_return():
    service = RouteService(FakeProvider())
    result = service.build_route(
        start_address="Domicile",
        stop_addresses=["Magasin B", "Magasin A"],
        return_address="Domicile",
        optimize_order=True,
    )
    assert [p.label for p in result.points] == ["Domicile", "Magasin A", "Magasin B", "Domicile"]
    assert result.distance_km == 30.0
    assert result.duration_hours == 0.75
