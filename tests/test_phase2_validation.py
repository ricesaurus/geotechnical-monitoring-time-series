import csv
from pathlib import Path

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase2_validation import validate_phase2_tables


def test_committed_phase2_tables_are_aggregate_only_and_valid() -> None:
    assert validate_phase2_tables(PROJECT_ROOT) == []


def test_phase2_validator_rejects_observation_columns_and_duplicate_keys(
    tmp_path: Path,
) -> None:
    provenance = tmp_path / "data/provenance"
    provenance.mkdir(parents=True)
    for source in (PROJECT_ROOT / "data/provenance").glob("cleveland_corral_*.csv"):
        (provenance / source.name).write_bytes(source.read_bytes())

    target = provenance / "cleveland_corral_actual_compatibility.csv"
    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.append(dict(rows[0]))
    fieldnames = [*rows[0], "value"]
    for row in rows:
        row["value"] = "1"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    errors = validate_phase2_tables(tmp_path)

    assert any("observation columns are forbidden" in error for error in errors)
    assert any("duplicate composite key" in error for error in errors)
