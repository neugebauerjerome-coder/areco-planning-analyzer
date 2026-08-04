from __future__ import annotations
import re
from typing import Any
import pandas as pd

def _text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()

def intervention_address(row: pd.Series, mapping: dict[str, str | None]) -> str:
    parts = []
    for key in ("address", "address2", "postal_code", "city"):
        column = mapping.get(key)
        if column:
            value = _text(row.get(column))
            if value and value != "46":
                parts.append(value)
    country_column = mapping.get("country")
    country = _text(row.get(country_column)) if country_column else ""
    parts.append(country or "FR")
    return ", ".join(parts)

def technician_home_address(location: str) -> str:
    value = _text(location)
    if not value:
        return ""
    if "(" in value and ")" in value:
        value = value.split("(", 1)[1].split(")", 1)[0]
    value = value.split("/")[0].strip()
    value = re.sub(r"^GI\s+", "", value, flags=re.IGNORECASE)
    if not value:
        return ""
    if any(country in value.lower() for country in ("france", "belgique", "luxembourg", "espagne", "allemagne")):
        return value
    return f"{value}, France"
