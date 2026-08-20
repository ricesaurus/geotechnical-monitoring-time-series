"""Validation for committed Phase 2 metadata-only artifacts."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from geotech_ts.acquisition import file_digest
from geotech_ts.metadata_inventory import (
    OBSERVATION_COLUMNS,
    SENSITIVE_COLUMN_TERMS,
    SENSITIVE_CONTENT_MARKERS,
    WINDOWS_ABSOLUTE_PATH,
)

SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Phase2TableSpec:
    """Schema and composite-key contract for an aggregate-only table."""

    relative_path: Path
    required_columns: frozenset[str]
    key_columns: tuple[str, ...]


PHASE2_TABLE_SPECS = (
    Phase2TableSpec(
        Path("data/provenance/cleveland_corral_download_manifest.csv"),
        frozenset(
            {
                "resource_id",
                "doi",
                "sciencebase_item_id",
                "sciencebase_item_url",
                "filename",
                "exact_resource_url",
                "byte_size",
                "sha256",
                "source_checksum_algorithm",
                "source_checksum",
                "source_date_uploaded",
                "item_last_updated",
                "access_timestamp_utc",
                "license",
                "local_raw_layer_id",
            }
        ),
        ("resource_id",),
    ),
    Phase2TableSpec(
        Path("data/provenance/cleveland_corral_archive_inventory.csv"),
        frozenset(
            {
                "archive_filename",
                "archive_sha256",
                "member_path",
                "member_crc32",
                "product_type",
                "station",
                "timestamp_column",
                "column_count",
                "columns",
                "data_row_count",
                "timestamp_parse_failure_count",
                "duplicate_timestamp_count",
                "out_of_order_timestamp_count",
                "gap_count",
                "missing_expected_interval_count",
            }
        ),
        ("member_path",),
    ),
    Phase2TableSpec(
        Path("data/provenance/cleveland_corral_qc_summary.csv"),
        frozenset(
            {
                "product_type",
                "sensor_id",
                "measurement_role",
                "installation_segment_id",
                "row_count",
                "nonmissing_value_count",
                "missing_value_count",
                "first_nonmissing_timestamp_pst",
                "last_nonmissing_timestamp_pst",
                "missing_expected_interval_count",
            }
        ),
        ("product_type", "sensor_id", "measurement_role", "installation_segment_id"),
    ),
    Phase2TableSpec(
        Path("data/provenance/cleveland_corral_actual_compatibility.csv"),
        frozenset(
            {
                "candidate_id",
                "product_type",
                "sensor_ids",
                "common_window_start_pst",
                "common_window_end_pst",
                "exact_common_nonmissing_timestamp_count",
                "alignment_note",
            }
        ),
        ("candidate_id", "product_type"),
    ),
    Phase2TableSpec(
        Path("data/provenance/cleveland_corral_product_semantics.csv"),
        frozenset(
            {
                "sensor_id",
                "daily_measurement_role",
                "tested_15_minute_role",
                "tested_aggregation",
                "comparable_date_count",
                "match_within_1e_12_count",
                "mismatch_count",
                "mismatch_calendar_years",
                "maximum_absolute_difference",
            }
        ),
        ("sensor_id", "tested_15_minute_role", "tested_aggregation"),
    ),
)


def _read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def validate_phase2_tables(project_root: Path) -> list[str]:
    """Validate aggregate-only schemas, keys, values, and repository safety."""

    errors: list[str] = []
    for spec in PHASE2_TABLE_SPECS:
        path = project_root / spec.relative_path
        if not path.is_file():
            errors.append(f"missing Phase 2 table: {path}")
            continue
        fieldnames, rows = _read_table(path)
        missing_columns = sorted(spec.required_columns - set(fieldnames))
        if missing_columns:
            errors.append(f"{path}: missing required columns: {', '.join(missing_columns)}")
        forbidden = sorted(set(fieldnames) & OBSERVATION_COLUMNS)
        if forbidden:
            errors.append(f"{path}: observation columns are forbidden: {', '.join(forbidden)}")
        sensitive = sorted(
            column
            for column in fieldnames
            if any(term in column.casefold() for term in SENSITIVE_COLUMN_TERMS)
        )
        if sensitive:
            errors.append(f"{path}: sensitive columns are forbidden: {', '.join(sensitive)}")
        if not rows:
            errors.append(f"{path}: table must contain at least one row")
            continue

        observed_keys: set[tuple[str, ...]] = set()
        for row_number, row in enumerate(rows, start=2):
            key = tuple((row.get(column) or "").strip() for column in spec.key_columns)
            if not all(key):
                errors.append(f"{path}:{row_number}: blank composite key")
            elif key in observed_keys:
                errors.append(f"{path}:{row_number}: duplicate composite key {key}")
            observed_keys.add(key)
            for column in fieldnames:
                value = (row.get(column) or "").strip()
                if not value:
                    errors.append(f"{path}:{row_number}:{column}: blank value")
                    continue
                if WINDOWS_ABSOLUTE_PATH.match(value) or value.startswith(("/home/", "/tmp/")):
                    errors.append(f"{path}:{row_number}:{column}: local absolute path")
                if any(marker in value.casefold() for marker in SENSITIVE_CONTENT_MARKERS):
                    errors.append(f"{path}:{row_number}:{column}: possible credential content")
                if column.endswith("_count") or column in {
                    "byte_size",
                    "column_count",
                    "data_row_count",
                    "row_count",
                }:
                    try:
                        if int(value) < 0:
                            raise ValueError
                    except ValueError:
                        errors.append(f"{path}:{row_number}:{column}: expected nonnegative integer")

        if spec.relative_path.name == "cleveland_corral_download_manifest.csv":
            for row_number, row in enumerate(rows, start=2):
                if not SHA256_PATTERN.fullmatch(row.get("sha256", "")):
                    errors.append(f"{path}:{row_number}: invalid SHA-256")
                local_id = row.get("local_raw_layer_id", "")
                if Path(local_id).is_absolute() or ".." in Path(local_id).parts:
                    errors.append(f"{path}:{row_number}: unsafe local raw-layer identifier")
    return errors


def verify_download_manifest(project_root: Path) -> list[str]:
    """Verify local ignored raw resources against the committed manifest."""

    path = project_root / "data/provenance/cleveland_corral_download_manifest.csv"
    _, rows = _read_table(path)
    raw_root = (project_root / "data/raw").resolve()
    errors: list[str] = []
    for row in rows:
        resource = (raw_root / row["local_raw_layer_id"]).resolve()
        if raw_root not in resource.parents:
            errors.append(f"unsafe raw resource path: {resource}")
            continue
        if not resource.is_file():
            errors.append(f"missing raw resource: {row['local_raw_layer_id']}")
            continue
        if resource.stat().st_size != int(row["byte_size"]):
            errors.append(f"size mismatch: {row['local_raw_layer_id']}")
        if file_digest(resource) != row["sha256"]:
            errors.append(f"SHA-256 mismatch: {row['local_raw_layer_id']}")
    return errors
