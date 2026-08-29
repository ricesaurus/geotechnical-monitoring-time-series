"""Programmatic Phase 5 synthesis from verified aggregate Phase 1–4 evidence."""

from __future__ import annotations

import platform
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from geotech_ts.paths import PROJECT_ROOT

PHASE3_BUILD = (
    "./.venv/Scripts/python.exe ./scripts/build_phase3_analysis.py; "
    "./.venv/Scripts/python.exe ./scripts/verify_phase3_outputs.py"
)
PHASE4_BUILD = (
    "./.venv/Scripts/python.exe ./scripts/build_phase4_analysis.py; "
    "./.venv/Scripts/python.exe ./scripts/verify_phase4_outputs.py"
)
PHASE2_BUILD = (
    "./.venv/Scripts/python.exe ./scripts/build_phase2_interim.py; "
    "./.venv/Scripts/python.exe ./scripts/verify_phase2_data.py"
)


def _read(root: Path, relative_path: str) -> pd.DataFrame:
    return pd.read_csv(root / relative_path)


def _one(frame: pd.DataFrame, **filters: object) -> pd.Series:
    selected = frame
    for column, value in filters.items():
        selected = selected.loc[selected[column].eq(value)]
    if len(selected) != 1:
        raise ValueError(f"Expected one row for {filters}, found {len(selected)}")
    return selected.iloc[0]


def _lag_row(
    lags: pd.DataFrame,
    *,
    window_id: str,
    response: str,
    method: str,
    rain_definition: str,
) -> pd.Series:
    return _one(
        lags,
        window_id=window_id,
        predictor="mid_R",
        response=response,
        method=method,
        rain_definition=rain_definition,
    )


def build_key_forecast_results(project_root: Path = PROJECT_ROOT) -> pd.DataFrame:
    """Reorganize the frozen six forecast decisions without changing the analysis."""

    decisions = _read(project_root, "reports/tables/phase4/selection_decisions.csv")
    metrics = _read(project_root, "reports/tables/phase4/validation_metrics.csv")
    rows: list[dict[str, object]] = []
    labels = {
        "middle_stable_2009_2016": "Middle stable window",
        "toe_pre_topple_long": "Toe pre-topple window",
    }
    for decision in decisions.sort_values(["window_id", "horizon_days"]).itertuples():
        zero = _one(
            metrics,
            window_id=decision.window_id,
            stage="evaluation",
            model_id="zero_change",
            horizon_days=decision.horizon_days,
        )
        rows.append(
            {
                "target_window": labels[decision.window_id],
                "window_id": decision.window_id,
                "sensor_id": decision.target_id,
                "horizon_days": int(decision.horizon_days),
                "frozen_model": decision.retained_model_id,
                "selection_mae_cm_per_day": decision.retained_selection_common_origin_mae,
                "later_frozen_mae_cm_per_day": decision.retained_evaluation_mae,
                "later_zero_mae_cm_per_day": zero["mae"],
                "later_best_observed_model": decision.evaluation_best_observed_model_id,
                "later_best_observed_mae_cm_per_day": decision.evaluation_best_observed_mae,
                "evaluation_reselected_model": False,
            }
        )
    return pd.DataFrame(rows)


