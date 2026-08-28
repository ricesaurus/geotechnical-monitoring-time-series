"""Leakage-free rolling forecasts for Cleveland Corral Phase 4.

The public functions preserve the Phase 3 target mask on a complete calendar.  Missing
targets remain missing states.  Observation-bearing results belong only in the ignored
processed-data layer.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.tsa.statespace.sarimax import SARIMAX

HORIZONS = (1, 2, 7)
INTERVAL_LEVELS = (0.80, 0.95)
MINIMUM_CALENDAR_DAYS = 365
MINIMUM_TARGET_OBSERVATIONS = 300
MINIMUM_ARIMAX_EQUATIONS = 240
ORIGIN_STRIDE_DAYS = 14


@dataclass(frozen=True)
class ForecastWindow:
    """Predeclared target, date, origin, and selection-stage rules."""

    window_id: str
    target_id: str
    start: date
    end_exclusive: date
    anchor: date
    selection_end: date | None
    history_start: date
    role: str


FORECAST_WINDOWS = (
    ForecastWindow(
        "middle_stable_2009_2016",
        "mid_E2_B",
        date(2009, 2, 12),
        date(2016, 1, 22),
        date(2010, 2, 12),
        date(2013, 8, 31),
        date(2009, 2, 12),
        "primary",
    ),
    ForecastWindow(
        "toe_pre_topple_long",
        "toe_E5_C",
        date(2006, 11, 30),
        date(2016, 1, 22),
        date(2007, 11, 30),
        date(2012, 12, 31),
        date(2006, 11, 30),
        "secondary_primary_window",
    ),
    ForecastWindow(
        "toe_pre_topple_post_rain_resume",
        "toe_E5_C",
        date(2016, 1, 28),
        date(2017, 3, 16),
        date(2016, 1, 28),
        None,
        date(2006, 11, 30),
        "external_time_check",
    ),
)


@dataclass(frozen=True)
class ArimaSpec:
    """A fixed state-space ARIMA candidate."""

    model_id: str
    order: tuple[int, int, int]
    seasonal_order: tuple[int, int, int, int]
    target_ids: tuple[str, ...]
    complexity_rank: int
    rationale: str


ARIMA_SPECS = (
    ArimaSpec(
        "arima_mean",
        (0, 0, 0),
        (0, 0, 0, 0),
        ("mid_E2_B", "toe_E5_C"),
        5,
        "white-noise mean model",
    ),
    ArimaSpec(
        "arima_ar1",
        (1, 0, 0),
        (0, 0, 0, 0),
        ("mid_E2_B", "toe_E5_C"),
        6,
        "parsimonious short-memory model",
    ),
    ArimaSpec(
        "arima_ar2",
        (2, 0, 0),
        (0, 0, 0, 0),
        ("mid_E2_B", "toe_E5_C"),
        7,
        "limited second-lag model",
    ),
    ArimaSpec(
        "arima_arma11",
        (1, 0, 1),
        (0, 0, 0, 0),
        ("mid_E2_B", "toe_E5_C"),
        8,
        "limited ARMA alternative",
    ),
    ArimaSpec(
        "arima_ar1_weekly",
        (1, 0, 0),
        (1, 0, 0, 7),
        ("mid_E2_B",),
        9,
        "middle weekly-memory sensitivity",
    ),
)

BASELINE_COMPLEXITY = {
    "zero_change": 1,
    "expanding_median": 2,
    "persistence": 3,
    "prior_year_same_date": 4,
    "arimax_ar1_rain_lag2": 10,
}


class ArimaxFit(NamedTuple):
    coefficients: np.ndarray
    covariance: np.ndarray
    innovation_variance: float
    equation_count: int
    warning: str


def model_specifications_table() -> pd.DataFrame:
    """Return the versioned fixed model-candidate inventory."""

    rows: list[dict[str, object]] = [
        {
            "model_id": "zero_change",
            "family": "baseline",
            "order": "not_applicable",
            "seasonal_order": "not_applicable",
            "targets": "mid_E2_B;toe_E5_C",
            "horizons_days": "1;2;7",
            "exogenous_feature": "none",
            "complexity_rank": 1,
            "rationale": "target-scale no-change reference",
        },
        {
            "model_id": "expanding_median",
            "family": "baseline",
            "order": "not_applicable",
            "seasonal_order": "not_applicable",
            "targets": "mid_E2_B;toe_E5_C",
            "horizons_days": "1;2;7",
            "exogenous_feature": "none",
            "complexity_rank": 2,
            "rationale": "robust expanding historical center",
        },
        {
            "model_id": "persistence",
            "family": "baseline",
            "order": "not_applicable",
            "seasonal_order": "not_applicable",
            "targets": "mid_E2_B;toe_E5_C",
            "horizons_days": "1;2;7",
            "exogenous_feature": "none",
            "complexity_rank": 3,
            "rationale": "last eligible displacement change",
        },
        {
            "model_id": "prior_year_same_date",
            "family": "baseline",
            "order": "not_applicable",
            "seasonal_order": "not_applicable",
            "targets": "mid_E2_B;toe_E5_C",
            "horizons_days": "1;2;7",
            "exogenous_feature": "none",
            "complexity_rank": 4,
            "rationale": "exact prior-calendar-year seasonal reference",
        },
    ]
    for spec in ARIMA_SPECS:
        rows.append(
            {
                "model_id": spec.model_id,
                "family": "ARIMA",
                "order": str(spec.order),
                "seasonal_order": str(spec.seasonal_order),
                "targets": ";".join(spec.target_ids),
                "horizons_days": "1;2;7",
                "exogenous_feature": "none",
                "complexity_rank": spec.complexity_rank,
                "rationale": spec.rationale,
            }
        )
    rows.append(
        {
            "model_id": "arimax_ar1_rain_lag2",
            "family": "conditional_ARIMAX",
            "order": "(1,0,0)",
            "seasonal_order": "none",
            "targets": "toe_E5_C",
            "horizons_days": "1;2 (7 unavailable by contract)",
            "exogenous_feature": "eligible daily interval rain at target lag 2",
            "complexity_rank": 10,
            "rationale": "Phase 3 toe rain-to-change association at two days",
        }
    )
    return pd.DataFrame(rows)


def target_windows_table(daily_series: pd.DataFrame) -> pd.DataFrame:
    """Summarize declared windows without exposing observations."""

    rows = []
    for window in FORECAST_WINDOWS:
        selected = daily_series.loc[
            daily_series["sensor_id"].eq(window.target_id)
            & daily_series["transformation"].eq("daily_first_difference")
            & daily_series["local_date"].ge(pd.Timestamp(window.start))
            & daily_series["local_date"].lt(pd.Timestamp(window.end_exclusive))
        ]
        eligible = selected.loc[selected["analysis_eligible"] & selected["value"].notna()]
        rows.append(
            {
                "window_id": window.window_id,
                "target_id": window.target_id,
                "role": window.role,
                "start_date": window.start.isoformat(),
                "end_date_inclusive": (
                    pd.Timestamp(window.end_exclusive) - pd.Timedelta(days=1)
                ).date().isoformat(),
                "history_start_date": window.history_start.isoformat(),
                "origin_anchor_date": window.anchor.isoformat(),
                "origin_stride_days": ORIGIN_STRIDE_DAYS,
                "calendar_day_count": len(
                    pd.date_range(
                        window.start,
                        pd.Timestamp(window.end_exclusive) - pd.Timedelta(days=1),
                    )
                ),
                "eligible_target_change_count": len(eligible),
                "first_eligible_target_date": eligible["local_date"].min().date().isoformat(),
                "last_eligible_target_date": eligible["local_date"].max().date().isoformat(),
                "selection_end_date": (
                    window.selection_end.isoformat()
                    if window.selection_end is not None
                    else "not_applicable"
                ),
            }
        )
    return pd.DataFrame(rows)


def _water_year(timestamp: pd.Timestamp) -> int:
    return timestamp.year + 1 if timestamp.month >= 10 else timestamp.year


def _stage(window: ForecastWindow, origin: pd.Timestamp) -> str:
    if window.selection_end is None:
        return "external_time_check"
    return "selection" if origin.date() <= window.selection_end else "evaluation"


def _evaluation_half(window: ForecastWindow, origin: pd.Timestamp) -> str:
    if _stage(window, origin) != "evaluation":
        return "not_applicable"
    evaluation_start = pd.Timestamp(window.selection_end) + pd.Timedelta(days=1)
    evaluation_end = pd.Timestamp(window.end_exclusive) - pd.Timedelta(days=1)
    midpoint = evaluation_start + (evaluation_end - evaluation_start) / 2
    return "early" if origin <= midpoint else "late"


def _target_grid(daily_series: pd.DataFrame, window: ForecastWindow) -> pd.DataFrame:
    end = pd.Timestamp(window.end_exclusive) - pd.Timedelta(days=1)
    index = pd.date_range(window.history_start, end, freq="D", name="local_date")
    grid = pd.DataFrame(index=index)
    target = daily_series.loc[
        daily_series["sensor_id"].eq(window.target_id)
        & daily_series["transformation"].eq("daily_first_difference")
    ].drop_duplicates("local_date")
    target = target.set_index("local_date").reindex(index)
    grid["target_value"] = target["value"].where(target["analysis_eligible"].fillna(False))
    grid["target_eligible"] = target["analysis_eligible"].fillna(False).astype(bool)
    grid["target_segment"] = target["installation_segment_id"].astype("string")
    grid["target_water_year"] = target["water_year"].astype("Int64")

    rain = daily_series.loc[
        daily_series["sensor_id"].eq("mid_R")
        & daily_series["transformation"].eq("daily_interval_sum")
    ].drop_duplicates("local_date")
    rain = rain.set_index("local_date").reindex(index)
    grid["rain_value"] = rain["value"].where(rain["analysis_eligible"].fillna(False))
    grid["rain_eligible"] = rain["analysis_eligible"].fillna(False).astype(bool)
    grid["rain_segment"] = rain["installation_segment_id"].astype("string")
    if window.role == "external_time_check":
        interruption = grid.index.to_series().between(
            pd.Timestamp(2016, 1, 22),
            pd.Timestamp(window.start),
            inclusive="left",
        )
        grid.loc[interruption.to_numpy(), "target_value"] = np.nan
        grid.loc[interruption.to_numpy(), "target_eligible"] = False
    return grid


def scheduled_origins(window: ForecastWindow) -> pd.DatetimeIndex:
    """Return the exact, never-shifted contract origin schedule."""

    end = pd.Timestamp(window.end_exclusive) - pd.Timedelta(days=1)
    return pd.date_range(window.anchor, end, freq=f"{ORIGIN_STRIDE_DAYS}D")


def core_origin_eligible(
    grid: pd.DataFrame, origin: pd.Timestamp, horizon: int, window: ForecastWindow
) -> bool:
    """Require an unbroken eligible target path inside one regime and water year."""

    target_date = origin + pd.Timedelta(days=horizon)
    if origin < pd.Timestamp(window.start) or target_date >= pd.Timestamp(window.end_exclusive):
        return False
    path = grid.reindex(pd.date_range(origin, target_date, freq="D"))
    if len(path) != horizon + 1 or not path["target_eligible"].all():
        return False
    return bool(
        path["target_segment"].notna().all()
        and path["target_segment"].nunique() == 1
        and path["target_water_year"].notna().all()
        and path["target_water_year"].nunique() == 1
    )


def training_mase_scale(training: pd.DataFrame) -> float:
    """Compute a training-only exact-date naive scale without crossing boundaries."""

    valid = (
        training["target_eligible"]
        & training["target_value"].notna()
        & training["target_eligible"].shift(fill_value=False)
        & training["target_segment"].eq(training["target_segment"].shift())
        & training["target_water_year"].eq(training["target_water_year"].shift())
    )
    changes = training["target_value"].sub(training["target_value"].shift()).abs()[valid]
    if len(changes) < 30:
        return math.nan
    scale = float(changes.mean())
    return scale if scale > 0 else math.nan


def _base_record(
    window: ForecastWindow,
    origin: pd.Timestamp,
    horizon: int,
    model_id: str,
    family: str,
    grid: pd.DataFrame,
) -> dict[str, object]:
    target_date = origin + pd.Timedelta(days=horizon)
    stage = _stage(window, origin)
    record: dict[str, object] = {
        "window_id": window.window_id,
        "target_id": window.target_id,
        "window_role": window.role,
        "origin_date": origin,
        "target_date": target_date,
        "stage": stage,
        "evaluation_half": _evaluation_half(window, origin),
        "horizon_days": horizon,
        "model_id": model_id,
        "model_family": family,
        "core_eligible": core_origin_eligible(grid, origin, horizon, window),
        "status": "ineligible_core_origin",
        "interval_status": "not_available",
        "target_value": math.nan,
        "prediction": math.nan,
        "error": math.nan,
        "absolute_error": math.nan,
        "squared_error": math.nan,
        "mase_scale": math.nan,
        "scaled_absolute_error": math.nan,
        "training_calendar_days": 0,
        "training_target_count": 0,
        "high_movement_threshold": math.nan,
        "high_movement": False,
        "target_water_year": _water_year(target_date),
        "season": "wet" if target_date.month in {10, 11, 12, 1, 2, 3, 4} else "dry",
        "converged": False,
        "fit_warning": "none",
        "minimum_ar_root_modulus": math.nan,
        "minimum_ma_root_modulus": math.nan,
    }
    for level in INTERVAL_LEVELS:
        label = int(level * 100)
        record[f"lower_{label}"] = math.nan
        record[f"upper_{label}"] = math.nan
    return record


def _training_context(
    grid: pd.DataFrame, window: ForecastWindow, origin: pd.Timestamp
) -> tuple[pd.DataFrame, int, float, float]:
    training = grid.loc[pd.Timestamp(window.history_start) : origin].copy()
    count = int(training["target_value"].notna().sum())
    mase = training_mase_scale(training)
    threshold = (
        float(training["target_value"].dropna().abs().quantile(0.95)) if count else math.nan
    )
    return training, count, mase, threshold


def _finish_point_record(
    record: dict[str, object], prediction: float, grid: pd.DataFrame
) -> dict[str, object]:
    target_date = pd.Timestamp(record["target_date"])
    observed = float(grid.at[target_date, "target_value"])
    error = observed - float(prediction)
    scale = float(record["mase_scale"])
    record.update(
        {
            "status": "ok",
            "target_value": observed,
            "prediction": float(prediction),
            "error": error,
            "absolute_error": abs(error),
            "squared_error": error**2,
            "scaled_absolute_error": abs(error) / scale if np.isfinite(scale) else math.nan,
            "high_movement": bool(
                np.isfinite(float(record["high_movement_threshold"]))
                and abs(observed) > float(record["high_movement_threshold"])
            ),
        }
    )
    return record


def _baseline_prediction(
    model_id: str,
    training: pd.DataFrame,
    grid: pd.DataFrame,
    origin: pd.Timestamp,
    target_date: pd.Timestamp,
) -> tuple[float, str]:
    if model_id == "zero_change":
        return 0.0, "ok"
    if model_id == "persistence":
        value = grid.at[origin, "target_value"]
        return (float(value), "ok") if pd.notna(value) else (math.nan, "feature_unavailable")
    if model_id == "expanding_median":
        values = training["target_value"].dropna()
        return (
            (float(values.median()), "ok")
            if not values.empty
            else (math.nan, "insufficient_training")
        )
    if model_id == "prior_year_same_date":
        if target_date.month == 2 and target_date.day == 29:
            return math.nan, "feature_unavailable"
        prior_date = target_date - pd.DateOffset(years=1)
        if prior_date > origin or prior_date not in grid.index:
            return math.nan, "feature_unavailable"
        value = grid.at[prior_date, "target_value"]
        return (float(value), "ok") if pd.notna(value) else (math.nan, "feature_unavailable")
    raise ValueError(f"Unknown baseline: {model_id}")


def _minimum_root_modulus(roots: np.ndarray) -> float:
    finite = np.abs(np.asarray(roots, dtype=complex))
    return float(finite.min()) if len(finite) else math.nan


def _fit_arima(
    training: pd.DataFrame, spec: ArimaSpec
) -> tuple[object | None, list[tuple[str, float]], dict[str, object]]:
    endog = training["target_value"].astype(float).asfreq("D")
    diagnostics: dict[str, object] = {
        "status": "fit_failure",
        "converged": False,
        "fit_warning": "none",
        "minimum_ar_root_modulus": math.nan,
        "minimum_ma_root_modulus": math.nan,
    }
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = SARIMAX(
                endog,
                order=spec.order,
                seasonal_order=spec.seasonal_order,
                trend="c",
                enforce_stationarity=True,
                enforce_invertibility=True,
                simple_differencing=False,
            )
            result = model.fit(disp=False, maxiter=100, method="lbfgs")
        converged = bool(result.mle_retvals.get("converged", False))
        warning_text = " | ".join(str(item.message) for item in caught) or "none"
        diagnostics.update(
            {
                "status": "ok" if converged else "fit_failure",
                "converged": converged,
                "fit_warning": warning_text,
                "minimum_ar_root_modulus": _minimum_root_modulus(result.arroots),
                "minimum_ma_root_modulus": _minimum_root_modulus(result.maroots),
            }
        )
        parameters = [(str(name), float(value)) for name, value in result.params.items()]
        return (result if converged else None), parameters, diagnostics
    except Exception as error:  # statsmodels exposes several fit-specific exception types
        diagnostics["fit_warning"] = f"{type(error).__name__}: {error}"
        return None, [], diagnostics


def _fit_conditional_arimax(training: pd.DataFrame) -> ArimaxFit | None:
    equations = pd.DataFrame(index=training.index)
    equations["y"] = training["target_value"]
    equations["y_lag1"] = training["target_value"].shift(1)
    equations["rain_lag2"] = training["rain_value"].shift(2)
    equations = equations.dropna()
    if len(equations) < MINIMUM_ARIMAX_EQUATIONS:
        return None
    design = np.column_stack(
        [
            np.ones(len(equations)),
            equations["y_lag1"].to_numpy(dtype=float),
            equations["rain_lag2"].to_numpy(dtype=float),
        ]
    )
    response = equations["y"].to_numpy(dtype=float)
    if np.linalg.matrix_rank(design) < design.shape[1]:
        return None
    coefficients, _, _, _ = np.linalg.lstsq(design, response, rcond=None)
    residuals = response - design @ coefficients
    degrees = len(response) - design.shape[1]
    if degrees <= 0:
        return None
    innovation_variance = float(np.sum(residuals**2) / degrees)
    covariance = innovation_variance * np.linalg.inv(design.T @ design)
    phi = float(coefficients[1])
    warning = "none" if abs(phi) < 1 else "conditional_ar_coefficient_outside_unit_circle"
    return ArimaxFit(
        coefficients,
        covariance,
        innovation_variance,
        len(equations),
        warning,
    )


def _arimax_forecasts(
    fit: ArimaxFit, grid: pd.DataFrame, origin: pd.Timestamp
) -> dict[int, tuple[float, dict[int, tuple[float, float]]]]:
    constant, phi, beta = (float(value) for value in fit.coefficients)
    y_origin = grid.at[origin, "target_value"]
    rain_for_h1 = grid.at[origin - pd.Timedelta(days=1), "rain_value"]
    rain_for_h2 = grid.at[origin, "rain_value"]
    forecasts: dict[int, tuple[float, dict[int, tuple[float, float]]]] = {}
    if pd.notna(y_origin) and pd.notna(rain_for_h1):
        prediction_1 = constant + phi * float(y_origin) + beta * float(rain_for_h1)
        intervals_1: dict[int, tuple[float, float]] = {}
        variance_1 = fit.innovation_variance
        for level in INTERVAL_LEVELS:
            z_value = float(norm.ppf((1 + level) / 2))
            half_width = z_value * math.sqrt(max(variance_1, 0.0))
            intervals_1[int(level * 100)] = (
                prediction_1 - half_width,
                prediction_1 + half_width,
            )
        forecasts[1] = (prediction_1, intervals_1)
        if pd.notna(rain_for_h2):
            prediction_2 = constant + phi * prediction_1 + beta * float(rain_for_h2)
            intervals_2: dict[int, tuple[float, float]] = {}
            variance_2 = fit.innovation_variance * (1 + phi**2)
            for level in INTERVAL_LEVELS:
                z_value = float(norm.ppf((1 + level) / 2))
                half_width = z_value * math.sqrt(max(variance_2, 0.0))
                intervals_2[int(level * 100)] = (
                    prediction_2 - half_width,
                    prediction_2 + half_width,
                )
            forecasts[2] = (prediction_2, intervals_2)
    return forecasts


def _add_empirical_baseline_intervals(predictions: pd.DataFrame) -> pd.DataFrame:
    result = predictions.copy()
    baseline_ids = {
        "zero_change",
        "persistence",
        "expanding_median",
        "prior_year_same_date",
    }
    selected = result["model_id"].isin(baseline_ids) & result["status"].eq("ok")
    groups = result.loc[selected].groupby(
        ["window_id", "target_id", "model_id", "horizon_days"], sort=True
    )
    for _, group in groups:
        ordered = group.sort_values("origin_date")
        for row_index, row in ordered.iterrows():
            past = ordered.loc[
                ordered["target_date"].le(row["origin_date"])
                & ordered["origin_date"].lt(row["origin_date"]),
                "error",
            ].dropna()
            if len(past) < 30:
                result.at[row_index, "interval_status"] = "insufficient_past_calibration"
                continue
            prediction = float(row["prediction"])
            for level in INTERVAL_LEVELS:
                alpha = 1 - level
                lower_error, upper_error = past.quantile([alpha / 2, 1 - alpha / 2])
                label = int(level * 100)
                result.at[row_index, f"lower_{label}"] = prediction + float(lower_error)
                result.at[row_index, f"upper_{label}"] = prediction + float(upper_error)
            result.at[row_index, "interval_status"] = "ok_past_residuals"
    return result


def run_rolling_forecasts(
    daily_series: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run every declared rolling-origin attempt and return observation-bearing results."""

    prediction_rows: list[dict[str, object]] = []
    parameter_rows: list[dict[str, object]] = []
    baseline_ids = (
        "zero_change",
        "persistence",
        "expanding_median",
        "prior_year_same_date",
    )
    for window in FORECAST_WINDOWS:
        grid = _target_grid(daily_series, window)
        for origin in scheduled_origins(window):
            training, target_count, mase_scale, high_threshold = _training_context(
                grid, window, origin
            )
            training_days = len(training)
            enough_training = (
                training_days >= MINIMUM_CALENDAR_DAYS
                and target_count >= MINIMUM_TARGET_OBSERVATIONS
            )
            core_by_horizon = {
                horizon: core_origin_eligible(grid, origin, horizon, window)
                for horizon in HORIZONS
            }

            for model_id in baseline_ids:
                for horizon in HORIZONS:
                    record = _base_record(
                        window, origin, horizon, model_id, "baseline", grid
                    )
                    record.update(
                        {
                            "training_calendar_days": training_days,
                            "training_target_count": target_count,
                            "mase_scale": mase_scale,
                            "high_movement_threshold": high_threshold,
                            "converged": True,
                        }
                    )
                    if not core_by_horizon[horizon]:
                        prediction_rows.append(record)
                        continue
                    if not enough_training:
                        record["status"] = "insufficient_training"
                        prediction_rows.append(record)
                        continue
                    target_date = origin + pd.Timedelta(days=horizon)
                    point, status = _baseline_prediction(
                        model_id, training, grid, origin, target_date
                    )
                    if status != "ok":
                        record["status"] = status
                    else:
                        _finish_point_record(record, point, grid)
                    prediction_rows.append(record)

            for spec in ARIMA_SPECS:
                if window.target_id not in spec.target_ids:
                    continue
                records = {
                    horizon: _base_record(
                        window, origin, horizon, spec.model_id, "ARIMA", grid
                    )
                    for horizon in HORIZONS
                }
                for record in records.values():
                    record.update(
                        {
                            "training_calendar_days": training_days,
                            "training_target_count": target_count,
                            "mase_scale": mase_scale,
                            "high_movement_threshold": high_threshold,
                        }
                    )
                eligible_horizons = [
                    horizon for horizon in HORIZONS if core_by_horizon[horizon]
                ]
                if not eligible_horizons:
                    prediction_rows.extend(records.values())
                    continue
                if not enough_training:
                    for horizon in eligible_horizons:
                        records[horizon]["status"] = "insufficient_training"
                    prediction_rows.extend(records.values())
                    continue
                result, parameters, diagnostics = _fit_arima(training, spec)
                for record in records.values():
                    record.update(
                        {
                            "converged": diagnostics["converged"],
                            "fit_warning": diagnostics["fit_warning"],
                            "minimum_ar_root_modulus": diagnostics[
                                "minimum_ar_root_modulus"
                            ],
                            "minimum_ma_root_modulus": diagnostics[
                                "minimum_ma_root_modulus"
                            ],
                        }
                    )
                for parameter_name, parameter_value in parameters:
                    parameter_rows.append(
                        {
                            "window_id": window.window_id,
                            "target_id": window.target_id,
                            "origin_date": origin,
                            "stage": _stage(window, origin),
                            "model_id": spec.model_id,
                            "parameter": parameter_name,
                            "parameter_value": parameter_value,
                            "converged": diagnostics["converged"],
                        }
                    )
                if result is None:
                    for horizon in eligible_horizons:
                        records[horizon]["status"] = "fit_failure"
                    prediction_rows.extend(records.values())
                    continue
                try:
                    forecast = result.get_forecast(steps=max(HORIZONS))
                    means = np.asarray(forecast.predicted_mean, dtype=float)
                    intervals: dict[int, np.ndarray] = {}
                    for level in INTERVAL_LEVELS:
                        alpha = 1 - level
                        intervals[int(level * 100)] = np.asarray(
                            forecast.conf_int(alpha=alpha), dtype=float
                        )
                    for horizon in eligible_horizons:
                        record = records[horizon]
                        _finish_point_record(record, float(means[horizon - 1]), grid)
                        record["interval_status"] = "ok_model_based"
                        for label, bounds in intervals.items():
                            record[f"lower_{label}"] = float(bounds[horizon - 1, 0])
                            record[f"upper_{label}"] = float(bounds[horizon - 1, 1])
                except Exception as error:  # forecast failures vary by statsmodels version
                    for horizon in eligible_horizons:
                        records[horizon]["status"] = "forecast_failure"
                        records[horizon]["fit_warning"] = (
                            f"{records[horizon]['fit_warning']} | "
                            f"{type(error).__name__}: {error}"
                        )
                prediction_rows.extend(records.values())

            if window.target_id == "toe_E5_C":
                model_id = "arimax_ar1_rain_lag2"
                records = {
                    horizon: _base_record(
                        window, origin, horizon, model_id, "conditional_ARIMAX", grid
                    )
                    for horizon in HORIZONS
                }
                for record in records.values():
                    record.update(
                        {
                            "training_calendar_days": training_days,
                            "training_target_count": target_count,
                            "mase_scale": mase_scale,
                            "high_movement_threshold": high_threshold,
                        }
                    )
                records[7]["status"] = "feature_unavailable"
                eligible_horizons = [
                    horizon for horizon in (1, 2) if core_by_horizon[horizon]
                ]
                if not enough_training:
                    for horizon in eligible_horizons:
                        records[horizon]["status"] = "insufficient_training"
                    prediction_rows.extend(records.values())
                    continue
                fit = _fit_conditional_arimax(training)
                if fit is None:
                    for horizon in eligible_horizons:
                        records[horizon]["status"] = "insufficient_training"
                    prediction_rows.extend(records.values())
                    continue
                parameter_names = ("constant", "ar.L1", "rain_lag2")
                for parameter_name, parameter_value in zip(
                    parameter_names, fit.coefficients, strict=True
                ):
                    parameter_rows.append(
                        {
                            "window_id": window.window_id,
                            "target_id": window.target_id,
                            "origin_date": origin,
                            "stage": _stage(window, origin),
                            "model_id": model_id,
                            "parameter": parameter_name,
                            "parameter_value": float(parameter_value),
                            "converged": True,
                        }
                    )
                forecasts = _arimax_forecasts(fit, grid, origin)
                for horizon in eligible_horizons:
                    record = records[horizon]
                    record.update(
                        {
                            "converged": True,
                            "fit_warning": fit.warning,
                        }
                    )
                    if horizon not in forecasts:
                        record["status"] = "feature_unavailable"
                        continue
                    point, intervals = forecasts[horizon]
                    _finish_point_record(record, point, grid)
                    record["interval_status"] = "ok_model_based"
                    for label, bounds in intervals.items():
                        record[f"lower_{label}"] = bounds[0]
                        record[f"upper_{label}"] = bounds[1]
                prediction_rows.extend(records.values())

    predictions = pd.DataFrame(prediction_rows).sort_values(
        ["window_id", "origin_date", "model_id", "horizon_days"]
    )
    predictions = _add_empirical_baseline_intervals(predictions).reset_index(drop=True)
    parameters = pd.DataFrame(parameter_rows)
    if not parameters.empty:
        parameters = parameters.sort_values(
            ["window_id", "origin_date", "model_id", "parameter"]
        ).reset_index(drop=True)
    return predictions, parameters
