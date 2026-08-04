from pathlib import Path
from areco_planning.analyzer.service import analyze_with_routes
from areco_planning.core.service import build_dataset
from areco_planning.reports.service import export_all_reports
from areco_planning.route_engine.models import Coordinates, RouteLeg, RouteSummary
ROOT=Path(__file__).resolve().parents[1]
class FakeRouteProvider:
    def __init__(self): self.index={}
    def geocode(self,address):
        if address not in self.index:
            i=len(self.index)+1; self.index[address]=Coordinates(2.0+i*0.01,48.0+i*0.01)
        return self.index[address]
    def route(self,points):
        points=list(points); legs=[RouteLeg(a.label,b.label,15.0,0.30) for a,b in zip(points,points[1:])]
        return RouteSummary(points,legs,15.0*len(legs),0.30*len(legs))
def test_reports_are_created(tmp_path):
    planning=ROOT/"samples/planning_test_04-08-2026.xlsx"; teams=ROOT/"areco_planning/data/toutes_les_equipes_areco.xlsx"; rules=ROOT/"areco_planning/config/rules_v4.json"
    analyses,summary=analyze_with_routes(planning,teams,rules,FakeRouteProvider(),True)
    dataset=build_dataset(planning,teams,rules)
    outputs=export_all_reports(tmp_path,analyses,summary,dataset,rules)
    assert outputs["excel"].exists() and outputs["excel"].stat().st_size>10000
    assert outputs["pdf"].exists() and outputs["pdf"].stat().st_size>5000
    assert outputs["mail"].exists() and "Objet :" in outputs["mail_text"]
