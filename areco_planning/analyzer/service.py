from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import pandas as pd

from areco_planning.core.service import build_dataset
from areco_planning.route_engine.models import RoutePoint
from areco_planning.route_engine.planner import nearest_neighbor_order
from .addressing import intervention_address, technician_home_address
from .models import DailyTechnicianAnalysis

class AnalyzerError(RuntimeError):
    pass

def _status(total_hours: float, is_nap: bool, rules: dict[str, Any]) -> str:
    if total_hours > float(rules["thresholds"]["maximum_daily_hours"]):
        return "RED_OVERLOAD"
    if is_nap and total_hours < float(rules["thresholds"]["nap_minimum_daily_hours"]):
        return "RED_NAP_UNDERLOAD"
    if total_hours < float(rules["thresholds"]["nap_minimum_daily_hours"]):
        return "YELLOW_UNDERLOAD"
    return "GREEN_OK"

def analyze_with_routes(planning_path: Path, teams_path: Path, rules_path: Path, route_provider, optimize_order: bool = True):
    dataset = build_dataset(planning_path, teams_path, rules_path)
    frame = dataset.interventions.copy()
    mapping = dataset.metadata["column_mapping"]
    rules = json.loads(rules_path.read_text(encoding="utf-8"))

    analyses = []
    previous_gi_stop = {}
    dates = sorted(frame[mapping["date"]].dt.date.unique())
    first_date, last_date = dates[0], dates[-1]

    for (tech_code, day), group in frame.groupby(["_technician_code", frame[mapping["date"]].dt.date], sort=True):
        technician = dataset.technicians.get(tech_code)
        if technician is None:
            continue

        home_address = technician_home_address(technician.location)
        if not home_address:
            raise AnalyzerError(f"Domicile introuvable pour {tech_code}.")

        if technician.is_grand_itinerant and tech_code in previous_gi_stop and day != first_date:
            start_point = previous_gi_stop[tech_code]
        else:
            start_point = RoutePoint(home_address, route_provider.geocode(home_address))

        unique_addresses = []
        seen = set()
        for _, row in group.iterrows():
            address = intervention_address(row, mapping)
            if address and address not in seen:
                seen.add(address)
                unique_addresses.append(address)

        stops = [RoutePoint(address, route_provider.geocode(address)) for address in unique_addresses]
        ordered_stops = nearest_neighbor_order(start_point, stops) if optimize_order else stops
        route_points = [start_point, *ordered_stops]

        must_return_home = (not technician.is_grand_itinerant) or day == last_date
        if must_return_home:
            route_points.append(RoutePoint(home_address, route_provider.geocode(home_address)))

        route_summary = route_provider.route(route_points)

        if technician.is_grand_itinerant and ordered_stops:
            previous_gi_stop[tech_code] = ordered_stops[-1]

        intervention_hours = float(group["_duration_v3"].sum())
        travel_hours = float(route_summary.duration_hours)
        total_hours = intervention_hours + travel_hours

        analyses.append(DailyTechnicianAnalysis(
            technician=tech_code,
            technician_name=technician.name,
            day=day,
            intervention_count=len(group),
            intervention_hours=round(intervention_hours, 2),
            travel_hours=round(travel_hours, 2),
            total_hours=round(total_hours, 2),
            distance_km=round(float(route_summary.distance_km), 2),
            nap=technician.is_nap,
            grand_itinerant=technician.is_grand_itinerant,
            status=_status(total_hours, technician.is_nap, rules),
            route_points=[point.label for point in route_summary.points],
            route_legs=[{
                "origin": leg.origin,
                "destination": leg.destination,
                "distance_km": leg.distance_km,
                "duration_hours": leg.duration_hours,
            } for leg in route_summary.legs],
        ))

    summary = {
        "analysis_dates": [str(value) for value in dates],
        "interventions": int(len(frame)),
        "technicians_active": int(frame["_technician_code"].nunique()),
        "intervention_hours": round(sum(x.intervention_hours for x in analyses), 2),
        "travel_hours": round(sum(x.travel_hours for x in analyses), 2),
        "total_hours": round(sum(x.total_hours for x in analyses), 2),
        "distance_km": round(sum(x.distance_km for x in analyses), 2),
        "nap_under_7_5": [x.technician for x in analyses if x.status == "RED_NAP_UNDERLOAD"],
        "over_10_hours": [x.technician for x in analyses if x.status == "RED_OVERLOAD"],
        "core_issues": len(dataset.issues),
        "core_issues_by_category": {},
    }
    for issue in dataset.issues:
        summary["core_issues_by_category"][issue.category] = summary["core_issues_by_category"].get(issue.category, 0) + 1
    return analyses, summary

def analyses_to_frames(analyses):
    daily_rows, leg_rows = [], []
    for item in analyses:
        daily_rows.append({
            "Technicien": item.technician,
            "Nom": item.technician_name,
            "Date": item.day,
            "Interventions": item.intervention_count,
            "Heures intervention": item.intervention_hours,
            "Heures trajet": item.travel_hours,
            "Total journée": item.total_hours,
            "Distance km": item.distance_km,
            "NAP": "Oui" if item.nap else "Non",
            "Grand itinérant": "Oui" if item.grand_itinerant else "Non",
            "Statut": item.status,
            "Ordre des sites": " → ".join(item.route_points),
        })
        for leg in item.route_legs:
            leg_rows.append({
                "Technicien": item.technician,
                "Date": item.day,
                "Départ": leg["origin"],
                "Arrivée": leg["destination"],
                "Distance km": leg["distance_km"],
                "Temps trajet h": leg["duration_hours"],
            })
    return pd.DataFrame(daily_rows), pd.DataFrame(leg_rows)