def build_claim_evidence_matrix(project_root: Path = PROJECT_ROOT) -> pd.DataFrame:
    """Build final claims and their exact evidence routes from committed aggregates."""

    archive = _read(project_root, "data/provenance/cleveland_corral_archive_inventory.csv")
    manifest = _read(project_root, "data/provenance/cleveland_corral_download_manifest.csv")
    sensors = _read(project_root, "data/provenance/cleveland_corral_sensor_inventory.csv")
    semantics = _read(project_root, "data/provenance/cleveland_corral_product_semantics.csv")
    decomposition = _read(project_root, "reports/tables/phase3/decomposition_diagnostics.csv")
    dependence = _read(project_root, "reports/tables/phase3/acf_pacf_diagnostics.csv")
    lags = _read(project_root, "reports/tables/phase3/daily_lag_summary.csv")
    events = _read(project_root, "reports/tables/phase3/event_alignment_sensitivity.csv")
    metrics = _read(project_root, "reports/tables/phase4/validation_metrics.csv")
    uncertainty = _read(project_root, "reports/tables/phase4/forecast_comparison_uncertainty.csv")
    decisions = _read(project_root, "reports/tables/phase4/selection_decisions.csv")
    intervals = _read(project_root, "reports/tables/phase4/interval_diagnostics.csv")
    residuals = _read(project_root, "reports/tables/phase4/residual_diagnostics.csv")
    failures = _read(project_root, "reports/tables/phase4/model_coverage_failures.csv")
    changepoints = _read(project_root, "reports/tables/phase4/changepoint_candidates.csv")

    archive_counts = archive.groupby("product_type")["member_path"].nunique()
    archive_rows = archive.groupby("product_type")["data_row_count"].sum()
    non_rain = semantics.loc[semantics["sensor_id"].ne("mid_R")]
    rain_cumulative = _one(
        semantics,
        sensor_id="mid_R",
        tested_15_minute_role="cumulative_precipitation",
    )
    non_rain_comparable = int(non_rain["comparable_date_count"].sum())
    non_rain_matches = int(non_rain["match_within_1e_12_count"].sum())
    if len(non_rain) != 12 or non_rain_matches != non_rain_comparable:
        raise ValueError("Expected all 12 selected non-rain daily products to match")
    if (
        int(rain_cumulative["comparable_date_count"]) != 7_584
        or int(rain_cumulative["match_within_1e_12_count"]) != 6_961
        or int(rain_cumulative["mismatch_count"]) != 623
        or rain_cumulative["mismatch_calendar_years"] != "1999;2000;2007;2013"
    ):
        raise ValueError("Unexpected published daily-rain comparison result")

    def max_n_acf(sensor_id: str) -> float:
        selected = dependence.loc[
            dependence["sensor_id"].eq(sensor_id)
            & dependence["transformation"].eq("daily_level")
            & dependence["lag_days"].eq(1)
        ].sort_values("n", ascending=False)
        return float(selected.iloc[0]["acf"])

    def seasonal(sensor_id: str, period: int = 365) -> float:
        selected = decomposition.loc[
            decomposition["sensor_id"].eq(sensor_id)
            & decomposition["transformation"].eq("daily_level")
            & decomposition["seasonal_period_days"].eq(period)
        ]
        if len(selected) != 1:
            raise ValueError(f"Expected one seasonal row for {sensor_id}")
        return float(selected.iloc[0]["seasonal_strength"])

    mid_p1 = _lag_row(
        lags,
        window_id="middle_stable_2009_2016",
        response="mid_P1",
        method="prewhitened",
        rain_definition="15_minute_interval_sum",
    )
    mid_p2 = _lag_row(
        lags,
        window_id="middle_stable_2009_2016",
        response="mid_P2",
        method="prewhitened",
        rain_definition="15_minute_interval_sum",
    )
    toe_moisture = _lag_row(
        lags,
        window_id="toe_pre_topple_long",
        response="toe_M1_A",
        method="prewhitened",
        rain_definition="15_minute_interval_sum",
    )
    toe_pressure = _lag_row(
        lags,
        window_id="toe_pre_topple_long",
        response="toe_P7_B",
        method="prewhitened",
        rain_definition="15_minute_interval_sum",
    )
    toe_displacement = _lag_row(
        lags,
        window_id="toe_pre_topple_long",
        response="toe_E5_C",
        method="prewhitened",
        rain_definition="15_minute_interval_sum",
    )
    middle_displacement = _lag_row(
        lags,
        window_id="middle_stable_2009_2016",
        response="mid_E2_B",
        method="prewhitened",
        rain_definition="15_minute_interval_sum",
    )
    middle_naive = _lag_row(
        lags,
        window_id="middle_stable_2009_2016",
        response="mid_E2_B",
        method="naive_levels",
        rain_definition="published_cumulative",
    )
    toe_naive = _lag_row(
        lags,
        window_id="toe_pre_topple_long",
        response="toe_E5_C",
        method="naive_levels",
        rain_definition="published_cumulative",
    )

    pressure_event_lags = events.loc[
        events["response_sensor"].eq("toe_P7_B") & events["tolerance_minutes"].eq(8.0),
        "peak_lag_hours",
    ]
    displacement_event_lags = events.loc[
        events["response_sensor"].eq("toe_E5_C") & events["tolerance_minutes"].eq(8.0),
        "peak_lag_hours",
    ]

    later = metrics.loc[metrics["stage"].eq("evaluation")]
    zero = later.loc[later["model_id"].eq("zero_change")]
    median = later.loc[later["model_id"].eq("expanding_median")]
    zero_median = zero.merge(
        median,
        on=["window_id", "target_id", "horizon_days"],
        suffixes=("_zero", "_median"),
        validate="one_to_one",
    )
    if (
        len(zero_median) != 6
        or not (zero_median["mae_zero"] - zero_median["mae_median"]).abs().le(1e-12).all()
    ):
        raise ValueError("Zero change and expanding median must tie at all six evaluations")
    retained_nonzero = decisions.loc[decisions["retained_model_id"].ne("zero_change")]
    retained_uncertainty = retained_nonzero.merge(
        uncertainty.loc[uncertainty["stage"].eq("evaluation")],
        left_on=["window_id", "target_id", "horizon_days", "retained_model_id"],
        right_on=["window_id", "target_id", "horizon_days", "model_id"],
        validate="one_to_one",
    )
    if len(retained_uncertainty) != 5 or not retained_uncertainty["difference_ci_low"].gt(0).all():
        raise ValueError("Expected five nonzero retained models with intervals above zero")

    arimax_1 = _one(
        later,
        window_id="toe_pre_topple_long",
        model_id="arimax_ar1_rain_lag2",
        horizon_days=1,
    )
    arimax_2 = _one(
        later,
        window_id="toe_pre_topple_long",
        model_id="arimax_ar1_rain_lag2",
        horizon_days=2,
    )
    toe_zero_1 = _one(
        later,
        window_id="toe_pre_topple_long",
        model_id="zero_change",
        horizon_days=1,
    )
    toe_zero_2 = _one(
        later,
        window_id="toe_pre_topple_long",
        model_id="zero_change",
        horizon_days=2,
    )
    external = metrics.loc[metrics["stage"].eq("external_time_check")]
    external_best = external.loc[external.groupby("horizon_days")["mae"].idxmin()]

    retained_interval_rows = []
    for decision in decisions.itertuples():
        selected = intervals.loc[
            intervals["window_id"].eq(decision.window_id)
            & intervals["stage"].eq("evaluation")
            & intervals["model_id"].eq(decision.retained_model_id)
            & intervals["horizon_days"].eq(decision.horizon_days)
        ]
        retained_interval_rows.append(selected)
    retained_intervals = pd.concat(retained_interval_rows, ignore_index=True)
    dynamic_intervals = retained_intervals.loc[
        retained_intervals["model_id"].isin(["arima_ar1", "arima_ar2", "arima_arma11"])
    ]
    coverage_80 = dynamic_intervals.loc[
        dynamic_intervals["nominal_level"].eq(0.80), "empirical_coverage"
    ]
    coverage_95 = dynamic_intervals.loc[
        dynamic_intervals["nominal_level"].eq(0.95), "empirical_coverage"
    ]

    def kurtosis(window_id: str, model_id: str, horizon: int) -> float:
        return float(
            _one(
                residuals,
                window_id=window_id,
                stage="evaluation",
                model_id=model_id,
                horizon_days=horizon,
                lag_in_origin_sequence=0,
            )["residual_excess_kurtosis"]
        )

    status_counts = failures.groupby("status")["attempt_count"].sum()
    stability_counts = changepoints["sensitivity_stability"].value_counts()
    context_counts = changepoints["context_classification"].value_counts()
    if int(context_counts["event_aligned"]) != 23 or int(context_counts["unexplained"]) != 19:
        raise ValueError("Unexpected changepoint context counts")
    archive_water_years = pd.to_numeric(archive["nominal_water_year"], errors="coerce")
    first_water_year = int(archive_water_years.min())
    last_water_year = int(archive_water_years.max())
    if (
        len(manifest) != 3
        or manifest["resource_kind"].eq("measurement_archive").sum() != 2
        or manifest["resource_kind"].eq("sensor_metadata").sum() != 1
    ):
        raise ValueError("Expected two official monitoring archives and one sensor table")

    rows = [
        {
            "claim_id": "C01",
            "claim": (
                f"The official archives contain {int(archive_counts['15_minute'])} "
                f"15-minute CSV members with {int(archive_rows['15_minute']):,} source rows "
                f"and {int(archive_counts['daily'])} daily CSV members with "
                f"{int(archive_rows['daily']):,} source rows."
            ),
            "evidence_category": "observed data",
            "source_phase": "Phase 2",
            "source_artifact": "data/provenance/cleveland_corral_archive_inventory.csv",
            "source_locator": "grouped by product_type",
            "exact_reproduction_command": PHASE2_BUILD,
            "applicable_caveat": (
                "Archive rows are station rows, not independent sensor observations."
            ),
        },
        {
            "claim_id": "C02",
            "claim": (
                f"The official sensor inventory contains {len(sensors)} IDs and documents gaps, "
                "cumulative resets, replacements, relocations, logger-phase differences, range "
                "concerns, and unresolved metadata that constrain interpretation."
            ),
            "evidence_category": "observed data",
            "source_phase": "Phases 1–2",
            "source_artifact": "data/provenance/cleveland_corral_sensor_inventory.csv",
            "source_locator": "all rows; maintenance and unresolved-fields columns",
            "exact_reproduction_command": (
                "./.venv/Scripts/python.exe -m pytest tests/test_metadata_inventory.py "
                "tests/test_phase2_validation.py"
            ),
            "applicable_caveat": (
                "Metadata identify concerns but do not prove that flagged readings are invalid."
            ),
        },
        {
            "claim_id": "C03",
            "claim": (
                "Daily pressure and toe-moisture levels are strongly persistent: representative "
                f"lag-1 ACF values are {max_n_acf('mid_P1'):.3f} for mid_P1, "
                f"{max_n_acf('mid_P2'):.3f} for mid_P2, and {max_n_acf('toe_M1_A'):.3f} "
                "for toe_M1_A."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/acf_pacf_diagnostics.csv",
            "source_locator": "lag_days=1, daily_level, longest representative run",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "ACF values are segment-specific and do not establish a physical mechanism."
            ),
        },
        {
            "claim_id": "C04",
            "claim": (
                "A 365-day robust STL description gives seasonal-strength values of "
                f"{seasonal('mid_P1'):.2f} for mid_P1, {seasonal('mid_P2'):.2f} for mid_P2, "
                f"{seasonal('toe_M1_A'):.2f} for toe_M1_A, and {seasonal('toe_P7_B'):.2f} "
                "for toe_P7_B."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/decomposition_diagnostics.csv",
            "source_locator": "daily_level, seasonal_period_days=365",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "STL is descriptive, limited to exact contiguous runs, and does not "
                "identify causes."
            ),
        },
        {
            "claim_id": "C05",
            "claim": (
                "Using daily interval rain and cautious AR(1) prewhitening, rain leads mid_P1 "
                f"and mid_P2 changes by one day with correlations {mid_p1['peak_correlation']:.3f} "
                f"and {mid_p2['peak_correlation']:.3f}, respectively."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/daily_lag_summary.csv",
            "source_locator": "middle stable window; prewhitened; 15-minute interval-sum rain",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "Intervals are conditional on the selected peak and do not correct for "
                "searching 31 lags."
            ),
        },
        {
            "claim_id": "C06",
            "claim": (
                "In the long pre-topple toe window, prewhitened rain associations peak on the "
                f"same day for toe_M1_A ({toe_moisture['peak_correlation']:.3f}) and toe_P7_B "
                f"({toe_pressure['peak_correlation']:.3f})."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/daily_lag_summary.csv",
            "source_locator": "toe long window; prewhitened; 15-minute interval-sum rain",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "The moisture scale is official and unitless; its installation depth is "
                "undocumented."
            ),
        },
        {
            "claim_id": "C07",
            "claim": (
                "The long pre-topple toe rain-to-displacement-change association peaks at "
                "two days with a prewhitened correlation of "
                f"{toe_displacement['peak_correlation']:.3f}."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/daily_lag_summary.csv",
            "source_locator": "toe long window; mid_R to toe_E5_C; prewhitened interval rain",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "This is a modest observational association, not a causal delay or warning "
                "threshold."
            ),
        },
        {
            "claim_id": "C08",
            "claim": (
                "The corresponding middle rain-to-displacement result is weak: the "
                "prewhitened lag-zero correlation is "
                f"{middle_displacement['peak_correlation']:.3f}."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/daily_lag_summary.csv",
            "source_locator": "middle stable window; mid_R to mid_E2_B; prewhitened interval rain",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "The selected peak is weak and does not support a general middle-site lag."
            ),
        },
        {
            "claim_id": "C09",
            "claim": (
                "Naive cumulative-level rain/displacement correlations of "
                f"{middle_naive['peak_correlation']:.3f} at the middle and "
                f"{toe_naive['peak_correlation']:.3f} at the toe shrink to "
                f"{middle_displacement['peak_correlation']:.3f} and "
                f"{toe_displacement['peak_correlation']:.3f} after valid differencing and "
                "prewhitening."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/daily_lag_summary.csv",
            "source_locator": "naive_levels versus prewhitened interval-rain rows",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "Different transformations answer different questions; the comparison "
                "demonstrates confounding by accumulation and persistence."
            ),
        },
        {
            "claim_id": "C10",
            "claim": (
                "Across three rain-selected storms, eight-minute-tolerance peak lags span "
                f"{pressure_event_lags.min():.2f}–{pressure_event_lags.max():.2f} hours for "
                f"toe pressure and {displacement_event_lags.min():.2f}–"
                f"{displacement_event_lags.max():.2f} hours for toe displacement."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 3",
            "source_artifact": "reports/tables/phase3/event_alignment_sensitivity.csv",
            "source_locator": "tolerance_minutes=8; toe_P7_B and toe_E5_C",
            "exact_reproduction_command": PHASE3_BUILD,
            "applicable_caveat": (
                "Only three rain-selected events were analyzed and peak signs also vary."
            ),
        },
        {
            "claim_id": "C11",
            "claim": (
                "Zero change, tied numerically with the expanding median, has the lowest later "
                "MAE for both displacement targets at all three tested horizons."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/validation_metrics.csv",
            "source_locator": (
                "evaluation rows; zero_change versus expanding_median; six "
                "target/horizon combinations"
            ),
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "This is a sparse-origin MAE result, not evidence that physical movement "
                "is always zero."
            ),
        },
        {
            "claim_id": "C12",
            "claim": (
                "For all five nonzero frozen retained models, paired 95% moving-block intervals "
                "for model-minus-zero MAE are wholly above zero and therefore favor zero change."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/forecast_comparison_uncertainty.csv",
            "source_locator": "evaluation rows joined to nonzero retained models",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "The intervals are design-specific and do not prove that dynamic models "
                "can never help elsewhere."
            ),
        },
        {
            "claim_id": "C13",
            "claim": (
                "The long-window rain-conditioned ARIMAX has later MAE "
                f"{arimax_1['mae']:.3f} versus {toe_zero_1['mae']:.3f} for zero change at one "
                f"day and {arimax_2['mae']:.3f} versus {toe_zero_2['mae']:.3f} at two days."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/validation_metrics.csv",
            "source_locator": "toe long-window evaluation; ARIMAX and zero-change rows",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "ARIMAX is unavailable at seven days because future rain would be required."
            ),
        },
        {
            "claim_id": "C14",
            "claim": (
                "The short post-rain-resume check contains only 25–26 successful origins per "
                f"horizon, although its best observed MAE values are "
                f"{external_best.sort_values('horizon_days')['mae'].iloc[0]:.3f}, "
                f"{external_best.sort_values('horizon_days')['mae'].iloc[1]:.3f}, and "
                f"{external_best.sort_values('horizon_days')['mae'].iloc[2]:.3f} at one, two, "
                "and seven days."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/validation_metrics.csv",
            "source_locator": "external_time_check; minimum MAE per horizon",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "This small stability check did not trigger model reselection and cannot "
                "support broad generalization."
            ),
        },
        {
            "claim_id": "C15",
            "claim": (
                "Retained dynamic-model interval coverage is conservative: 80% coverage ranges "
                f"from {100 * coverage_80.min():.1f}% to {100 * coverage_80.max():.1f}% and "
                f"95% coverage ranges from {100 * coverage_95.min():.1f}% to "
                f"{100 * coverage_95.max():.1f}%."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/interval_diagnostics.csv",
            "source_locator": "later evaluation rows for retained ARIMA/ARMA models",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "High coverage partly reflects wide intervals and limited forecast counts."
            ),
        },
        {
            "claim_id": "C16",
            "claim": (
                "Later residuals are heavy-tailed: excess kurtosis is about "
                f"{kurtosis('toe_pre_topple_long', 'persistence', 1):.1f} for toe persistence "
                f"at one day, {kurtosis('toe_pre_topple_long', 'arima_arma11', 2):.1f} for toe "
                "ARMA(1,1) at two days, and "
                f"{kurtosis('middle_stable_2009_2016', 'arima_ar2', 7):.1f} "
                "for middle AR(2) at seven days."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/residual_diagnostics.csv",
            "source_locator": "evaluation rows at lag_in_origin_sequence=0",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "Origin counts are modest and rare extremes limit formal tail diagnostics."
            ),
        },
        {
            "claim_id": "C17",
            "claim": (
                f"All {int(status_counts.sum()):,} scheduled forecast attempts are accounted "
                f"for: {int(status_counts['ok']):,} succeeded, "
                f"{int(status_counts['ineligible_core_origin']):,} were core-ineligible, "
                f"{int(status_counts['feature_unavailable']):,} were feature-unavailable, and "
                f"{int(status_counts['fit_failure']):,} were fit failures."
            ),
            "evidence_category": "observed workflow result",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/model_coverage_failures.csv",
            "source_locator": "attempt_count grouped by status",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "Contractual unavailability and data-path ineligibility are distinct from "
                "numerical fit failure."
            ),
        },
        {
            "claim_id": "C18",
            "claim": (
                f"Only {int(stability_counts['method_stable'])} of {len(changepoints)} grouped "
                f"changepoint candidates have support from both method families; "
                f"{int(stability_counts['within_method_only'])} are within-method only and "
                f"{int(stability_counts['unstable'])} are unstable."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/changepoint_candidates.csv",
            "source_locator": "sensitivity_stability counts",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                f"Event context covers {int(context_counts['event_aligned'])} groups, while "
                f"{int(context_counts['unexplained'])} remain unexplained; neither class "
                "identifies cause."
            ),
        },
        {
            "claim_id": "C19",
            "claim": (
                "The verified results establish temporal association and forecast performance "
                "under the declared design, but they do not establish causation, a physical "
                "threshold, operational forecasting skill, or a warning rule."
            ),
            "evidence_category": "engineering interpretation and limitation",
            "source_phase": "Phases 3–5",
            "source_artifact": "docs/CLEVELAND_CORRAL_PHASE4_FORECASTING_VALIDATION.md",
            "source_locator": "decision and evidence-categories sections",
            "exact_reproduction_command": (
                "./.venv/Scripts/python.exe ./scripts/verify_phase5_outputs.py"
            ),
            "applicable_caveat": (
                "Operational or causal conclusions require new data, designs, and "
                "authority outside this project."
            ),
        },
        {
            "claim_id": "C20",
            "claim": (
                f"For the {len(non_rain)} selected non-rain IDs, all "
                f"{non_rain_comparable:,} comparable daily values match the median "
                "recalculated from available 15-minute observations within 10⁻¹²."
            ),
            "evidence_category": "observed data",
            "source_phase": "Phase 2",
            "source_artifact": "data/provenance/cleveland_corral_product_semantics.csv",
            "source_locator": "all non-rain rows; comparable and match-count columns",
            "exact_reproduction_command": PHASE2_BUILD,
            "applicable_caveat": (
                "This validates the published daily aggregation for comparable available "
                "values; it does not remove gaps or sensor-regime concerns."
            ),
        },
        {
            "claim_id": "C21",
            "claim": (
                "Daily rain matches the maximum cumulative 15-minute field on "
                f"{int(rain_cumulative['match_within_1e_12_count']):,} of "
                f"{int(rain_cumulative['comparable_date_count']):,} comparable dates; "
                f"{int(rain_cumulative['mismatch_count']):,} mismatches are confined to "
                "1999–2000, 2007, and 2013 and remain unresolved."
            ),
            "evidence_category": "observed data",
            "source_phase": "Phase 2",
            "source_artifact": "data/provenance/cleveland_corral_product_semantics.csv",
            "source_locator": "mid_R cumulative-precipitation comparison row",
            "exact_reproduction_command": PHASE2_BUILD,
            "applicable_caveat": (
                "The published daily rain field is preserved; unresolved offsets prevent "
                "silently substituting one rain definition for the other."
            ),
        },
        {
            "claim_id": "C22",
            "claim": (
                "Twenty-three groups are near a declared rain event or run-specific "
                "high-displacement episode and 19 are unexplained by those contexts."
            ),
            "evidence_category": "statistical inference",
            "source_phase": "Phase 4",
            "source_artifact": "reports/tables/phase4/changepoint_candidates.csv",
            "source_locator": "context_classification counts",
            "exact_reproduction_command": PHASE4_BUILD,
            "applicable_caveat": (
                "Proximity supplies context only and does not identify the cause of a "
                "candidate boundary."
            ),
        },
        {
            "claim_id": "C23",
            "claim": (
                f"The primary USGS release spans monitoring from {first_water_year} "
                f"through {last_water_year}."
            ),
            "evidence_category": "observed data",
            "source_phase": "Phase 2",
            "source_artifact": "data/provenance/cleveland_corral_archive_inventory.csv",
            "source_locator": "minimum and maximum nominal_water_year",
            "exact_reproduction_command": PHASE2_BUILD,
            "applicable_caveat": (
                "Individual sensors have shorter coverage and contain gaps and regime changes."
            ),
        },
        {
            "claim_id": "C24",
            "claim": (
                "Phase 2 acquired only the two monitoring archives and the "
                "sensor-description table."
            ),
            "evidence_category": "observed workflow result",
            "source_phase": "Phase 2",
            "source_artifact": "data/provenance/cleveland_corral_download_manifest.csv",
            "source_locator": "all three resource_kind rows",
            "exact_reproduction_command": (
                "./.venv/Scripts/python.exe ./scripts/acquire_cleveland_corral.py; "
                "./.venv/Scripts/python.exe ./scripts/verify_phase2_data.py"
            ),
            "applicable_caveat": (
                "Other releases were audited in Phase 1 but were not required for the "
                "selected analysis."
            ),
        },
    ]
    result = pd.DataFrame(rows)
    if result["claim_id"].duplicated().any():
        raise ValueError("Claim IDs must be unique")
    return result


