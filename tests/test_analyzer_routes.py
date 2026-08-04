from pathlib import Path
from areco_planning.analyzer.service import analyze_with_routes, analyses_to_frames
from areco_planning.route_engine.models import Coordinates, RouteLeg, RouteSummary

ROOT = Path(__file__).resolve().parents[1]

class FakeRouteProvider:
    def __init__(self):
        self.index = {}
    def geocode(self, address):
        if address not in self.index:
            i = len(self.index) + 1
            self.index[address] = Coordinates(2.0 + i*0.01, 48.0 + i*0.01)
        return self.index[address]
    def route(self, points):
        points = list(points)
        legs = [RouteLeg(a.label, b.label, 12.0, 0.25) for a, b in zip(points, points[1:])]
        return RouteSummary(points, legs, 12.0*len(legs), 0.25*len(legs))

def test_real_planning_with_fake_routes():
    analyses, summary = analyze_with_routes(
        ROOT / "samples/planning_test_04-08-2026.xlsx",
        ROOT / "areco_planning/data/toutes_les_equipes_areco.xlsx",
        ROOT / "areco_planning/config/rules_v4.json",
        FakeRouteProvider(),
        True,
    )
    assert summary["interventions"] == 49
    assert summary["technicians_active"] == 23
    assert summary["travel_hours"] > 0
    daily, legs = analyses_to_frames(analyses)
    assert not daily.empty
    assert not legs.empty
    assert "Heures trajet" in daily.columns
