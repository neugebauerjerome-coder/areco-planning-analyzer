from __future__ import annotations
from pathlib import Path
from typing import Any
import json
import pandas as pd
from areco_planning.analyzer.service import analyses_to_frames

def export_excel_report(output_path: Path, analyses, summary: dict[str, Any], dataset, rules: dict[str, Any], mail_text: str) -> None:
    daily, legs = analyses_to_frames(analyses)
    issues = pd.DataFrame([{
        "Priorité": issue.severity,
        "Catégorie": issue.category,
        "Technicien": issue.technician,
        "Intervention": issue.intervention_number,
        "Message": issue.message,
    } for issue in dataset.issues])
    tables = {
        "Analyse techniciens": daily,
        "NAP": daily[daily["NAP"] == "Oui"].copy(),
        "Grands itinérants": daily[daily["Grand itinérant"] == "Oui"].copy(),
        "Détail trajets": legs,
        "Alertes": issues,
        "Détail interventions": dataset.interventions,
    }
    with pd.ExcelWriter(output_path, engine="xlsxwriter", datetime_format="dd/mm/yyyy") as writer:
        workbook = writer.book
        title = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#1F4E78", "font_size": 14, "align": "center"})
        header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#4472C4", "border": 1, "align": "center"})
        wrap = workbook.add_format({"text_wrap": True, "valign": "top"})
        red = workbook.add_format({"bg_color": "#F4CCCC", "font_color": "#9C0006"})
        orange = workbook.add_format({"bg_color": "#FCE5CD", "font_color": "#7F6000"})
        green = workbook.add_format({"bg_color": "#D9EAD3", "font_color": "#274E13"})

        dashboard = pd.DataFrame([
            ["Interventions", summary["interventions"], "Techniciens actifs", summary["technicians_active"]],
            ["Heures intervention", summary["intervention_hours"], "Heures trajet", summary["travel_hours"]],
            ["Total heures", summary["total_hours"], "Distance km", summary["distance_km"]],
            ["NAP < 7 h 30", len(summary["nap_under_7_5"]), "Journées > 10 h", len(summary["over_10_hours"])],
            ["Alertes métier", summary["core_issues"], "Version", "4.0.4"],
        ], columns=["Indicateur", "Valeur", "Indicateur 2", "Valeur 2"])
        dashboard.to_excel(writer, sheet_name="Tableau de bord", startrow=3, index=False)
        ws = writer.sheets["Tableau de bord"]
        ws.merge_range("A1:D1", "ARECO PLANNING SUITE V4.0.4 - RAPPORT", title)
        for c, name in enumerate(dashboard.columns):
            ws.write(3, c, name, header)
        ws.set_column("A:A", 26); ws.set_column("B:B", 18); ws.set_column("C:C", 26); ws.set_column("D:D", 18)
        chart = workbook.add_chart({"type": "column"})
        chart.add_series({"name": "Indicateurs", "categories": ["Tableau de bord", 4, 0, 6, 0], "values": ["Tableau de bord", 4, 1, 6, 1]})
        chart.set_title({"name": "Indicateurs principaux"}); chart.set_legend({"none": True}); chart.set_style(10)
        ws.insert_chart("F3", chart, {"x_scale": 1.25, "y_scale": 1.15})

        for sheet_name, frame in tables.items():
            frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
            sheet = writer.sheets[sheet_name[:31]]
            sheet.freeze_panes(1, 0)
            if len(frame.columns):
                sheet.autofilter(0, 0, max(len(frame), 1), len(frame.columns)-1)
            for c, col in enumerate(frame.columns):
                sheet.write(0, c, col, header)
                vals = frame[col].astype(str).head(250)
                width = min(max(len(str(col))+2, vals.map(len).max()+2 if not vals.empty else 12), 42)
                sheet.set_column(c, c, width)
            if sheet_name == "Analyse techniciens" and not frame.empty:
                sc = frame.columns.get_loc("Statut"); tc = frame.columns.get_loc("Total journée")
                sheet.conditional_format(1, sc, len(frame), sc, {"type": "text", "criteria": "containing", "value": "GREEN", "format": green})
                sheet.conditional_format(1, sc, len(frame), sc, {"type": "text", "criteria": "containing", "value": "YELLOW", "format": orange})
                sheet.conditional_format(1, sc, len(frame), sc, {"type": "text", "criteria": "containing", "value": "RED", "format": red})
                sheet.conditional_format(1, tc, len(frame), tc, {"type": "cell", "criteria": ">", "value": 10, "format": red})

        pd.DataFrame({"Mail prêt à envoyer": mail_text.splitlines()}).to_excel(writer, sheet_name="Mail accompagnement", index=False)
        m = writer.sheets["Mail accompagnement"]; m.write(0, 0, "Mail prêt à envoyer", header); m.set_column("A:A", 115, wrap)
        rf = pd.DataFrame([{"Règle": k, "Valeur": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v} for k, v in rules.items()])
        rf.to_excel(writer, sheet_name="Règles V4", index=False)
        r = writer.sheets["Règles V4"]; r.write(0,0,"Règle",header); r.write(0,1,"Valeur",header); r.set_column("A:A",34); r.set_column("B:B",85,wrap)
