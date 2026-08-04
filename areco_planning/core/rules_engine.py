from __future__ import annotations

import re
from typing import Any
import pandas as pd

from .models import PlanningIssue, Technician


def _text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _number(value: Any) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def classify_intervention(intervention_type: Any) -> str:
    value = _text(intervention_type).upper()
    if "INST" in value or value.startswith(("06 ", "1INSTAL", "36 FIN INST", "41 RECUP NUIT", "16 M+DEMONT")):
        return "Installation"
    if "DEP" in value:
        return "Dépannage"
    if re.search(r"\bM[1234]B?\b", value) or value.startswith(("04 ", "12 ", "22 ", "24 ", "29 ", "30 ", "31 ")):
        return "Maintenance"
    if value.startswith("02 "):
        return "Audit"
    if value.startswith("11 "):
        return "Bureau"
    if value.startswith("43 "):
        return "Trajet"
    if value.startswith("44 "):
        return "Nuitée"
    return "Autre"


def calculate_v3_duration(row: pd.Series, same_day: pd.DataFrame, mapping: dict, rules: dict) -> float:
    type_value = _text(row.get(mapping["type"])).upper()
    site = _text(row.get(mapping["site"])).upper()
    description = _text(row.get(mapping.get("description"))).upper() if mapping.get("description") else ""

    if type_value.startswith(("43 TRAJET", "44 NUITEE")):
        return 0.0
    if "HMY" in site or "HMY" in description:
        return float(rules["durations"]["hmy"])
    if "ZUMMO" in site or "ZUMMO" in description:
        return float(rules["durations"]["zummo"])
    if type_value.startswith("11 BUREAU"):
        type_col = mapping["type"]
        operational = same_day[
            ~same_day[type_col].fillna("").astype(str).str.upper().str.startswith(
                ("11 BUREAU", "43 TRAJET", "44 NUITEE")
            )
        ]
        return float(
            rules["durations"]["bureau_avec_interventions"]
            if not operational.empty
            else rules["durations"]["bureau_seul"]
        )
    return _number(row.get(mapping["duration"]))


def apply_rules(
    frame: pd.DataFrame,
    mapping: dict,
    technicians: dict[str, Technician],
    rules: dict,
) -> tuple[pd.DataFrame, list[PlanningIssue]]:
    result = frame.copy()
    issues: list[PlanningIssue] = []

    tech_col = mapping["technician"]
    date_col = mapping["date"]
    type_col = mapping["type"]
    client_col = mapping.get("client_number")
    postal_col = mapping.get("postal_code")

    result["_technician_code"] = result[tech_col].fillna("").astype(str).str.strip().str.upper()
    result["_category"] = result[type_col].map(classify_intervention)
    result["_contronics"] = (
        result[client_col].fillna("").astype(str).str.strip().str.upper().str.startswith(
            rules["contronics"]["client_prefix"]
        )
        if client_col
        else False
    )

    durations: dict[int, float] = {}
    for (_, _), group in result.groupby(["_technician_code", result[date_col].dt.date], sort=False):
        for index, row in group.iterrows():
            durations[index] = calculate_v3_duration(row, group, mapping, rules)
    result["_duration_v3"] = [durations[index] for index in result.index]

    for _, row in result.iterrows():
        code = row["_technician_code"]
        number = _text(row.get(mapping["number"]))
        site = _text(row.get(mapping["site"]))

        if code not in technicians:
            issues.append(
                PlanningIssue(
                    severity="HIGH",
                    category="RESOURCE_UNKNOWN",
                    technician=code,
                    intervention_number=number,
                    message=f"Ressource {code or '(vide)'} absente du référentiel.",
                )
            )
        elif technicians[code].excluded:
            issues.append(
                PlanningIssue(
                    severity="HIGH",
                    category="RESOURCE_EXCLUDED",
                    technician=code,
                    intervention_number=number,
                    message=f"Ressource exclue planifiée : {code}.",
                )
            )

        if bool(row["_contronics"]) and code not in set(rules["contronics"]["experts_confirmes"]):
            issues.append(
                PlanningIssue(
                    severity="MEDIUM",
                    category="CONTRONICS_SKILL",
                    technician=code,
                    intervention_number=number,
                    message=f"Compétence Contronics à vérifier pour {site}.",
                )
            )

        if (
            code == "JSA"
            and rules["constraints"]["JSA"]["paris_intramuros_interdit"]
            and postal_col
            and _text(row.get(postal_col)).startswith("75")
        ):
            issues.append(
                PlanningIssue(
                    severity="HIGH",
                    category="JSA_PARIS",
                    technician=code,
                    intervention_number=number,
                    message="JSA est planifié dans Paris intramuros.",
                )
            )

    duplicate_groups = result.groupby([result[date_col].dt.date, mapping["site"]], dropna=False)
    for (day, site), group in duplicate_groups:
        if len(group) > 1:
            techs = sorted(set(group["_technician_code"]))
            descriptions = (
                group[mapping["description"]].fillna("").astype(str).str.upper()
                if mapping.get("description")
                else pd.Series([], dtype=str)
            )
            if len(techs) > 1 or descriptions.str.contains("DOUBLON", na=False).any():
                issues.append(
                    PlanningIssue(
                        severity="HIGH",
                        category="DUPLICATE",
                        message=f"Doublon possible le {day} sur {site} : {', '.join(techs)}.",
                        context={"count": len(group), "technicians": techs},
                    )
                )

    return result, issues
