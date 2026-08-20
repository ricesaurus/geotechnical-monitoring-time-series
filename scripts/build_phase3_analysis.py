"""Reproduce the complete Phase 3 exploratory-dynamics workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from geotech_ts.exploratory import (
    PHASE3_SENSORS,
    add_level_eligibility,
    build_daily_analysis_series,
    coverage_missingness_summary,
    daily_lag_diagnostics,
    decomposition_diagnostics,
    dependence_diagnostics,
    distribution_summary,
    event_alignment_diagnostics,
    gap_length_distribution,
    select_rain_events,
    stationarity_diagnostics,
    synthetic_linear_process_diagnostics,
)
from geotech_ts.paths import FIGURES_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, PROJECT_ROOT
from geotech_ts.phase3_plots import (
    plot_acf_pacf,
    plot_daily_coverage,
    plot_daily_lag_curves,
    plot_distributions,
    plot_event_sensitivity,
    plot_representative_decomposition,
    plot_synthetic_demo,
    plot_temporal_regimes,
    plot_water_year_patterns,
)

TABLE_DIRECTORY = PROJECT_ROOT / "reports/tables/phase3"
FIGURE_DIRECTORY = FIGURES_DIR / "phase3"
PROCESSED_DIRECTORY = PROCESSED_DATA_DIR / "cleveland_corral"

PHASE3_INPUT_COLUMNS = [
    "timestamp_pst_fixed",
    "water_year",
    "expected_interval_minutes",
    "product_type",
    "sensor_id",
    "measurement_role",
    "installation_segment_id",
    "value",
    "flag_timestamp_parse_failure",
    "flag_duplicate_timestamp_in_member",
    "flag_duplicate_timestamp",
    "flag_out_of_order_timestamp",
    "flag_missing_value",
    "flag_nonfinite_value",
    "flag_malformed_value",
    "flag_sentinel_candidate",
    "flag_documented_maintenance_or_outage",
    "flag_metadata_range_concern",
    "flag_unexplained_negative_increment",
]


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
        ("time_zone", "fixed PST (UTC-08:00) year-round"),
        ("daily_alignment", "exact local date; no interpolation"),
        ("level_mask", "numeric timestamped rows inside documented operation and outside outages"),
        ("metadata_range_concerns", "retained and counted; not automatically invalidated"),
        ("daily_interval_rain_minimum_coverage", "90 of 96 nominal 15-minute intervals"),
        (
            "published_rain_difference",
            "consecutive eligible dates, same water year and regime, both daily semantics matched",
        ),
        (
            "displacement_difference",
            "consecutive eligible dates, same water year and installation segment; "
            "negatives retained",
        ),
        ("decomposition", "robust STL on exact contiguous daily runs; periods 365 and 366"),
        ("stationarity", "ADF with intercept/AIC lags plus KPSS level-stationarity/auto lags"),
        ("acf_pacf", "daily lags, maximum 60 or sample-size limit; approximate 1.96/sqrt(n) bands"),
        ("daily_lag_range", "0 through 30 days; positive means predictor leads response"),
        ("daily_uncertainty", "500-replicate moving-block bootstrap, up to 30-row blocks"),
        (
            "event_selection",
            "top 3 eligible daily interval-rain totals at least 7 days apart; "
            "no displacement input",
        ),
        ("event_window", "one day before through two days after the selected rain date"),
        ("event_alignment", "one-to-one nearest; 8- and 15-minute tolerances; no reuse"),
        ("event_lag_range", "0 through 48 hours in 15-minute steps; rain leads response"),
        ("synthetic_demo", "AR(1), MA(1), random walk; seed 170; never mixed with USGS data"),
    )
    return pd.DataFrame(rows, columns=["parameter", "value"])


def main() -> None:
    """Build processed masks, aggregate diagnostics, and curated figures."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="reuse completed processed data and aggregate diagnostics",
    )
    args = parser.parse_args()

    if args.figures_only:
        daily_series = pd.read_parquet(
            PROCESSED_DIRECTORY / "phase3_daily_analysis_series.parquet"
        )
        decomposition = pd.read_csv(TABLE_DIRECTORY / "decomposition_diagnostics.csv")
        dependence = pd.read_csv(TABLE_DIRECTORY / "acf_pacf_diagnostics.csv")
        lag_curves = pd.read_csv(TABLE_DIRECTORY / "daily_lag_curves.csv")
        event_summary = pd.read_csv(TABLE_DIRECTORY / "event_alignment_sensitivity.csv")
        simulated, synthetic_diagnostics = synthetic_linear_process_diagnostics()
        _write_figures(
            daily_series,
            decomposition,
            dependence,
            lag_curves,
            event_summary,
            simulated,
            synthetic_diagnostics,
        )
        return

    interim = INTERIM_DATA_DIR / "cleveland_corral"
    fifteen = pd.read_parquet(
        interim / "selected_15_minute_quality_flagged.parquet", columns=PHASE3_INPUT_COLUMNS
    )
    daily = pd.read_parquet(
        interim / "selected_daily_quality_flagged.parquet", columns=PHASE3_INPUT_COLUMNS
    )
    fifteen = fifteen.loc[fifteen["sensor_id"].isin(PHASE3_SENSORS)].copy()
    daily = daily.loc[daily["sensor_id"].isin(PHASE3_SENSORS)].copy()

    masked_fifteen = add_level_eligibility(fifteen)
    masked_daily = add_level_eligibility(daily)
    del fifteen, daily
    coverage = pd.concat(
        [
            coverage_missingness_summary(masked_fifteen),
            coverage_missingness_summary(masked_daily),
        ],
        ignore_index=True,
    )
    gaps = pd.concat(
        [gap_length_distribution(masked_fifteen), gap_length_distribution(masked_daily)],
        ignore_index=True,
    )

    daily_series = build_daily_analysis_series(masked_daily, masked_fifteen)
    distributions = distribution_summary(daily_series)
    stationarity = stationarity_diagnostics(daily_series)
    dependence = dependence_diagnostics(daily_series)
    decomposition = decomposition_diagnostics(daily_series)
    lag_curves, lag_summary = daily_lag_diagnostics(daily_series)
    events = select_rain_events(daily_series)
    event_summary, event_matches = event_alignment_diagnostics(masked_fifteen, events)
    simulated, synthetic_diagnostics = synthetic_linear_process_diagnostics()

    _write_parquet_atomic(
        daily_series,
        PROCESSED_DIRECTORY / "phase3_daily_analysis_series.parquet",
    )
    _write_parquet_atomic(
        event_matches,
        PROCESSED_DIRECTORY / "phase3_event_alignment_pairs.parquet",
    )

    _write_csv(_configuration_table(), "analysis_configuration.csv")
    _write_csv(coverage, "coverage_missingness.csv")
    _write_csv(gaps, "gap_length_distribution.csv")
    _write_csv(distributions, "distribution_summary.csv")
    _write_csv(decomposition, "decomposition_diagnostics.csv")
    _write_csv(stationarity, "stationarity_diagnostics.csv")
    _write_csv(dependence, "acf_pacf_diagnostics.csv")
    _write_csv(lag_curves, "daily_lag_curves.csv")
    _write_csv(lag_summary, "daily_lag_summary.csv")
    _write_csv(events, "event_selection.csv")
    _write_csv(event_summary, "event_alignment_sensitivity.csv")
    _write_csv(synthetic_diagnostics, "synthetic_acf_pacf.csv")

    _write_figures(
        daily_series,
        decomposition,
        dependence,
        lag_curves,
        event_summary,
        simulated,
        synthetic_diagnostics,
    )


