"""Validation for Phase 3 aggregate, visual, and ignored processed outputs."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq

WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
FORBIDDEN_OBSERVATION_COLUMNS = {
    "timestamp_original",
    "timestamp_pst_fixed",
    "timestamp_utc",
    "local_date",
    "value_original",
    "predictor_value",
    "response_value",
    "source_row_number",
}


@dataclass(frozen=True)
class OutputSpec:
    """Schema and minimum-row contract for a Phase 3 aggregate table."""

    filename: str
    required_columns: frozenset[str]
    minimum_rows: int = 1


TABLE_SPECS = (
    OutputSpec("analysis_configuration.csv", frozenset({"parameter", "value"})),
    OutputSpec(
        "coverage_missingness.csv",
        frozenset(
            {
                "product_type",
                "sensor_id",
                "installation_segment_id",
                "absent_timestamp_count",
                "blank_measurement_count",
                "eligible_level_count",
            }
        ),
    ),
    OutputSpec(
        "gap_length_distribution.csv",
        frozenset({"sensor_id", "missing_interval_count", "gap_duration_hours", "gap_count"}),
    ),
    OutputSpec(
        "distribution_summary.csv",
        frozenset({"sensor_id", "transformation", "scope_id", "n", "median", "iqr"}),
    ),
    OutputSpec(
        "decomposition_diagnostics.csv",
        frozenset(
            {"sensor_id", "transformation", "n", "seasonal_period_days", "seasonal_strength"}
        ),
    ),
    OutputSpec(
        "stationarity_diagnostics.csv",
        frozenset(
            {
                "sensor_id",
                "transformation",
                "n",
                "adf_p_value",
                "kpss_p_value",
                "joint_interpretation",
            }
        ),
    ),
    OutputSpec(
        "acf_pacf_diagnostics.csv",
        frozenset({"sensor_id", "transformation", "n", "lag_days", "acf", "pacf"}),
    ),
    OutputSpec(
        "daily_lag_curves.csv",
        frozenset(
            {"window_id", "predictor", "response", "method", "lag_days", "correlation"}
        ),
    ),
    OutputSpec(
        "daily_lag_summary.csv",
        frozenset(
            {
                "window_id",
                "predictor",
                "response",
                "method",
                "peak_lag_days",
                "peak_correlation",
                "lag_sign_convention",
            }
        ),
    ),
    OutputSpec(
        "event_selection.csv",
        frozenset({"event_id", "event_date", "daily_interval_rain_mm", "selection_rule"}),
        minimum_rows=3,
    ),
    OutputSpec(
        "event_alignment_sensitivity.csv",
        frozenset(
            {
                "event_id",
                "response_sensor",
                "tolerance_minutes",
                "peak_lag_hours",
                "stable_across_tolerances",
            }
        ),
    ),
    OutputSpec(
        "synthetic_acf_pacf.csv",
        frozenset({"data_origin", "seed", "series", "lag", "acf", "pacf"}),
    ),
)

FIGURE_FILENAMES = tuple(f"{number:02d}_{name}.png" for number, name in (
    (1, "daily_coverage_missingness"),
    (2, "daily_levels_sensor_regimes"),
    (3, "daily_distributions"),
    (4, "water_year_seasonality"),
    (5, "robust_stl_decomposition"),
    (6, "daily_acf_pacf"),
    (7, "daily_lag_sensitivity"),
    (8, "event_alignment_sensitivity"),
    (9, "synthetic_linear_processes"),
))


def validate_phase3_outputs(
    project_root: Path, *, require_local_processed: bool = False
) -> list[str]:
    """Return errors for missing, unsafe, or observation-bearing deliverables."""

    errors: list[str] = []
    table_directory = project_root / "reports/tables/phase3"
    for spec in TABLE_SPECS:
        path = table_directory / spec.filename
        if not path.is_file():
            errors.append(f"missing Phase 3 aggregate table: {path}")
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = list(reader.fieldnames or [])
            rows = list(reader)
        missing = sorted(spec.required_columns - set(fieldnames))
        if missing:
            errors.append(f"{path}: missing columns: {', '.join(missing)}")
        forbidden = sorted(FORBIDDEN_OBSERVATION_COLUMNS & set(fieldnames))
        if forbidden:
            errors.append(f"{path}: observation columns are forbidden: {', '.join(forbidden)}")
        if len(rows) < spec.minimum_rows:
            errors.append(f"{path}: expected at least {spec.minimum_rows} rows")
        for row_number, row in enumerate(rows, start=2):
            for column, value in row.items():
                if value is None:
                    continue
                if WINDOWS_ABSOLUTE_PATH.match(value) or value.startswith(("/home/", "/tmp/")):
                    errors.append(f"{path}:{row_number}:{column}: local absolute path")

    figure_directory = project_root / "reports/figures/phase3"
    for filename in FIGURE_FILENAMES:
        path = figure_directory / filename
        if not path.is_file() or path.stat().st_size < 10_000:
            errors.append(f"missing or implausibly small Phase 3 figure: {path}")
        elif path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            errors.append(f"invalid PNG signature: {path}")

    if require_local_processed:
        processed = project_root / "data/processed/cleveland_corral"
        for filename in (
            "phase3_daily_analysis_series.parquet",
            "phase3_event_alignment_pairs.parquet",
        ):
            path = processed / filename
            if not path.is_file():
                errors.append(f"missing ignored Phase 3 processed output: {path}")
            elif pq.read_metadata(path).num_rows < 1:
                errors.append(f"empty Phase 3 processed output: {path}")
    return errors
