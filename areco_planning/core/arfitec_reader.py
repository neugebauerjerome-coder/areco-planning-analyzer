from __future__ import annotations

from pathlib import Path
from typing import Iterable
import pandas as pd


class ArfitecReadError(RuntimeError):
    pass


COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "number": ("N°", "No", "Numéro"),
    "date": ("Date d'intervention", "Date intervention"),
    "status": ("Statut planning", "Statut"),
    "type": ("Type Intervention", "Type d'intervention"),
    "site": ("Nom", "Client", "Magasin"),
    "description": ("Désignation", "Description"),
    "technician": ("Ressource intervention", "Ressource", "Technicien"),
    "duration": ("Durée de l intervention", "Durée de l'intervention", "Durée"),
    "client_number": ("N° client", "Numéro client"),
    "address": ("Adresse",),
    "address2": ("Adresse 2",),
    "postal_code": ("Code postal",),
    "city": ("Ville",),
    "country": ("Code pays/région", "Pays"),
}


def _resolve_column(columns: Iterable[str], aliases: tuple[str, ...], required: bool = False) -> str | None:
    normalized = {str(col).strip().casefold(): str(col) for col in columns}
    for alias in aliases:
        found = normalized.get(alias.casefold())
        if found:
            return found
    if required:
        raise ArfitecReadError(f"Colonne obligatoire absente. Noms acceptés : {', '.join(aliases)}")
    return None


def read_arfitec(path: Path) -> tuple[pd.DataFrame, dict[str, str | None]]:
    if not path.exists():
        raise ArfitecReadError(f"Fichier ARFITEC introuvable : {path}")

    try:
        excel = pd.ExcelFile(path)
    except Exception as exc:
        raise ArfitecReadError(f"Impossible d'ouvrir le classeur : {exc}") from exc

    sheet = "Commandes service" if "Commandes service" in excel.sheet_names else excel.sheet_names[0]
    frame = pd.read_excel(path, sheet_name=sheet)
    if frame.empty:
        raise ArfitecReadError("Le classeur ne contient aucune ligne exploitable.")

    mapping = {
        key: _resolve_column(
            frame.columns,
            aliases,
            required=key in {"number", "date", "type", "site", "technician", "duration"},
        )
        for key, aliases in COLUMN_ALIASES.items()
    }

    number_col = mapping["number"]
    frame = frame[frame[number_col].notna()].copy()
    frame[mapping["date"]] = pd.to_datetime(frame[mapping["date"]], errors="coerce")
    invalid_dates = int(frame[mapping["date"]].isna().sum())
    frame = frame[frame[mapping["date"]].notna()].copy()

    if frame.empty:
        raise ArfitecReadError("Aucune intervention avec une date valide.")

    frame["_source_sheet"] = sheet
    frame["_invalid_date_count"] = invalid_dates
    return frame, mapping