def _write_figures(
    daily_series: pd.DataFrame,
    decomposition: pd.DataFrame,
    dependence: pd.DataFrame,
    lag_curves: pd.DataFrame,
    event_summary: pd.DataFrame,
    simulated: pd.DataFrame,
    synthetic_diagnostics: pd.DataFrame,
) -> None:
    """Write the curated Phase 3 figure set from completed diagnostics."""

    plot_daily_coverage(
        daily_series, FIGURE_DIRECTORY / "01_daily_coverage_missingness.png"
    )
    plot_temporal_regimes(
        daily_series, FIGURE_DIRECTORY / "02_daily_levels_sensor_regimes.png"
    )
    plot_distributions(daily_series, FIGURE_DIRECTORY / "03_daily_distributions.png")
    plot_water_year_patterns(
        daily_series, FIGURE_DIRECTORY / "04_water_year_seasonality.png"
    )
    plot_representative_decomposition(
        daily_series, decomposition, FIGURE_DIRECTORY / "05_robust_stl_decomposition.png"
    )
    plot_acf_pacf(dependence, FIGURE_DIRECTORY / "06_daily_acf_pacf.png")
    plot_daily_lag_curves(lag_curves, FIGURE_DIRECTORY / "07_daily_lag_sensitivity.png")
    plot_event_sensitivity(
        event_summary, FIGURE_DIRECTORY / "08_event_alignment_sensitivity.png"
    )
    plot_synthetic_demo(
        simulated, synthetic_diagnostics, FIGURE_DIRECTORY / "09_synthetic_linear_processes.png"
    )
    print(f"Wrote curated figures: {FIGURE_DIRECTORY.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
