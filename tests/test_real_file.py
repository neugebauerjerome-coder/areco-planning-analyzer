from pathlib import Path

from areco_planning.core.service import build_dataset


ROOT = Path(__file__).resolve().parents[1]


def test_real_arfitec_file_is_read():
    dataset = build_dataset(
        ROOT / "samples/planning_test_04-08-2026.xlsx",
        ROOT / "areco_planning/data/toutes_les_equipes_areco.xlsx",
        ROOT / "areco_planning/config/rules_v4.json",
    )
    assert dataset.metadata["row_count"] == 49
    assert dataset.metadata["technician_count"] == 23
    assert len(dataset.analysis_dates) == 1
    assert "_duration_v3" in dataset.interventions.columns
    assert "_contronics" in dataset.interventions.columns
