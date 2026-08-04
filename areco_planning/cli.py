from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core.service import build_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description="ARECO Planning Suite V4.0.1")
    parser.add_argument("planning", type=Path, help="Export Excel ARFITEC")
    parser.add_argument(
        "--teams",
        type=Path,
        default=Path(__file__).parent / "data" / "toutes_les_equipes_areco.xlsx",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=Path(__file__).parent / "config" / "rules_v4.json",
    )
    parser.add_argument("--json", type=Path, help="Écrire le résumé JSON dans ce fichier")
    args = parser.parse_args()

    dataset = build_dataset(args.planning, args.teams, args.rules)
    summary = {
        "version": "4.0.1",
        "dates": [str(d) for d in dataset.analysis_dates],
        "interventions": dataset.metadata["row_count"],
        "techniciens_actifs": dataset.metadata["technician_count"],
        "problemes": len(dataset.issues),
        "problemes_par_categorie": {},
    }
    for issue in dataset.issues:
        summary["problemes_par_categorie"][issue.category] = (
            summary["problemes_par_categorie"].get(issue.category, 0) + 1
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.json:
        args.json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
