from __future__ import annotations

import io
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests


class AnalysisError(RuntimeError):
    pass


@dataclass
class AnalysisResult:
    analysis_date: date
    summary: dict[str, Any]
    technician_summary: pd.DataFrame
    nap: pd.DataFrame
    itinerants: pd.DataFrame
    daily_routes: pd.DataFrame
    route_legs: pd.DataFrame
    installations: pd.DataFrame
    depannages: pd.DataFrame
    maintenances: pd.DataFrame
    contronics: pd.DataFrame
    alerts: pd.DataFrame
    interventions: pd.DataFrame
    mail_text: str
    rules: dict[str, Any]


def load_reference_teams(uploaded_file, default_csv_path: Path) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.read_csv(default_csv_path, dtype=str).fillna("")

    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(data), dtype=str).fillna("")

    xls = pd.ExcelFile(io.BytesIO(data))
    sheet = "Toutes les équipes" if "Toutes les équipes" in xls.sheet_names else xls.sheet_names[0]
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet, dtype=str).fillna("")


def _read_planning(planning_bytes: bytes) -> pd.DataFrame:
    try:
        xls = pd.ExcelFile(io.BytesIO(planning_bytes))
    except Exception as exc:
        raise AnalysisError(f"Impossible de lire le fichier Excel : {exc}") from exc

    sheet = "Commandes service" if "Commandes service" in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(io.BytesIO(planning_bytes), sheet_name=sheet)
    if df.empty:
        raise AnalysisError("Le planning est vide.")

    required = {"Date d'intervention", "Ressource intervention", "Nom"}
    missing = required - set(df.columns)
    if missing:
        raise AnalysisError("Colonnes obligatoires absentes : " + ", ".join(sorted(missing)))

    df = df[df["N°"].notna()].copy() if "N°" in df.columns else df.copy()
    df["Date d'intervention"] = pd.to_datetime(df["Date d'intervention"], errors="coerce")
    df = df[df["Date d'intervention"].notna()].copy()
    if df.empty:
        raise AnalysisError("Aucune date d’intervention exploitable.")

    return df


def _text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()