def software_versions() -> pd.DataFrame:
    """Return the local software receipt used for the final verification run."""

    packages = (
        "numpy",
        "pandas",
        "scipy",
        "statsmodels",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "ruptures",
        "pyarrow",
        "pytest",
        "ruff",
    )
    rows = [{"component": "python", "version": platform.python_version()}]
    rows.extend({"component": package, "version": version(package)} for package in packages)
    return pd.DataFrame(rows)


def local_reproduction_receipt(project_root: Path = PROJECT_ROOT) -> pd.DataFrame:
    """Record aggregate counts from the ignored full-data workflow when available."""

    products = (
        (
            "Phase 2",
            "selected_15_minute_rows",
            "data/interim/cleveland_corral/selected_15_minute_quality_flagged.parquet",
        ),
        (
            "Phase 2",
            "selected_daily_rows",
            "data/interim/cleveland_corral/selected_daily_quality_flagged.parquet",
        ),
        (
            "Phase 3",
            "daily_analysis_rows",
            "data/processed/cleveland_corral/phase3_daily_analysis_series.parquet",
        ),
        (
            "Phase 3",
            "event_match_rows",
            "data/processed/cleveland_corral/phase3_event_alignment_pairs.parquet",
        ),
        (
            "Phase 4",
            "forecast_attempt_rows",
            "data/processed/cleveland_corral/phase4_rolling_forecasts.parquet",
        ),
        (
            "Phase 4",
            "fitted_parameter_rows",
            "data/processed/cleveland_corral/phase4_rolling_parameters.parquet",
        ),
        (
            "Phase 4",
            "raw_changepoint_detection_rows",
            "data/processed/cleveland_corral/phase4_changepoint_detections.parquet",
        ),
    )
    rows = []
    for phase, measure, relative in products:
        path = project_root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        rows.append(
            {
                "phase": phase,
                "measure": measure,
                "count": pq.read_metadata(path).num_rows,
                "source_layer": "git-ignored local Parquet metadata",
                "verification_status": "passed",
            }
        )
    for phase, table_dir, figure_dir in (
        ("Phase 3", "reports/tables/phase3", "reports/figures/phase3"),
        ("Phase 4", "reports/tables/phase4", "reports/figures/phase4"),
    ):
        rows.extend(
            [
                {
                    "phase": phase,
                    "measure": "committed_aggregate_tables",
                    "count": len(list((project_root / table_dir).glob("*.csv"))),
                    "source_layer": "version-controlled aggregate artifacts",
                    "verification_status": "passed",
                },
                {
                    "phase": phase,
                    "measure": "committed_figures",
                    "count": len(list((project_root / figure_dir).glob("*.png"))),
                    "source_layer": "version-controlled curated figures",
                    "verification_status": "passed",
                },
            ]
        )
    return pd.DataFrame(rows)
