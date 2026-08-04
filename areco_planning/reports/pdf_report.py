from __future__ import annotations
from pathlib import Path
from typing import Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def _label(status: str) -> str:
    return {"GREEN_OK":"Conforme","YELLOW_UNDERLOAD":"Sous 7 h 30","RED_NAP_UNDERLOAD":"NAP sous 7 h 30","RED_OVERLOAD":"Supérieur à 10 h"}.get(status,status)

def export_pdf_report(output_path: Path, analyses, summary: dict[str, Any], dataset, analysis_date: str) -> None:
    doc = SimpleDocTemplate(str(output_path), pagesize=landscape(A4), rightMargin=12*mm, leftMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ARECOTitle", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#1F4E78"), spaceAfter=10))
    styles.add(ParagraphStyle(name="ARECOSection", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#1F4E78"), spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(name="SmallText", parent=styles["BodyText"], fontSize=8, leading=10))
    story=[Paragraph(f"ARECO Planning Suite V4.0.4 - Contrôle du {analysis_date}", styles["ARECOTitle"]), Paragraph("Synthèse générale", styles["ARECOSection"])]
    sd=[["Indicateur","Valeur","Indicateur","Valeur"],
        ["Interventions",summary["interventions"],"Techniciens actifs",summary["technicians_active"]],
        ["Heures intervention",f'{summary["intervention_hours"]:.2f} h',"Heures trajet",f'{summary["travel_hours"]:.2f} h'],
        ["Total",f'{summary["total_hours"]:.2f} h',"Distance",f'{summary["distance_km"]:.1f} km'],
        ["NAP sous 7 h 30",len(summary["nap_under_7_5"]),"Journées > 10 h",len(summary["over_10_hours"])],
        ["Alertes métier",summary["core_issues"],"Version","4.0.4"]]
    t=Table(sd,colWidths=[48*mm,28*mm,48*mm,28*mm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4472C4")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#B7C9E2")),("BACKGROUND",(0,1),(-1,-1),colors.HexColor("#F4F8FC")),("FONTSIZE",(0,0),(-1,-1),9)]))
    story += [t, Spacer(1,8*mm), Paragraph("Analyse par technicien", styles["ARECOSection"])]
    data=[["Code","Nom","Interv.","Intervention","Trajet","Total","Km","NAP","GI","Statut"]]
    for x in analyses:
        data.append([x.technician,x.technician_name,x.intervention_count,f"{x.intervention_hours:.2f} h",f"{x.travel_hours:.2f} h",f"{x.total_hours:.2f} h",f"{x.distance_km:.1f}","Oui" if x.nap else "Non","Oui" if x.grand_itinerant else "Non",_label(x.status)])
    tt=Table(data,repeatRows=1,colWidths=[18*mm,36*mm,16*mm,23*mm,20*mm,20*mm,18*mm,14*mm,14*mm,28*mm])
    style=[("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4472C4")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#C6D4E1")),("FONTSIZE",(0,0),(-1,-1),7.5)]
    for i,x in enumerate(analyses,1):
        fill=colors.HexColor("#D9EAD3")
        if x.status.startswith("YELLOW"): fill=colors.HexColor("#FCE5CD")
        elif x.status.startswith("RED"): fill=colors.HexColor("#F4CCCC")
        style.append(("BACKGROUND",(9,i),(9,i),fill))
    tt.setStyle(TableStyle(style)); story.append(tt)
    story += [PageBreak(),Paragraph("Alertes métier",styles["ARECOSection"])]
    idata=[["Priorité","Catégorie","Technicien","Intervention","Message"]]
    for issue in dataset.issues:
        idata.append([issue.severity,issue.category,issue.technician,issue.intervention_number,Paragraph(issue.message,styles["SmallText"])])
    if len(idata)==1: idata.append(["-","-","-","-","Aucune alerte métier."])
    it=Table(idata,repeatRows=1,colWidths=[20*mm,34*mm,25*mm,28*mm,155*mm])
    it.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4472C4")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#C6D4E1")),("FONTSIZE",(0,0),(-1,-1),7.5),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(it); doc.build(story)
