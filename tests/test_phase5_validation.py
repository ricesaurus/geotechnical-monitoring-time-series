from pathlib import Path

import pandas as pd

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase5_validation import _compare_generated_csv, validate_phase5_outputs


def test_phase5_outputs_are_source_backed_and_valid() -> None:
    assert validate_phase5_outputs(PROJECT_ROOT) == []


def test_phase5_validator_rejects_changed_claim_value(tmp_path: Path) -> None:
    target = tmp_path / "reports/tables/phase5"
    target.mkdir(parents=True)
    source = PROJECT_ROOT / "reports/tables/phase5/claim_evidence_matrix.csv"
    frame = pd.read_csv(source)
    frame.loc[frame["claim_id"].eq("C11"), "claim"] = "A complex model had the lowest later MAE."
    frame.to_csv(target / source.name, index=False)

    expected = pd.read_csv(source)
    errors = _compare_generated_csv(
        tmp_path,
        "reports/tables/phase5/claim_evidence_matrix.csv",
        expected,
    )

    assert any("does not agree with Phase 1–4 source artifacts" in error for error in errors)
