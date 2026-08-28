"""Aggregate Phase 4 forecast metrics without exposing observations."""

from __future__ import annotations

import math
from collections.abc import Iterable

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import acf

from geotech_ts.forecasting import BASELINE_COMPLEXITY, INTERVAL_LEVELS, model_specifications_table

METRIC_GROUPS = [
    "window_id",
    "target_id",
    "window_role",
    "stage",
    "model_id",
    "model_family",
    "horizon_days",
]


def _safe_root_mean_square(values: pd.Series) -> float:
    clean = values.dropna().to_numpy(dtype=float)
    return float(np.sqrt(np.mean(clean))) if len(clean) else math.nan


def aggregate_validation_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Calculate overall coverage and error metrics by model, stage, and horizon."""

    rows: list[dict[str, object]] = []
    for keys, group in predictions.groupby(METRIC_GROUPS, sort=True, dropna=False):
        successful = group.loc[group["status"].eq("ok")]
        core_count = int(group["core_eligible"].sum())
        row = dict(zip(METRIC_GROUPS, keys, strict=True))
        row.update(
            {
                "scheduled_attempt_count": len(group),
                "core_eligible_origin_count": core_count,
                "point_forecast_count": len(successful),
                "point_coverage_fraction": (
                    len(successful) / core_count if core_count else math.nan
                ),
                "mae": float(successful["absolute_error"].mean())
                if len(successful)
                else math.nan,
                "rmse": _safe_root_mean_square(successful["squared_error"]),
                "bias": float(successful["error"].mean()) if len(successful) else math.nan,
                "mase": float(successful["scaled_absolute_error"].mean())
                if len(successful)
                else math.nan,
                "median_absolute_error": float(successful["absolute_error"].median())
                if len(successful)
                else math.nan,
                "q95_absolute_error": float(successful["absolute_error"].quantile(0.95))
                if len(successful)
                else math.nan,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _error_summary(group: pd.DataFrame) -> dict[str, object]:
    return {
        "forecast_count": len(group),
        "mae": float(group["absolute_error"].mean()),
        "rmse": _safe_root_mean_square(group["squared_error"]),
        "bias": float(group["error"].mean()),
        "mase": float(group["scaled_absolute_error"].mean()),
    }


def stratified_validation_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Report water-year, season, movement, and early/late forecast performance."""

    successful = predictions.loc[predictions["status"].eq("ok")].copy()
    rows: list[dict[str, object]] = []
    dimensions = {
        "water_year": successful["target_water_year"].astype(str),
        "season": successful["season"].astype(str),
        "movement_subset": successful["high_movement"].map(
            {True: "training_q95_high_movement", False: "not_training_q95_high_movement"}
        ),
        "evaluation_half": successful["evaluation_half"].astype(str),
    }
    base_groups = [
        "window_id",
        "target_id",
        "stage",
        "model_id",
        "horizon_days",
    ]
    for dimension, values in dimensions.items():
        working = successful.assign(group_value=values)
        for keys, group in working.groupby([*base_groups, "group_value"], sort=True):
            row = dict(zip([*base_groups, "group_value"], keys, strict=True))
            row["dimension"] = dimension
            row.update(_error_summary(group))
            rows.append(row)
    columns = [
        *base_groups,
        "dimension",
        "group_value",
        "forecast_count",
        "mae",
        "rmse",
        "bias",
        "mase",
    ]
    return pd.DataFrame(rows)[columns]


def winkler_interval_score(
    observed: pd.Series,
    lower: pd.Series,
    upper: pd.Series,
    level: float,
) -> pd.Series:
    """Calculate the proper Winkler interval score at a declared central level."""

    alpha = 1 - level
    score = upper - lower
    score = score + (2 / alpha) * (lower - observed).clip(lower=0)
    score = score + (2 / alpha) * (observed - upper).clip(lower=0)
    return score


