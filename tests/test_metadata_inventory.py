import csv
from pathlib import Path

from geotech_ts.metadata_inventory import (
    InventorySpec,
    validate_inventory,
    validate_repository_inventories,
)
from geotech_ts.paths import PROJECT_ROOT


def test_phase1_metadata_inventories_are_valid() -> None:
    assert validate_repository_inventories(PROJECT_ROOT) == []


def test_validator_rejects_observations_duplicates_and_unsafe_values(tmp_path: Path) -> None:
    inventory_path = tmp_path / "invalid.csv"
    with inventory_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "evidence_url", "timestamp", "note"])
        writer.writerow(["duplicate", "https://example.gov/one", "2020-01-01", "C:\\private"])
        writer.writerow(["duplicate", "not a URL", "2020-01-02", ""])

    spec = InventorySpec(
        relative_path=Path("invalid.csv"),
        identifier_column="record_id",
        required_columns=frozenset({"record_id", "evidence_url", "note"}),
    )

    errors = validate_inventory(inventory_path, spec)

    assert any("measurement-observation columns are forbidden" in error for error in errors)
    assert any("duplicate identifier" in error for error in errors)
    assert any("invalid HTTPS URL" in error for error in errors)
    assert any("local absolute path is forbidden" in error for error in errors)
    assert any("blank values are forbidden" in error for error in errors)
