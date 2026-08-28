"""Reproduce the complete Phase 4 forecasting and changepoint workflow."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from geotech_ts.paths import FIGURES_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(PROCESSED_DATA_DIR / "cleveland_corral/.matplotlib"),
)

from geotech_ts.changepoints import detect_changepoints, summarize_changepoints  # noqa: E402
from geotech_ts.forecast_metrics import (  # noqa: E402
    aggregate_validation_metrics,
    forecast_comparison_uncertainty,
    interval_diagnostics,
    model_coverage_failures,
    parameter_stability,
    residual_diagnostics,
    selection_decisions,
    stratified_validation_metrics,
    synthetic_leakage_demo,
)
from geotech_ts.forecasting import (  # noqa: E402
    model_specifications_table,
    run_rolling_forecasts,
    target_windows_table,
)
from geotech_ts.phase4_plots import (  # noqa: E402
    plot_changepoint_sensitivity,
    plot_forecast_coverage,
    plot_interval_calibration,
    plot_parameter_paths,
    plot_relative_mae,
    plot_retained_residual_acf,
    plot_synthetic_leakage,
    plot_validation_mae,
    plot_water_year_stability,
)

TABLE_DIRECTORY = PROJECT_ROOT / "reports/tables/phase4"
FIGURE_DIRECTORY = FIGURES_DIR / "phase4"
PROCESSED_DIRECTORY = PROCESSED_DATA_DIR / "cleveland_corral"


def _write_csv(frame: pd.DataFrame, filename: str) -> None:
    path = TABLE_DIRECTORY / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")
    print(f"Wrote {len(frame):,} aggregate rows: {path.relative_to(PROJECT_ROOT)}")


def _write_parquet_atomic(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial")
    if partial.exists():
        raise RuntimeError(f"Inspect interrupted output before retrying: {partial}")
    frame.to_parquet(partial, index=False)
    if pq.read_metadata(partial).num_rows != len(frame):
        partial.unlink()
        raise RuntimeError(f"Parquet row-count verification failed for {path.name}")
    partial.replace(path)
    print(f"Wrote {len(frame):,} ignored processed rows: {path.relative_to(PROJECT_ROOT)}")


def _configuration_table() -> pd.DataFrame:
    rows = (
        ("contract_frozen", "2026-08-27 before Phase 4 model comparison"),
        ("time_zone", "fixed PST (UTC-08:00) local calendar dates"),
        ("targets", "Phase 3 eligible daily first differences for mid_E2_B and toe_E5_C"),
        ("horizons_days", "1;2;7"),
        ("origin_schedule", "every 14 calendar days on fixed, never-shifted anchors"),
        ("minimum_training", "365 calendar days and 300 eligible target observations"),
        ("window_rule", "expanding complete daily calendar; missing targets remain missing"),
        (
            "core_origin_rule",
            "eligible origin-through-target path inside one target segment and water year",
        ),
        ("primary_metric", "MAE"),
        ("secondary_metrics", "RMSE;bias;training-only MASE"),
        ("high_movement", "absolute target above origin-specific training q95"),
        ("seasons", "wet October-April; dry May-September"),
        ("interval_levels", "80%;95%"),
        (
            "baseline_intervals",
            "empirical prior realized residuals only; minimum 30",
        ),
        ("arima_intervals", "statsmodels model-based state-space intervals"),
        (
            "arimax_availability",
            "toe rain lag 2 available only at horizons 1 and 2; horizon 7 skipped",
        ),
        (
            "performance_difference_uncertainty",
            "seed 170 moving-block bootstrap; 1000 replicates; block 3 origins",
        ),
        (
            "selection",
            "earlier stage common origins; 80% coverage; 5% complexity tie rule",
        ),
        (
            "changepoints",
            "exact runs >=180 days; min segment 30; PELT and Binseg sensitivity",
        ),
        ("synthetic_demo", "seed 170 regime-shift leakage example; not USGS data"),
    )
    return pd.DataFrame(rows, columns=["parameter", "value"])


def _build_aggregates(
    predictions: pd.DataFrame,
    parameters: pd.DataFrame,
    detections: pd.DataFrame,
    run_summary: pd.DataFrame,
    daily_series: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    metrics = aggregate_validation_metrics(predictions)
    stratified = stratified_validation_metrics(predictions)
    intervals = interval_diagnostics(predictions)
    residuals = residual_diagnostics(predictions)
    failures = model_coverage_failures(predictions)
    stability = parameter_stability(parameters)
    uncertainty = forecast_comparison_uncertainty(predictions)
    decisions = selection_decisions(predictions)
    candidates = summarize_changepoints(detections, daily_series)
    if not candidates.empty:
        candidate_counts = candidates.groupby("run_id").size()
        run_summary["candidate_group_count"] = (
            run_summary["run_id"].map(candidate_counts).fillna(0).astype(int)
        )
    else:
        run_summary["candidate_group_count"] = 0
    synthetic_summary, synthetic_values = synthetic_leakage_demo()
    return {
        "analysis_configuration": _configuration_table(),
        "target_windows": target_windows_table(daily_series),
        "model_specifications": model_specifications_table(),
        "validation_metrics": metrics,
        "stratified_metrics": stratified,
        "interval_diagnostics": intervals,
        "residual_diagnostics": residuals,
        "model_coverage_failures": failures,
        "parameter_stability": stability,
        "forecast_comparison_uncertainty": uncertainty,
        "selection_decisions": decisions,
        "changepoint_run_summary": run_summary,
        "changepoint_sensitivity": detections,
        "changepoint_candidates": candidates,
        "synthetic_leakage_demo": synthetic_summary,
        "synthetic_values": synthetic_values,
    }


def _write_tables(aggregates: dict[str, pd.DataFrame]) -> None:
    for name, frame in aggregates.items():
        if name == "synthetic_values":
            continue
        _write_csv(frame, f"{name}.csv")


def _write_figures(
    aggregates: dict[str, pd.DataFrame],
    parameters: pd.DataFrame,
    detections: pd.DataFrame,
) -> None:
    plot_validation_mae(
        aggregates["validation_metrics"], FIGURE_DIRECTORY / "01_validation_mae.png"
    )
    plot_relative_mae(
        aggregates["validation_metrics"],
        FIGURE_DIRECTORY / "02_relative_mae_to_zero.png",
    )
    plot_interval_calibration(
        aggregates["interval_diagnostics"],
        aggregates["selection_decisions"],
        FIGURE_DIRECTORY / "03_interval_calibration.png",
    )
    plot_retained_residual_acf(
        aggregates["residual_diagnostics"],
        aggregates["selection_decisions"],
        FIGURE_DIRECTORY / "04_retained_residual_acf.png",
    )
    plot_water_year_stability(
        aggregates["stratified_metrics"],
        aggregates["selection_decisions"],
        FIGURE_DIRECTORY / "05_water_year_stability.png",
    )
    plot_parameter_paths(parameters, FIGURE_DIRECTORY / "06_coefficient_stability.png")
    plot_changepoint_sensitivity(
        detections,
        aggregates["changepoint_candidates"],
        FIGURE_DIRECTORY / "07_changepoint_sensitivity.png",
    )
    plot_synthetic_leakage(
        aggregates["synthetic_leakage_demo"],
        aggregates["synthetic_values"],
        FIGURE_DIRECTORY / "08_synthetic_leakage.png",
    )
    plot_forecast_coverage(
        aggregates["validation_metrics"],
        FIGURE_DIRECTORY / "09_forecast_coverage_failures.png",
    )
    print(f"Wrote curated figures: {FIGURE_DIRECTORY.relative_to(PROJECT_ROOT)}")


def _read_existing_aggregates() -> dict[str, pd.DataFrame]:
    names = (
        "analysis_configuration",
        "target_windows",
        "model_specifications",
        "validation_metrics",
        "stratified_metrics",
        "interval_diagnostics",
        "residual_diagnostics",
        "model_coverage_failures",
        "parameter_stability",
        "forecast_comparison_uncertainty",
        "selection_decisions",
        "changepoint_run_summary",
        "changepoint_sensitivity",
        "changepoint_candidates",
        "synthetic_leakage_demo",
    )
    result = {name: pd.read_csv(TABLE_DIRECTORY / f"{name}.csv") for name in names}
    _, synthetic_values = synthetic_leakage_demo()
    result["synthetic_values"] = synthetic_values
    return result


def main() -> None:
    """Build per-origin outputs, aggregate diagnostics, and curated figures."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="reuse completed processed data and aggregate diagnostics",
    )
    args = parser.parse_args()
    if args.figures_only:
        aggregates = _read_existing_aggregates()
        parameters = pd.read_parquet(
            PROCESSED_DIRECTORY / "phase4_rolling_parameters.parquet"
        )
        detections = pd.read_parquet(
            PROCESSED_DIRECTORY / "phase4_changepoint_detections.parquet"
        )
        _write_figures(aggregates, parameters, detections)
        return

    daily_series = pd.read_parquet(
        PROCESSED_DIRECTORY / "phase3_daily_analysis_series.parquet"
    )
    predictions, parameters = run_rolling_forecasts(daily_series)
    detections, run_summary = detect_changepoints(daily_series)

    _write_parquet_atomic(
        predictions, PROCESSED_DIRECTORY / "phase4_rolling_forecasts.parquet"
    )
    _write_parquet_atomic(
        parameters, PROCESSED_DIRECTORY / "phase4_rolling_parameters.parquet"
    )
    _write_parquet_atomic(
        detections, PROCESSED_DIRECTORY / "phase4_changepoint_detections.parquet"
    )

    aggregates = _build_aggregates(
        predictions, parameters, detections, run_summary, daily_series
    )
    _write_tables(aggregates)
    _write_figures(aggregates, parameters, detections)


if __name__ == "__main__":
    main()