def interval_diagnostics(predictions: pd.DataFrame) -> pd.DataFrame:
    """Summarize empirical coverage, width, and interval score."""

    rows: list[dict[str, object]] = []
    successful = predictions.loc[predictions["status"].eq("ok")]
    for level in INTERVAL_LEVELS:
        label = int(level * 100)
        lower_column = f"lower_{label}"
        upper_column = f"upper_{label}"
        for keys, group in successful.groupby(METRIC_GROUPS, sort=True, dropna=False):
            available = group.dropna(subset=[lower_column, upper_column, "target_value"])
            row = dict(zip(METRIC_GROUPS, keys, strict=True))
            if available.empty:
                coverage = width = score = math.nan
            else:
                inside = available["target_value"].between(
                    available[lower_column], available[upper_column], inclusive="both"
                )
                coverage = float(inside.mean())
                width = float((available[upper_column] - available[lower_column]).mean())
                score = float(
                    winkler_interval_score(
                        available["target_value"],
                        available[lower_column],
                        available[upper_column],
                        level,
                    ).mean()
                )
            row.update(
                {
                    "nominal_level": level,
                    "point_forecast_count": len(group),
                    "interval_forecast_count": len(available),
                    "interval_availability_fraction": len(available) / len(group),
                    "empirical_coverage": coverage,
                    "average_width": width,
                    "mean_winkler_score": score,
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def residual_diagnostics(predictions: pd.DataFrame, maximum_lag: int = 10) -> pd.DataFrame:
    """Return out-of-sample residual ACF and heavy-tail diagnostics."""

    rows: list[dict[str, object]] = []
    successful = predictions.loc[predictions["status"].eq("ok")]
    for keys, group in successful.groupby(METRIC_GROUPS, sort=True, dropna=False):
        ordered = group.sort_values("origin_date")
        errors = ordered["error"].dropna().to_numpy(dtype=float)
        if len(errors) < 3 or np.std(errors) == 0:
            acf_values = np.full(maximum_lag + 1, np.nan)
            acf_values[0] = 1.0 if len(errors) else np.nan
        else:
            usable_lag = min(maximum_lag, len(errors) - 1)
            calculated = acf(errors, nlags=usable_lag, fft=False)
            acf_values = np.full(maximum_lag + 1, np.nan)
            acf_values[: len(calculated)] = calculated
        ljung_lag = min(maximum_lag, len(errors) // 5)
        if ljung_lag >= 1 and len(errors) > ljung_lag:
            ljung = acorr_ljungbox(errors, lags=[ljung_lag], return_df=True).iloc[0]
            ljung_statistic = float(ljung["lb_stat"])
            ljung_p_value = float(ljung["lb_pvalue"])
        else:
            ljung_statistic = ljung_p_value = math.nan
        series = pd.Series(errors)
        base = dict(zip(METRIC_GROUPS, keys, strict=True))
        for lag in range(maximum_lag + 1):
            rows.append(
                {
                    **base,
                    "forecast_count": len(errors),
                    "lag_in_origin_sequence": lag,
                    "residual_acf": float(acf_values[lag]),
                    "residual_bias": float(series.mean()) if len(series) else math.nan,
                    "residual_skewness": float(series.skew()) if len(series) >= 3 else math.nan,
                    "residual_excess_kurtosis": (
                        float(series.kurt()) if len(series) >= 4 else math.nan
                    ),
                    "median_absolute_error": (
                        float(series.abs().median()) if len(series) else math.nan
                    ),
                    "q95_absolute_error": (
                        float(series.abs().quantile(0.95)) if len(series) else math.nan
                    ),
                    "ljung_box_lag": ljung_lag,
                    "ljung_box_statistic": ljung_statistic,
                    "ljung_box_p_value": ljung_p_value,
                    "ljung_box_caveat": (
                        "approximate_with_skipped_origins_overlap_selection_and_heavy_tails"
                    ),
                }
            )
    return pd.DataFrame(rows)


def model_coverage_failures(predictions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate every success, skip, fit failure, and forecast failure."""

    groups = [
        "window_id",
        "target_id",
        "stage",
        "model_id",
        "model_family",
        "horizon_days",
        "status",
    ]
    counts = predictions.groupby(groups, sort=True, dropna=False).size().rename("attempt_count")
    result = counts.reset_index()
    totals = result.groupby(groups[:-1], sort=False)["attempt_count"].transform("sum")
    result["fraction_of_scheduled_attempts"] = result["attempt_count"] / totals
    return result


def parameter_stability(parameters: pd.DataFrame) -> pd.DataFrame:
    """Summarize coefficient behavior across rolling origins."""

    columns = ["window_id", "target_id", "stage", "model_id", "parameter"]
    if parameters.empty:
        return pd.DataFrame(
            columns=[
                *columns,
                "fit_count",
                "median",
                "q25",
                "q75",
                "minimum",
                "maximum",
                "converged_fraction",
            ]
        )
    rows = []
    for keys, group in parameters.groupby(columns, sort=True):
        values = group["parameter_value"].astype(float)
        row = dict(zip(columns, keys, strict=True))
        row.update(
            {
                "fit_count": len(values),
                "median": float(values.median()),
                "q25": float(values.quantile(0.25)),
                "q75": float(values.quantile(0.75)),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "converged_fraction": float(group["converged"].mean()),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def moving_block_mean_ci(
    values: Iterable[float],
    block_length: int = 3,
    replicates: int = 1000,
    seed: int = 170,
) -> tuple[float, float]:
    """Return a deterministic dependence-aware percentile interval for a mean."""

    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    n = len(array)
    if n < max(10, 2 * block_length):
        return math.nan, math.nan
    block = min(block_length, n)
    starts = np.arange(n - block + 1)
    blocks_needed = math.ceil(n / block)
    rng = np.random.default_rng(seed)
    means = np.empty(replicates)
    for replicate in range(replicates):
        chosen = rng.choice(starts, size=blocks_needed, replace=True)
        sample = np.concatenate([array[start : start + block] for start in chosen])[:n]
        means[replicate] = sample.mean()
    return tuple(float(value) for value in np.quantile(means, [0.025, 0.975]))


def forecast_comparison_uncertainty(predictions: pd.DataFrame) -> pd.DataFrame:
    """Compare absolute errors with zero change on identical origins."""

    successful = predictions.loc[predictions["status"].eq("ok")].copy()
    keys = ["window_id", "target_id", "stage", "horizon_days"]
    rows = []
    for group_keys, group in successful.groupby(keys, sort=True):
        zero = group.loc[group["model_id"].eq("zero_change"), [
            "origin_date",
            "target_date",
            "absolute_error",
        ]].rename(columns={"absolute_error": "zero_absolute_error"})
        for model_id, candidate in group.groupby("model_id", sort=True):
            paired = candidate[["origin_date", "target_date", "absolute_error"]].merge(
                zero,
                on=["origin_date", "target_date"],
                how="inner",
                validate="one_to_one",
            )
            difference = paired["absolute_error"] - paired["zero_absolute_error"]
            ci_low, ci_high = moving_block_mean_ci(difference)
            row = dict(zip(keys, group_keys, strict=True))
            row.update(
                {
                    "model_id": model_id,
                    "reference_model_id": "zero_change",
                    "common_origin_count": len(paired),
                    "mean_absolute_error_difference": (
                        float(difference.mean()) if len(difference) else math.nan
                    ),
                    "block_length_origins": 3,
                    "bootstrap_replicates": 1000,
                    "bootstrap_seed": 170,
                    "difference_ci_low": ci_low,
                    "difference_ci_high": ci_high,
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)


def _complexity_map() -> dict[str, int]:
    table = model_specifications_table()
    result = dict(zip(table["model_id"], table["complexity_rank"], strict=True))
    result.update(BASELINE_COMPLEXITY)
    return {key: int(value) for key, value in result.items()}


def _successful_key_sets(
    group: pd.DataFrame, candidates: list[str]
) -> dict[str, set[tuple[pd.Timestamp, pd.Timestamp]]]:
    sets = {}
    for model_id in candidates:
        model = group.loc[group["model_id"].eq(model_id) & group["status"].eq("ok")]
        sets[model_id] = set(zip(model["origin_date"], model["target_date"], strict=True))
    return sets


def _mean_error_for_model(
    group: pd.DataFrame,
    model_id: str,
    common_keys: set[tuple[pd.Timestamp, pd.Timestamp]],
) -> float:
    selected = group.loc[group["model_id"].eq(model_id) & group["status"].eq("ok")].copy()
    selected["forecast_key"] = list(
        zip(selected["origin_date"], selected["target_date"], strict=True)
    )
    selected = selected.loc[selected["forecast_key"].isin(common_keys)]
    return float(selected["absolute_error"].mean()) if len(selected) else math.nan


def selection_decisions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Apply the frozen common-origin coverage, MAE, and complexity rule."""

    rows = []
    complexity = _complexity_map()
    primary = predictions.loc[
        predictions["window_id"].isin(
            ["middle_stable_2009_2016", "toe_pre_topple_long"]
        )
    ]
    group_columns = ["window_id", "target_id", "horizon_days"]
    for keys, all_stages in primary.groupby(group_columns, sort=True):
        selection = all_stages.loc[all_stages["stage"].eq("selection")]
        coverage_rows = []
        for model_id, model in selection.groupby("model_id", sort=True):
            core_count = int(model["core_eligible"].sum())
            point_count = int(model["status"].eq("ok").sum())
            coverage = point_count / core_count if core_count else 0.0
            coverage_rows.append((model_id, coverage, point_count, core_count))
        eligible = [row[0] for row in coverage_rows if row[1] >= 0.80]
        key_sets = _successful_key_sets(selection, eligible)
        common_keys = (
            set.intersection(*(key_sets[model] for model in eligible)) if eligible else set()
        )
        mae_by_model = {
            model: _mean_error_for_model(selection, model, common_keys) for model in eligible
        }
        finite = {model: value for model, value in mae_by_model.items() if np.isfinite(value)}
        if len(common_keys) < 30 or not finite:
            retained = "zero_change"
            reason = "insufficient_common_selection_origins_retain_zero"
            selected_mae = _mean_error_for_model(selection, retained, key_sets.get(retained, set()))
        else:
            best_mae = min(finite.values())
            tied = [
                model for model, value in finite.items() if value <= best_mae * 1.05
            ]
            retained = min(tied, key=lambda model: complexity[model])
            selected_mae = finite[retained]
            reason = "lowest_common_origin_mae_with_five_percent_complexity_tie_rule"

        evaluation = all_stages.loc[all_stages["stage"].eq("evaluation")]
        evaluation_summary = (
            evaluation.loc[evaluation["status"].eq("ok")]
            .groupby("model_id")["absolute_error"]
            .agg(["mean", "count"])
        )
        retained_eval_mae = (
            float(evaluation_summary.at[retained, "mean"])
            if retained in evaluation_summary.index
            else math.nan
        )
        best_eval_model = (
            str(evaluation_summary["mean"].idxmin()) if not evaluation_summary.empty else "none"
        )
        best_eval_mae = (
            float(evaluation_summary["mean"].min()) if not evaluation_summary.empty else math.nan
        )

        external = predictions.loc[
            predictions["window_id"].eq("toe_pre_topple_post_rain_resume")
            & predictions["target_id"].eq(keys[1])
            & predictions["horizon_days"].eq(keys[2])
            & predictions["model_id"].eq(retained)
            & predictions["status"].eq("ok")
        ]
        rows.append(
            {
                "window_id": keys[0],
                "target_id": keys[1],
                "horizon_days": keys[2],
                "retained_model_id": retained,
                "selection_reason": reason,
                "selection_eligible_candidates": ";".join(sorted(eligible)),
                "selection_common_origin_count": len(common_keys),
                "retained_selection_common_origin_mae": selected_mae,
                "retained_evaluation_mae": retained_eval_mae,
                "evaluation_best_observed_model_id": best_eval_model,
                "evaluation_best_observed_mae": best_eval_mae,
                "evaluation_does_not_revise_selection": True,
                "external_time_check_forecast_count": len(external),
                "external_time_check_retained_mae": (
                    float(external["absolute_error"].mean()) if len(external) else math.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def synthetic_leakage_demo(seed: int = 170) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Contrast random and chronological validation on a synthetic regime shift."""

    rng = np.random.default_rng(seed)
    sample_size = 300
    shift_start = 220
    values = rng.normal(0, 1, sample_size)
    values[shift_start:] += 5
    indices = np.arange(sample_size)

    chronological_train = indices[:210]
    chronological_test = indices[210:]
    random_train = np.sort(rng.choice(indices, size=210, replace=False))
    random_test = np.setdiff1d(indices, random_train)
    rows = []
    for design, train, test in (
        ("chronological_split", chronological_train, chronological_test),
        ("random_split_leaks_later_regime", random_train, random_test),
    ):
        prediction = float(values[train].mean())
        error = values[test] - prediction
        rows.append(
            {
                "data_origin": "synthetic_seed_170_not_usgs",
                "validation_design": design,
                "sample_size": sample_size,
                "regime_shift_step": shift_start,
                "training_count": len(train),
                "test_count": len(test),
                "training_includes_post_shift": bool(np.any(train >= shift_start)),
                "mae": float(np.mean(np.abs(error))),
                "rmse": float(np.sqrt(np.mean(error**2))),
                "bias": float(np.mean(error)),
            }
        )
    values_frame = pd.DataFrame(
        {
            "step": indices,
            "synthetic_value": values,
            "chronological_training": indices < 210,
            "post_shift": indices >= shift_start,
        }
    )
    return pd.DataFrame(rows), values_frame
