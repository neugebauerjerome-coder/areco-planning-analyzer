from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigurationError(RuntimeError):
    pass


def load_rules(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigurationError(f"Fichier de règles introuvable : {path}")
    try:
        rules = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigurationError(f"JSON invalide dans {path}: {exc}") from exc

    required = {"nap", "grands_itinerants", "exclus", "contronics", "durations", "thresholds"}
    missing = required - set(rules)
    if missing:
        raise ConfigurationError("Règles obligatoires absentes : " + ", ".join(sorted(missing)))
    return rules
