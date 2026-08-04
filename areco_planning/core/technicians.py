from __future__ import annotations

from pathlib import Path
import pandas as pd

from .models import Technician


class TechnicianRepositoryError(RuntimeError):
    pass


def load_technicians(path: Path, rules: dict) -> dict[str, Technician]:
    if not path.exists():
        raise TechnicianRepositoryError(f"Référentiel techniciens introuvable : {path}")

    excel = pd.ExcelFile(path)
    sheet = "Toutes les équipes" if "Toutes les équipes" in excel.sheet_names else excel.sheet_names[0]
    frame = pd.read_excel(path, sheet_name=sheet, dtype=str).fillna("")

    required = {"Code", "Nom"}
    missing = required - set(frame.columns)
    if missing:
        raise TechnicianRepositoryError(
            "Colonnes obligatoires absentes du référentiel : " + ", ".join(sorted(missing))
        )

    nap = set(rules["nap"])
    gi = set(rules["grands_itinerants"])
    excluded = set(rules["exclus"])

    result: dict[str, Technician] = {}
    for _, row in frame.iterrows():
        code = str(row.get("Code", "")).strip().upper()
        if not code:
            continue
        result[code] = Technician(
            code=code,
            name=str(row.get("Nom", "")).strip(),
            team=str(row.get("Équipe", "")).strip(),
            location=str(row.get("Localisation", "")).strip(),
            function=str(row.get("Fonction / spécialité", "")).strip(),
            skills=str(row.get("Compétences / pictogrammes", "")).strip(),
            is_nap=code in nap,
            is_grand_itinerant=code in gi,
            excluded=code in excluded,
        )
    return result
