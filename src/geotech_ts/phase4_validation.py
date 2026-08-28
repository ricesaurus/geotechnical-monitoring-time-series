"""Validation for Phase 4 aggregate, visual, notebook, and processed outputs."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq

WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
FORBIDDEN_OBSERVATION_COLUMNS = {
    "local_date",
    "origin_date",
    "target_date",
    "target_value",
    "prediction",
    "error",
    "absolute_error",
    "squared_error",
    "scaled_absolute_error",
    "high_movement_threshold",
    "parameter_value",
}


@dataclass(frozen=True)
class OutputSpec:
    """Required schema and minimum row count for one aggregate table."""

    filename: str
    required_columns: frozenset[str]
    minimum_rows: int = 1


TABLE_SPECS = (
    OutputSpec("analysis_configuration.csv", frozenset({"parameter", "value"})),
    OutputSpec(
        "target_windows.csv",
        frozenset(
            {
                "window_id",
                "target_id",
                "start_date",
                "end_date_inclusive",
                "eligible_target_change_count",
            }
        ),
        3,
    ),
    OutputSpec(
        "model_specifications.csv",
        frozenset(
            {
                "model_id",
                "family",
                "order",
                "targets",
                "horizons_days",
                "complexity_rank",
            }
        ),
        10,
    ),
    OutputSpec(
        "validation_metrics.csv",
        frozenset(
            {
                "window_id",
                "stage",
                "model_id",
                "horizon_days",
                "point_coverage_fraction",
                "mae",
                "rmse",
                "bias",
                "mase",
            }
        ),
    ),
    OutputSpec(
        "stratified_metrics.csv",
        frozenset(
            {
                "window_id",
                "model_id",
                "horizon_days",
                "dimension",
                "group_value",
                "forecast_count",
                "mae",
            }
        ),
    ),
    OutputSpec(
        "interval_diagnostics.csv",
        frozenset(
            {
                "window_id",
                "model_id",
                "horizon_days",
                "nominal_level",
                "empirical_coverage",
                "average_width",
                "mean_winkler_score",
            }
        ),
    ),
    OutputSpec(
        "residual_diagnostics.csv",
        frozenset(
            {
                "window_id",
                "model_id",
                "horizon_days",
                "lag_in_origin_sequence",
                "residual_acf",
                "ljung_box_p_value",
                "ljung_box_caveat",
            }
        ),
    ),
    OutputSpec(
        "model_coverage_failures.csv",
        frozenset(
            {
                "window_id",
                "model_id",
                "horizon_days",
                "status",
                "attempt_count",
            }
        ),
    ),
    OutputSpec(
        "parameter_stability.csv",
        frozenset(
            {
                "window_id",
                "model_id",
                "parameter",
                "fit_count",
                "median",
                "q25",
                "q75",
            }
        ),
    ),
    OutputSpec(
        "forecast_comparison_uncertainty.csv",
        frozenset(
            {
                "window_id",
                "model_id",
                "reference_model_id",
                "common_origin_count",
                "mean_absolute_error_difference",
                "difference_ci_low",
                "difference_ci_high",
            }
        ),
    ),
    OutputSpec(
        "selection_decisions.csv",
        frozenset(
            {
                "window_id",
                "target_id",
                "horizon_days",
                "retained_model_id",
                "selection_reason",
                "selection_common_origin_count",
                "evaluation_does_not_revise_selection",
            }
        ),
        6,
    ),
    OutputSpec(
        "changepoint_run_summary.csv",
        frozenset(
            {
                "run_id",
                "window_id",
                "run_start_date",
                "run_end_date",
                "run_length_days",
                "sensitivity_setting_count",
            }
        ),
    ),
    OutputSpec(
        "changepoint_sensitivity.csv",
        frozenset(
            {
                "run_id",
                "method",
                "setting",
                "candidate_date",
                "minimum_segment_length_days",
            }
        ),
    ),
    OutputSpec(
        "changepoint_candidates.csv",
        frozenset(
            {
                "candidate_group_id",
                "candidate_date",
                "supporting_setting_count",
                "sensitivity_stability",
                "context_classification",
                "interpretation_limit",
            }
        ),
    ),
    OutputSpec(
        "synthetic_leakage_demo.csv",
        frozenset(
            {
                "data_origin",
                "validation_design",
                "training_includes_post_shift",
                "mae",
                "rmse",
                "bias",
            }
        ),
        2,
    ),
)

FIGURE_FILENAMES = tuple(
    f"{number:02d}_{name}.png"
    for number, name in (
        (1, "validation_mae"),
        (2, "relative_mae_to_zero"),
        (3, "interval_calibration"),
        (4, "retained_residual_acf"),
        (5, "water_year_stability"),
        (6, "coefficient_stability"),
        (7, "changepoint_sensitivity"),
        (8, "synthetic_leakage"),
        (9, "forecast_coverage_failures"),
    )
)


def _validate_notebook(project_root: Path) -> list[str]:
    errors: list[str] = []
    path = project_root / "notebooks/03_phase4_forecasting_validation.ipynb"
    if not path.is_file():
        return [f"missing executed Phase 4 notebook: {path}"]
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid Phase 4 notebook: {error}"]
    code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
    if not code_cells:
        errors.append(f"{path}: expected instructional code cells")
    for cell_number, cell in enumerate(code_cells, start=1):
        if cell.get("execution_count") is None:
            errors.append(f"{path}: code cell {cell_number} was not executed")
        if any(output.get("output_type") == "error" for output in cell.get("outputs", [])):
            errors.append(f"{path}: code cell {cell_number} contains an error output")
    return errors


def validate_phase4_outputs(
    project_root: Path,
    *,
    require_local_processed: bool = False,
    require_executed_notebook: bool = True,
) -> list[str]:
    """Return errors for missing, unsafe, unexecuted, or observation-bearing outputs."""

    errors: list[str] = []
    table_directory = project_root / "reports/tables/phase4"
    for spec in TABLE_SPECS:
        path = table_directory / spec.filename
        if not path.is_file():
            errors.append(f"missing Phase 4 aggregate table: {path}")
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
            errors.append(
                f"{path}: observation columns are forbidden: {', '.join(forbidden)}"
            )
        if len(rows) < spec.minimum_rows:
            errors.append(f"{path}: expected at least {spec.minimum_rows} rows")
        for row_number, row in enumerate(rows, start=2):
            for column, value in row.items():
                if value is None:
                    continue
                if WINDOWS_ABSOLUTE_PATH.match(value) or value.startswith(("/home/", "/tmp/")):
                    errors.append(f"{path}:{row_number}:{column}: local absolute path")
            if spec.filename == "validation_metrics.csv":
                coverage_text = row.get("point_coverage_fraction", "")
                if coverage_text:
                    coverage = float(coverage_text)
                    if not 0 <= coverage <= 1:
                        errors.append(
                            f"{path}:{row_number}: point coverage must be between zero and one"
                        )

    figure_directory = project_root / "reports/figures/phase4"
    for filename in FIGURE_FILENAMES:
        path = figure_directory / filename
        if not path.is_file() or path.stat().st_size < 10_000:
            errors.append(f"missing or implausibly small Phase 4 figure: {path}")
        elif path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            errors.append(f"invalid PNG signature: {path}")

    if require_executed_notebook:
        errors.extend(_validate_notebook(project_root))

    if require_local_processed:
        processed = project_root / "data/processed/cleveland_corral"
        for filename in (
            "phase4_rolling_forecasts.parquet",
            "phase4_rolling_parameters.parquet",
            "phase4_changepoint_detections.parquet",
        ):
            path = processed / filename
            if not path.is_file():
                errors.append(f"missing ignored Phase 4 processed output: {path}")
            elif pq.read_metadata(path).num_rows < 1:
                errors.append(f"empty Phase 4 processed output: {path}")
    return errors
