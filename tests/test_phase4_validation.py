import csv
from pathlib import Path

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase4_validation import validate_phase4_outputs


def test_phase4_outputs_are_present_aggregate_only_and_valid() -> None:
    # CI checks only version-controlled deliverables. The explicit local verifier also
    # requires the ignored observation-bearing Parquet products after a full build.
    assert validate_phase4_outputs(PROJECT_ROOT, require_local_processed=False) == []


def test_phase4_validator_rejects_observation_columns_and_invalid_coverage(
    tmp_path: Path,
) -> None:
    table_directory = tmp_path / "reports/tables/phase4"
    table_directory.mkdir(parents=True)
    source_directory = PROJECT_ROOT / "reports/tables/phase4"
    for source in source_directory.glob("*.csv"):
        (table_directory / source.name).write_bytes(source.read_bytes())

    target = table_directory / "validation_metrics.csv"
    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fieldnames = [*rows[0], "origin_date"]
    rows[0]["point_coverage_fraction"] = "1.2"
    for row in rows:
        row["origin_date"] = "2020-01-01"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    errors = validate_phase4_outputs(
        tmp_path, require_local_processed=False, require_executed_notebook=False
    )

    assert any("observation columns are forbidden" in error for error in errors)
    assert any("point coverage must be between zero and one" in error for error in errors)
