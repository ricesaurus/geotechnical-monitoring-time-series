"""Lightweight validation for the Phase 1 metadata-only inventories."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

CONTROLLED_MISSING_VALUES = {
    "not_applicable",
    "not_stated",
    "requires_file_inspection",
    "unknown",
}

DISALLOWED_MISSING_VALUES = {"n/a", "na", "none", "null", "tbd"}
OBSERVATION_COLUMNS = {
    "datetime",
    "date_time",
    "measurement_value",
    "observation",
    "observed_value",
    "reading",
    "timestamp",
    "value",
}
SENSITIVE_COLUMN_TERMS = {"api_key", "credential", "password", "secret", "token"}
SENSITIVE_CONTENT_MARKERS = (
    "api_key=",
    "authorization: bearer",
    "begin private key",
    "credentials.json",
    "password=",
)
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[a-zA-Z]:[\\/]")
POSIX_ABSOLUTE_PATH = re.compile(r"^/(?:etc|home|root|tmp|usr|var)(?:/|$)")


@dataclass(frozen=True)
class InventorySpec:
    """Expected schema and identifier for one inventory."""

    relative_path: Path
    identifier_column: str
    required_columns: frozenset[str]


INVENTORY_SPECS = {
    "sources": InventorySpec(
        relative_path=Path("data/provenance/cleveland_corral_source_inventory.csv"),
        identifier_column="source_id",
        required_columns=frozenset(
            {
                "source_id",
                "source_organization",
                "source_title",
                "official_landing_url",
                "direct_resource_url",
                "source_date",
                "access_date",
                "access_method",
                "available_format",
                "geographic_site_description",
                "documentation_supplied",
                "use_attribution_notes",
                "evidence_url",
                "unresolved_questions",
            }
        ),
    ),
    "sensors": InventorySpec(
        relative_path=Path("data/provenance/cleveland_corral_sensor_inventory.csv"),
        identifier_column="sensor_id",
        required_columns=frozenset(
            {
                "sensor_id",
                "instrument_name",
                "site_location",
                "measured_variable",
                "instrument_type",
                "manufacturer_model",
                "sensor_depth_m",
                "units",
                "measurement_datum",
                "instrument_range",
                "timestamp_timezone",
                "daylight_saving_treatment",
                "nominal_sampling_interval",
                "start_date",
                "end_date",
                "missing_outage_notes",
                "maintenance_instrument_change_notes",
                "source_record",
                "source_file",
                "evidence_url",
                "metadata_completeness",
                "unresolved_fields",
                "phase2_recommendation",
            }
        ),
    ),
    "compatibility": InventorySpec(
        relative_path=Path("data/provenance/cleveland_corral_compatibility.csv"),
        identifier_column="comparison_id",
        required_columns=frozenset(
            {
                "comparison_id",
                "series_ids",
                "candidate_role",
                "site_relationship",
                "metadata_coverage",
                "sampling_frequency_compatibility",
                "time_zone_compatibility",
                "unit_and_datum_clarity",
                "depth_or_location_relevance",
                "continuity_and_instrument_concerns",
                "apparent_temporal_overlap",
                "resampling_may_be_needed",
                "event_analysis_suitability",
                "forecasting_suitability",
                "major_phase2_checks",
                "provisional_recommendation",
                "evidence_url",
            }
        ),
    ),
}


def _is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_inventory(path: Path, spec: InventorySpec) -> list[str]:
    """Return validation errors for a metadata-only CSV inventory."""

    errors: list[str] = []
    if not path.is_file():
        return [f"missing inventory: {path}"]

    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    missing_columns = sorted(spec.required_columns - set(fieldnames))
    if missing_columns:
        errors.append(f"{path}: missing required columns: {', '.join(missing_columns)}")

    duplicate_columns = sorted({name for name in fieldnames if fieldnames.count(name) > 1})
    if duplicate_columns:
        errors.append(f"{path}: duplicate columns: {', '.join(duplicate_columns)}")

    observation_columns = sorted(set(fieldnames) & OBSERVATION_COLUMNS)
    if observation_columns:
        errors.append(
            f"{path}: measurement-observation columns are forbidden: "
            f"{', '.join(observation_columns)}"
        )

    sensitive_columns = sorted(
        name
        for name in fieldnames
        if any(term in name.casefold() for term in SENSITIVE_COLUMN_TERMS)
    )
    if sensitive_columns:
        errors.append(f"{path}: sensitive columns are forbidden: {', '.join(sensitive_columns)}")

    if not rows:
        errors.append(f"{path}: inventory must contain at least one row")

    identifiers: set[str] = set()
    url_columns = [name for name in fieldnames if name.endswith("_url")]
    for row_number, row in enumerate(rows, start=2):
        identifier = (row.get(spec.identifier_column) or "").strip()
        if not identifier:
            errors.append(f"{path}:{row_number}: missing {spec.identifier_column}")
        elif identifier in identifiers:
            errors.append(f"{path}:{row_number}: duplicate identifier {identifier!r}")
        identifiers.add(identifier)

        for column in fieldnames:
            value = (row.get(column) or "").strip()
            if not value:
                errors.append(
                    f"{path}:{row_number}:{column}: blank values are forbidden; use one of "
                    f"{sorted(CONTROLLED_MISSING_VALUES)}"
                )
                continue
            if value.casefold() in DISALLOWED_MISSING_VALUES:
                errors.append(
                    f"{path}:{row_number}:{column}: use a controlled missing value instead of "
                    f"{value!r}"
                )
            if value.casefold().startswith("file://"):
                errors.append(f"{path}:{row_number}:{column}: local file URL is forbidden")
            if WINDOWS_ABSOLUTE_PATH.match(value) or POSIX_ABSOLUTE_PATH.match(value):
                errors.append(f"{path}:{row_number}:{column}: local absolute path is forbidden")
            folded_value = value.casefold()
            if any(marker in folded_value for marker in SENSITIVE_CONTENT_MARKERS):
                errors.append(f"{path}:{row_number}:{column}: possible credential content")

        for column in url_columns:
            value = (row.get(column) or "").strip()
            if value not in CONTROLLED_MISSING_VALUES and not _is_valid_url(value):
                errors.append(f"{path}:{row_number}:{column}: invalid HTTPS URL {value!r}")

    return errors


def validate_repository_inventories(project_root: Path) -> list[str]:
    """Validate all version-controlled Phase 1 inventories."""

    errors: list[str] = []
    for spec in INVENTORY_SPECS.values():
        errors.extend(validate_inventory(project_root / spec.relative_path, spec))
    return errors
