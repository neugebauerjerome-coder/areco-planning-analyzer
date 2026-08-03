from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from areco_engine import (
    AnalysisError,
    analyze_planning,
    create_v3_workbook,
    load_reference_teams,
)

APP_DIR = Path(__file__).resolve().parent
DEFAULT_TEAMS = APP_DIR / "data" / "equipes_areco.csv"
DEFAULT_RULES = APP_DIR / "data" / "regles_v3.json"

st.set_page_config(
    page_title="ARECO Planning Analyzer V3",
    page_icon="📊",
    layout="wide",
)

st.title("ARECO Planning Analyzer V3")
st.caption("Déposez l’export ARFITEC. L’application calcule les trajets OpenRouteService et génère le rapport V3.")

with st.sidebar:
    st.header("Paramètres")
    api_key = st.text_input(
        "Clé API OpenRouteService",
        value=(st.secrets.get("ORS_API_KEY", "") if hasattr(st, "secrets") else "") or os.getenv("ORS_API_KEY", ""),
        type="password",
        help="La clé reste dans la session du navigateur et n’est pas enregistrée dans le rapport.",
    )
    base_url = st.selectbox(
        "Serveur OpenRouteService",
        [
            "https://api.heigit.org",
            "https://api.openrouteservice.org",
        ],
        help="Utilisez api.heigit.org en priorité. L’ancien domaine reste proposé en secours.",
    )
    route_order = st.radio(
        "Ordre des interventions",
        ["Optimisé par proximité", "Ordre du fichier"],
        index=0,
    )
    st.info(
        "Régional : domicile → interventions → domicile.\n\n"
        "Grand itinérant : domicile le lundi, tournée continue, retour domicile le vendredi."
    )

planning_file = st.file_uploader("Planning ARFITEC (.xlsx)", type=["xlsx"])
teams_file = st.file_uploader(
    "Référentiel équipes (facultatif)",
    type=["xlsx", "csv"],
    help="Sans fichier, la base ARECO intégrée est utilisée.",
)

if planning_file:
    st.success(f"Fichier chargé : {planning_file.name}")

analyze = st.button("Analyser le planning", type="primary", disabled=planning_file is None)

if analyze:
    if not api_key:
        st.error("Saisissez la clé OpenRouteService dans la barre latérale.")
        st.stop()

    try:
        with st.status("Analyse en cours…", expanded=True) as status:
            st.write("Lecture du planning")
            planning_bytes = planning_file.getvalue()

            st.write("Chargement du référentiel ARECO")
            teams = load_reference_teams(
                uploaded_file=teams_file,
                default_csv_path=DEFAULT_TEAMS,
            )
            rules = json.loads(DEFAULT_RULES.read_text(encoding="utf-8"))

            st.write("Géocodage des domiciles et magasins")
            st.write("Calcul des itinéraires routiers par technicien et par jour")
            result = analyze_planning(
                planning_bytes=planning_bytes,
                teams=teams,
                rules=rules,
                api_key=api_key,
                base_url=base_url,
                optimize_order=route_order.startswith("Optimisé"),
            )

            st.write("Génération du classeur V3")
            report_bytes = create_v3_workbook(result)
            status.update(label="Analyse terminée", state="complete", expanded=False)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Interventions", result.summary["interventions"])
        k2.metric("Techniciens actifs", result.summary["techniciens_actifs"])
        k3.metric("Heures intervention", f'{result.summary["heures_intervention"]:.2f} h')
        k4.metric("Temps de trajet", f'{result.summary["heures_trajet"]:.2f} h')
        k5.metric("Total", f'{result.summary["heures_total"]:.2f} h')

        st.subheader("Alertes prioritaires")
        if result.alerts.empty:
            st.success("Aucune alerte détectée.")
        else:
            st.dataframe(result.alerts, use_container_width=True, hide_index=True)

        st.subheader("Charge par technicien")
        st.dataframe(
            result.technician_summary,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Télécharger le rapport V3",
            data=report_bytes,
            file_name=f'ARECO_Planning_Analyzer_V3_{result.analysis_date:%Y-%m-%d}.xlsx',
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

        with st.expander("Mail d’accompagnement"):
            st.code(result.mail_text, language=None)

    except AnalysisError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.exception(exc)
