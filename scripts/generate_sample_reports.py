from pathlib import Path
from areco_planning.analyzer.service import analyze_with_routes
from areco_planning.core.service import build_dataset
from areco_planning.reports.service import export_all_reports
from areco_planning.route_engine.models import Coordinates, RouteLeg, RouteSummary
ROOT=Path(__file__).resolve().parents[1]
class OfflineDemoProvider:
    def __init__(self): self.coordinates={}
    def geocode(self,address):
        if address not in self.coordinates:
            i=len(self.coordinates)+1; self.coordinates[address]=Coordinates(2.0+i*0.01,48.0+i*0.01)
        return self.coordinates[address]
    def route(self,points):
        points=list(points); legs=[RouteLeg(a.label,b.label,14.0,0.28) for a,b in zip(points,points[1:])]
        return RouteSummary(points,legs,14.0*len(legs),0.28*len(legs))
planning=ROOT/"samples/planning_test_04-08-2026.xlsx"; teams=ROOT/"areco_planning/data/toutes_les_equipes_areco.xlsx"; rules=ROOT/"areco_planning/config/rules_v4.json"
analyses,summary=analyze_with_routes(planning,teams,rules,OfflineDemoProvider(),True)
dataset=build_dataset(planning,teams,rules)
print(export_all_reports(ROOT/"sample_reports",analyses,summary,dataset,rules))
