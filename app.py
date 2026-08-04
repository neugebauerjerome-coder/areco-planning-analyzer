from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from areco_planning.analyzer.service import analyze_with_routes, analyses_to_frames
from areco_planning.core.service import build_dataset
from areco_planning.reports.service import export_all_reports
from areco_planning.route_engine.cache import RouteCache
from areco_planning.route_engine.ors_client import OpenRouteServiceClient


APP_DIR = Path(__file__).resolve().parent
TEAMS_PATH = APP_DIR / "areco_planning" / "data" / "toutes_les_equipes_areco.xlsx"
RULES_PATH = APP_DIR / "areco_planning" / "config" / "rules_v4.json"

st.set_page_config(
    page_title="ARECO Planning Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .areco-header {
        background: linear-gradient(90deg,#17365D,#1F4E78);
        padding: 22px 26px;
        border-radius: 12px;
        color: white;
        margin-bottom: 18px;
      }
      .areco-header h1 {margin:0;font-size:30px;}
      .areco-header p {margin:7px 0 0 0;opacity:.9;}
      div[data-testid="stMetric"] {
        background:#F6F9FC;
        border:1px solid #D9E5F1;
        padding:14px;
        border-radius:10px;
      }
      .small-note {color:#5D6D7E;font-size:0.9rem;}
    </style>
    <div class="areco-header">
      <h1>ARECO Planning Suite Online V5.1</h1>
      <p>Analyse ARFITEC, trajets OpenRouteService, alertes métier et rapports.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Paramètres")

    secret_key = ""
    try:
        secret_key = st.secrets.get("ORS_API_KEY", "")
    except Exception:
        pass

    api_key = secret_key or os.getenv("ORS_API_KEY", "")
    if api_key:
        st.success("Clé OpenRouteService configurée")
    else:
        api_key = st.text_input("Clé OpenRouteService", type="password")

    optimize_order = st.checkbox("Optimiser l’ordre des magasins", value=True)
    st.divider()
    st.caption("LAL : Almeida-Martins Lucas — 09200 Saint-Girons")
    st.caption("Contronics : numéro client commençant par B")

uploaded = st.file_uploader(
    "Déposez le planning Excel ARFITEC",
    type=["xlsx"],
    accept_multiple_files=False,
)

analyse = st.button(
    "ANALYSER LE PLANNING",
    type="primary",
    use_container_width=True,
    disabled=uploaded is None,
)

if analyse:
    if not api_key:
        st.error("La clé OpenRouteService n’est pas configurée.")
        st.stop()

    with tempfile.TemporaryDirectory(prefix="areco_v51_") as temp_name:
        temp_dir = Path(temp_name)
        planning_path = temp_dir / uploaded.name
        planning_path.write_bytes(uploaded.getvalue())
        reports_dir = temp_dir / "reports"
        cache = None

        try:
            with st.status("Analyse en cours…", expanded=True) as status:
                st.write("Lecture du planning ARFITEC")
                dataset = build_dataset(planning_path, TEAMS_PATH, RULES_PATH)

                st.write("Calcul des trajets routiers")
                cache = RouteCache(temp_dir / "route_cache.sqlite")
                provider = OpenRouteServiceClient(api_key, cache)
                analyses, summary = analyze_with_routes(
                    planning_path,
                    TEAMS_PATH,
                    RULES_PATH,
                    provider,
                    optimize_order=optimize_order,
                )

                st.write("Génération des rapports")
                reports = export_all_reports(
                    reports_dir,
                    analyses,
                    summary,
                    dataset,
                    RULES_PATH,
                )
                daily, legs = analyses_to_frames(analyses)

                st.session_state["summary"] = summary
                st.session_state["daily"] = daily
                st.session_state["legs"] = legs
                st.session_state["issues"] = pd.DataFrame([
                    {
                        "Priorité": i.severity,
                        "Catégorie": i.category,
                        "Technicien": i.technician,
                        "Intervention": i.intervention_number,
                        "Message": i.message,
                    }
                    for i in dataset.issues
                ])
                st.session_state["excel"] = reports["excel"].read_bytes()
                st.session_state["pdf"] = reports["pdf"].read_bytes()
                st.session_state["mail"] = reports["mail"].read_text(encoding="utf-8")

                status.update(label="Analyse terminée", state="complete", expanded=False)

        except Exception as exc:
            st.exception(exc)
        finally:
            if cache is not None:
                cache.close()

if "summary" in st.session_state:
    summary = st.session_state["summary"]
    daily = st.session_state["daily"]
    legs = st.session_state["legs"]
    issues = st.session_state["issues"]

    tabs = st.tabs(["📊 Synthèse", "👷 Techniciens", "🚗 Trajets", "🚨 Alertes", "📄 Rapports"])

    with tabs[0]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", summary["interventions"])
        c2.metric("Techniciens actifs", summary["technicians_active"])
        c3.metric("Temps d’intervention", f'{summary["intervention_hours"]:.2f} h')
        c4.metric("Temps de trajet", f'{summary["travel_hours"]:.2f} h')

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Total", f'{summary["total_hours"]:.2f} h')
        c6.metric("Distance", f'{summary["distance_km"]:.1f} km')
        c7.metric("NAP < 7 h 30", len(summary["nap_under_7_5"]))
        c8.metric("Journées > 10 h", len(summary["over_10_hours"]))

        if summary["over_10_hours"]:
            st.error("Surcharge : " + ", ".join(summary["over_10_hours"]))
        if summary["nap_under_7_5"]:
            st.warning("NAP sous 7 h 30 : " + ", ".join(summary["nap_under_7_5"]))

        chart_data = daily[["Technicien", "Heures intervention", "Heures trajet"]].copy()
        chart_data = chart_data.groupby("Technicien", as_index=False).sum().set_index("Technicien")
        st.subheader("Charge par technicien")
        st.bar_chart(chart_data)

    with tabs[1]:
        st.subheader("Analyse détaillée")
        status_filter = st.multiselect(
            "Filtrer les statuts",
            options=sorted(daily["Statut"].unique()),
            default=sorted(daily["Statut"].unique()),
        )
        view = daily[daily["Statut"].isin(status_filter)].copy()
        st.dataframe(view, use_container_width=True, hide_index=True)

        technician = st.selectbox("Voir un technicien", sorted(daily["Technicien"].unique()))
        tech_data = daily[daily["Technicien"] == technician]
        st.dataframe(tech_data, use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Détail des segments routiers")
        tech_filter = st.multiselect(
            "Techniciens",
            options=sorted(legs["Technicien"].unique()),
            default=sorted(legs["Technicien"].unique()),
        )
        st.dataframe(
            legs[legs["Technicien"].isin(tech_filter)],
            use_container_width=True,
            hide_index=True,
        )

    with tabs[3]:
        st.subheader("Alertes métier")
        if issues.empty:
            st.success("Aucune alerte métier")
        else:
            priority = st.multiselect(
                "Priorité",
                options=sorted(issues["Priorité"].unique()),
                default=sorted(issues["Priorité"].unique()),
            )
            st.dataframe(
                issues[issues["Priorité"].isin(priority)],
                use_container_width=True,
                hide_index=True,
            )

    with tabs[4]:
        d1, d2, d3 = st.columns(3)
        d1.download_button(
            "Télécharger Excel",
            data=st.session_state["excel"],
            file_name="ARECO_Planning_Analyse.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        d2.download_button(
            "Télécharger PDF",
            data=st.session_state["pdf"],
            file_name="ARECO_Planning_Analyse.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        d3.download_button(
            "Télécharger le mail",
            data=st.session_state["mail"],
            file_name="ARECO_Planning_Mail.txt",
            mime="text/plain",
            use_container_width=True,
        )
        with st.expander("Afficher le mail"):
            st.code(st.session_state["mail"], language=None)
