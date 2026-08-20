from pathlib import Path

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase3_validation import validate_phase3_outputs


def test_phase3_outputs_are_present_aggregate_only_and_valid() -> None:
    assert validate_phase3_outputs(PROJECT_ROOT) == []


def test_phase3_validator_rejects_observation_columns(tmp_path: Path) -> None:
    table_directory = tmp_path / "reports/tables/phase3"
    table_directory.mkdir(parents=True)
    source_directory = PROJECT_ROOT / "reports/tables/phase3"
    for source in source_directory.glob("*.csv"):
        target = table_directory / source.name
        target.write_bytes(source.read_bytes())
    target = table_directory / "event_selection.csv"
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines()
    lines[0] += ",timestamp_pst_fixed"
    for index in range(1, len(lines)):
        lines[index] += ",2020-01-01"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")

    errors = validate_phase3_outputs(tmp_path)

    assert any("observation columns are forbidden" in error for error in errors)
