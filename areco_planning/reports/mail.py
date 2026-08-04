from __future__ import annotations
from typing import Any

def build_summary_mail(summary: dict[str, Any], analysis_date: str) -> str:
    over = ", ".join(summary.get("over_10_hours", [])) or "aucun"
    nap = ", ".join(summary.get("nap_under_7_5", [])) or "aucun"
    return (
        f"Objet : Contrôle V4 du planning du {analysis_date}\n\n"
        "Bonjour,\n\n"
        f"Le planning comprend {summary['interventions']} interventions pour "
        f"{summary['technicians_active']} techniciens actifs.\n\n"
        f"Temps d'intervention : {summary['intervention_hours']:.2f} h\n"
        f"Temps de trajet : {summary['travel_hours']:.2f} h\n"
        f"Total intervention + trajet : {summary['total_hours']:.2f} h\n"
        f"Distance totale : {summary['distance_km']:.1f} km\n\n"
        f"Journées supérieures à 10 h : {over}\n"
        f"NAP sous 7 h 30 : {nap}\n"
        f"Alertes métier : {summary['core_issues']}\n\n"
        "Les détails figurent dans les rapports Excel et PDF joints.\n\n"
        "Cordialement,\nJérôme Neugebauer\nSupport Client - ARECO"
    )
