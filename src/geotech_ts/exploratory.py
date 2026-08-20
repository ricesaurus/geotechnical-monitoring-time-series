"""Segment-aware exploratory time-series methods for Cleveland Corral Phase 3.

The functions in this module never alter Phase 2 inputs.  Observation-level outputs
are intended for the ignored processed-data layer; committed tables contain only
aggregate diagnostics.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, kpss, pacf

PRIMARY_SENSORS = ("mid_R", "mid_P1", "mid_P2", "mid_E2_B")
SECONDARY_SENSORS = ("toe_M1_A", "toe_P7_B", "toe_E5_C")
PHASE3_SENSORS = PRIMARY_SENSORS + SECONDARY_SENSORS

DAILY_ROLE = {
    "mid_R": "daily_rainfall_maximum",
    **{sensor_id: "daily_median" for sensor_id in PHASE3_SENSORS if sensor_id != "mid_R"},
}

FATAL_LEVEL_FLAGS = (
    "flag_timestamp_parse_failure",
    "flag_duplicate_timestamp_in_member",
    "flag_duplicate_timestamp",
    "flag_out_of_order_timestamp",
    "flag_missing_value",
    "flag_nonfinite_value",
    "flag_malformed_value",
    "flag_sentinel_candidate",
    "flag_documented_maintenance_or_outage",
)


@dataclass(frozen=True)
class AnalysisWindow:
    """A half-open period with unchanged instruments for the named series."""

    window_id: str
    start: date
    end_exclusive: date
    sensor_ids: tuple[str, ...]


ANALYSIS_WINDOWS = (
    AnalysisWindow(
        "middle_stable_2009_2016",
        date(2009, 2, 12),
        date(2016, 1, 22),
        PRIMARY_SENSORS,
    ),
    AnalysisWindow(
        "toe_pre_topple_long",
        date(2006, 11, 30),
        date(2016, 1, 22),
        ("mid_R", "toe_M1_A", "toe_P7_B", "toe_E5_C"),
    ),
    AnalysisWindow(
        "toe_pre_topple_post_rain_resume",
        date(2016, 1, 28),
        date(2017, 3, 16),
        ("mid_R", "toe_M1_A", "toe_P7_B", "toe_E5_C"),
    ),
)


class LagPair(NamedTuple):
    predictor: str
    response: str


WINDOW_RELATIONSHIPS = {
    "middle_stable_2009_2016": (
        LagPair("mid_R", "mid_P1"),
        LagPair("mid_R", "mid_P2"),
        LagPair("mid_P1", "mid_E2_B"),
        LagPair("mid_P2", "mid_E2_B"),
        LagPair("mid_R", "mid_E2_B"),
    ),
    "toe_pre_topple_long": (
        LagPair("mid_R", "toe_M1_A"),
        LagPair("mid_R", "toe_P7_B"),
        LagPair("toe_M1_A", "toe_E5_C"),
        LagPair("toe_P7_B", "toe_E5_C"),
        LagPair("mid_R", "toe_E5_C"),
    ),
    "toe_pre_topple_post_rain_resume": (
        LagPair("mid_R", "toe_M1_A"),
        LagPair("mid_R", "toe_P7_B"),
        LagPair("toe_M1_A", "toe_E5_C"),
        LagPair("toe_P7_B", "toe_E5_C"),
        LagPair("mid_R", "toe_E5_C"),
    ),
}


def add_level_eligibility(frame: pd.DataFrame) -> pd.DataFrame:
    """Add an explicit level-analysis mask without removing questionable values."""

    result = frame.copy()
    eligible = result["timestamp_pst_fixed"].notna() & result["value"].notna()
    for column in FATAL_LEVEL_FLAGS:
        eligible &= ~result[column].fillna(False)
    eligible &= result["installation_segment_id"].ne("outside_documented_operation")
    result["analysis_eligible_level"] = eligible
    result["analysis_retains_range_concern"] = (
        eligible & result["flag_metadata_range_concern"].fillna(False)
    )
    return result


def _preferred_rows(frame: pd.DataFrame, product_type: str) -> pd.DataFrame:
    roles = pd.Series(DAILY_ROLE)
    selected = frame.loc[
        frame["product_type"].eq(product_type) & frame["sensor_id"].isin(PHASE3_SENSORS)
    ].copy()
    if product_type == "daily":
        selected = selected.loc[
            selected["measurement_role"].eq(selected["sensor_id"].map(roles))
        ]
    else:
        preferred_15 = {
            "mid_R": "interval_precipitation",
            **{
                sensor_id: "15_minute_observation"
                for sensor_id in PHASE3_SENSORS
                if sensor_id != "mid_R"
            },
        }
        selected = selected.loc[
            selected["measurement_role"].eq(selected["sensor_id"].map(preferred_15))
        ]
    return selected


def coverage_missingness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Distinguish blank values from timestamps absent inside each source segment."""

    selected = pd.concat(
        [_preferred_rows(frame, product) for product in sorted(frame["product_type"].unique())],
        ignore_index=True,
    )
    group_columns = [
        "product_type",
        "sensor_id",
        "measurement_role",
        "installation_segment_id",
    ]
    rows: list[dict[str, object]] = []
    for keys, group in selected.groupby(group_columns, observed=True, sort=True):
        timestamps = group["timestamp_pst_fixed"].dropna().drop_duplicates().sort_values()
        if timestamps.empty:
            continue
        expected_minutes = int(group["expected_interval_minutes"].iloc[0])
        span_minutes = (timestamps.iloc[-1] - timestamps.iloc[0]).total_seconds() / 60
        expected_count = int(math.floor(span_minutes / expected_minutes)) + 1
        absent = max(0, expected_count - len(timestamps))
        blank = int(group["flag_missing_value"].sum())
        nonmissing = int(group["value"].notna().sum())
        row = dict(zip(group_columns, keys, strict=True))
        row.update(
            {
                "first_timestamp_pst": timestamps.iloc[0].isoformat(),
                "last_timestamp_pst": timestamps.iloc[-1].isoformat(),
                "expected_interval_minutes": expected_minutes,
                "expected_timestamp_count_in_span": expected_count,
                "observed_timestamp_count": int(len(timestamps)),
                "absent_timestamp_count": absent,
                "blank_measurement_count": blank,
                "nonmissing_measurement_count": nonmissing,
                "eligible_level_count": int(group["analysis_eligible_level"].sum()),
                "range_concern_retained_count": int(
                    group["analysis_retains_range_concern"].sum()
                ),
                "blank_percent_of_rows": 100 * blank / len(group),
                "absent_percent_of_expected": 100 * absent / expected_count,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def gap_length_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Count exact absent-interval gap lengths for preferred series and segments."""

    pieces: list[pd.DataFrame] = []
    for product in sorted(frame["product_type"].unique()):
        selected = _preferred_rows(frame, product)
        group_columns = [
            "product_type",
            "sensor_id",
            "measurement_role",
            "installation_segment_id",
        ]
        for keys, group in selected.groupby(group_columns, observed=True, sort=True):
            timestamps = group["timestamp_pst_fixed"].dropna().drop_duplicates().sort_values()
            if len(timestamps) < 2:
                continue
            expected = int(group["expected_interval_minutes"].iloc[0])
            delta = timestamps.diff().dt.total_seconds().div(60)
            missing = np.floor(delta / expected).sub(1).astype("Int64")
            missing = missing.loc[missing.gt(0)]
            if missing.empty:
                continue
            counts = missing.value_counts().sort_index()
            part = counts.rename("gap_count").reset_index(name="gap_count")
            part = part.rename(
                columns={"missing_expected_intervals_before": "missing_interval_count"}
            )
            if "missing_interval_count" not in part:
                part = part.rename(columns={part.columns[0]: "missing_interval_count"})
            for column, value in zip(group_columns, keys, strict=True):
                part[column] = value
            part["gap_duration_hours"] = part["missing_interval_count"] * expected / 60
            pieces.append(part)
    columns = [
        "product_type",
        "sensor_id",
        "measurement_role",
        "installation_segment_id",
        "missing_interval_count",
        "gap_duration_hours",
        "gap_count",
    ]
    if not pieces:
        return pd.DataFrame(columns=columns)
    return pd.concat(pieces, ignore_index=True)[columns]


def _daily_level_rows(daily: pd.DataFrame) -> pd.DataFrame:
    selected = _preferred_rows(daily, "daily").copy()
    selected["local_date"] = selected["timestamp_pst_fixed"].dt.date
    selected["transformation"] = np.where(
        selected["sensor_id"].eq("mid_R"), "daily_cumulative_level", "daily_level"
    )
    selected["analysis_eligible"] = selected["analysis_eligible_level"]
    selected["coverage_count"] = 1
    selected["coverage_fraction"] = 1.0
    selected["daily_semantics_match"] = True
    return selected


def _daily_semantics_matches(
    daily_rain: pd.DataFrame, fifteen_minute: pd.DataFrame
) -> pd.Series:
    cumulative = fifteen_minute.loc[
        fifteen_minute["sensor_id"].eq("mid_R")
        & fifteen_minute["measurement_role"].eq("cumulative_precipitation")
        & fifteen_minute["timestamp_pst_fixed"].notna()
        & fifteen_minute["value"].notna()
    ].copy()
    cumulative["local_date"] = cumulative["timestamp_pst_fixed"].dt.date
    by_date = cumulative.groupby("local_date", sort=True)["value"].max()
    observed = daily_rain.set_index("local_date")["value"]
    comparison = pd.concat([observed.rename("daily"), by_date.rename("fifteen")], axis=1)
    matches = pd.Series(False, index=comparison.index)
    comparable = comparison.notna().all(axis=1)
    matches.loc[comparable] = np.isclose(
        comparison.loc[comparable, "daily"],
        comparison.loc[comparable, "fifteen"],
        rtol=0,
        atol=1e-12,
    )
    return daily_rain["local_date"].map(matches).fillna(False)


def _consecutive_changes(
    levels: pd.DataFrame,
    transformation: str,
    require_same_water_year: bool,
    extra_eligibility: pd.Series | None = None,
) -> pd.DataFrame:
    ordered = levels.sort_values("local_date").copy()
    previous_date = ordered["local_date"].shift()
    previous_value = ordered["value"].shift()
    previous_segment = ordered["installation_segment_id"].shift()
    previous_eligible = ordered["analysis_eligible_level"].shift(fill_value=False)
    current_dates = pd.to_datetime(ordered["local_date"])
    prior_dates = pd.to_datetime(previous_date)
    eligible = (
        ordered["analysis_eligible_level"]
        & previous_eligible
        & current_dates.sub(prior_dates).dt.days.eq(1)
        & ordered["installation_segment_id"].eq(previous_segment)
    )
    if require_same_water_year:
        eligible &= ordered["water_year"].eq(ordered["water_year"].shift())
    if extra_eligibility is not None:
        eligible &= extra_eligibility & extra_eligibility.shift(fill_value=False)
    ordered["value"] = ordered["value"] - previous_value
    ordered["transformation"] = transformation
    ordered["analysis_eligible"] = eligible
    ordered["coverage_count"] = 2
    ordered["coverage_fraction"] = np.where(eligible, 1.0, 0.0)
    return ordered


def _interval_rain_daily(fifteen_minute: pd.DataFrame, minimum_count: int) -> pd.DataFrame:
    rain = fifteen_minute.loc[
        fifteen_minute["sensor_id"].eq("mid_R")
        & fifteen_minute["measurement_role"].eq("interval_precipitation")
        & fifteen_minute["timestamp_pst_fixed"].notna()
    ].copy()
    rain["local_date"] = rain["timestamp_pst_fixed"].dt.date
    grouped_rows: list[dict[str, object]] = []
    for local_date, group in rain.groupby("local_date", sort=True):
        eligible = group.loc[group["analysis_eligible_level"]]
        segments = eligible["installation_segment_id"].dropna().unique()
        count = int(eligible["value"].notna().sum())
        grouped_rows.append(
            {
                "local_date": local_date,
                "sensor_id": "mid_R",
                "measurement_role": "interval_precipitation",
                "installation_segment_id": segments[0] if len(segments) == 1 else "mixed_or_none",
                "water_year": int(group["water_year"].dropna().iloc[0]),
                "value": float(eligible["value"].sum()) if count else np.nan,
                "transformation": "daily_interval_sum",
                "analysis_eligible": count >= minimum_count and len(segments) == 1,
                "analysis_eligible_level": count >= minimum_count and len(segments) == 1,
                "analysis_retains_range_concern": bool(
                    eligible["flag_metadata_range_concern"].any()
                ),
                "flag_metadata_range_concern": bool(
                    eligible["flag_metadata_range_concern"].any()
                ),
                "coverage_count": count,
                "coverage_fraction": count / 96,
                "daily_semantics_match": True,
                "timestamp_pst_fixed": pd.Timestamp(local_date).tz_localize("Etc/GMT+8"),
            }
        )
    return pd.DataFrame(grouped_rows)


def build_daily_analysis_series(
    daily: pd.DataFrame,
    fifteen_minute: pd.DataFrame,
    minimum_interval_rain_count: int = 90,
) -> pd.DataFrame:
    """Construct masked daily levels and changes without interpolation or splicing."""

    if "analysis_eligible_level" not in daily:
        daily = add_level_eligibility(daily)
    if "analysis_eligible_level" not in fifteen_minute:
        fifteen_minute = add_level_eligibility(fifteen_minute)
    levels = _daily_level_rows(daily)
    rain_level = levels.loc[levels["sensor_id"].eq("mid_R")].copy()
    rain_level["daily_semantics_match"] = _daily_semantics_matches(
        rain_level, fifteen_minute
    ).to_numpy()
    levels.loc[rain_level.index, "daily_semantics_match"] = rain_level[
        "daily_semantics_match"
    ]

    pieces = [levels]
    for sensor_id in PHASE3_SENSORS:
        if sensor_id == "mid_R":
            continue
        sensor_levels = levels.loc[levels["sensor_id"].eq(sensor_id)]
        pieces.append(
            _consecutive_changes(
                sensor_levels,
                "daily_first_difference",
                require_same_water_year=sensor_id in {"mid_E2_B", "toe_E5_C"},
            )
        )

    rain_extra = rain_level["daily_semantics_match"] & ~rain_level[
        "flag_unexplained_negative_increment"
    ].fillna(False)
    pieces.append(
        _consecutive_changes(
            rain_level,
            "daily_cumulative_difference",
            require_same_water_year=True,
            extra_eligibility=rain_extra,
        )
    )
    pieces.append(_interval_rain_daily(fifteen_minute, minimum_interval_rain_count))

    columns = [
        "local_date",
        "timestamp_pst_fixed",
        "sensor_id",
        "measurement_role",
        "installation_segment_id",
        "water_year",
        "transformation",
        "value",
        "analysis_eligible",
        "analysis_eligible_level",
        "analysis_retains_range_concern",
        "flag_metadata_range_concern",
        "coverage_count",
        "coverage_fraction",
        "daily_semantics_match",
    ]
    result = pd.concat(pieces, ignore_index=True)[columns]
    result["local_date"] = pd.to_datetime(result["local_date"])
    return result.sort_values(["sensor_id", "transformation", "local_date"]).reset_index(
        drop=True
    )


def distribution_summary(series: pd.DataFrame) -> pd.DataFrame:
    """Return conventional and robust segment-aware summaries."""

    eligible = series.loc[series["analysis_eligible"] & series["value"].notna()].copy()
    eligible["scope_id"] = eligible["installation_segment_id"].astype(str)
    cumulative_level = eligible["transformation"].eq("daily_cumulative_level") | (
        eligible["sensor_id"].isin({"mid_E2_B", "toe_E5_C"})
        & eligible["transformation"].eq("daily_level")
    )
    eligible.loc[cumulative_level, "scope_id"] += (
        "__WY" + eligible.loc[cumulative_level, "water_year"].astype("Int64").astype(str)
    )
    rows: list[dict[str, object]] = []
    group_columns = ["sensor_id", "transformation", "scope_id"]
    for keys, group in eligible.groupby(group_columns, sort=True):
        values = group["value"].astype(float)
        median = float(values.median())
        mad = float((values - median).abs().median())
        row = dict(zip(group_columns, keys, strict=True))
        row.update(
            {
                "start_date": group["local_date"].min().date().isoformat(),
                "end_date": group["local_date"].max().date().isoformat(),
                "n": int(len(values)),
                "mean": float(values.mean()),
                "standard_deviation": float(values.std(ddof=1)),
                "minimum": float(values.min()),
                "q05": float(values.quantile(0.05)),
                "q25": float(values.quantile(0.25)),
                "median": median,
                "q75": float(values.quantile(0.75)),
                "q95": float(values.quantile(0.95)),
                "maximum": float(values.max()),
                "iqr": float(values.quantile(0.75) - values.quantile(0.25)),
                "median_absolute_deviation": mad,
                "range_concern_retained_count": int(
                    group["analysis_retains_range_concern"].sum()
                ),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _contiguous_runs(series: pd.DataFrame, minimum_n: int) -> pd.DataFrame:
    eligible = series.loc[series["analysis_eligible"] & series["value"].notna()].copy()
    eligible["scope_id"] = eligible["installation_segment_id"].astype(str)
    cumulative_level = eligible["transformation"].eq("daily_cumulative_level") | (
        eligible["sensor_id"].isin({"mid_E2_B", "toe_E5_C"})
        & eligible["transformation"].eq("daily_level")
    )
    eligible.loc[cumulative_level, "scope_id"] += (
        "__WY" + eligible.loc[cumulative_level, "water_year"].astype("Int64").astype(str)
    )
    parts: list[pd.DataFrame] = []
    group_columns = ["sensor_id", "transformation", "scope_id"]
    for keys, group in eligible.groupby(group_columns, sort=True):
        ordered = group.sort_values("local_date").drop_duplicates("local_date", keep=False)
        run_id = ordered["local_date"].diff().dt.days.ne(1).cumsum()
        for run_number, run in ordered.groupby(run_id):
            if len(run) < minimum_n:
                continue
            run = run.copy()
            for column, value in zip(group_columns, keys, strict=True):
                run[column] = value
            run["run_id"] = f"{keys[0]}__{keys[1]}__{keys[2]}__r{run_number}"
            parts.append(run)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def longest_contiguous_runs(series: pd.DataFrame, minimum_n: int = 120) -> pd.DataFrame:
    """Select the longest exact-daily run inside every segment-aware scope."""

    runs = _contiguous_runs(series, minimum_n)
    if runs.empty:
        return runs
    sizes = runs.groupby("run_id").size()
    run_metadata = runs[["run_id", "sensor_id", "transformation", "scope_id"]].drop_duplicates()
    run_metadata["n"] = run_metadata["run_id"].map(sizes)
    chosen = (
        run_metadata.sort_values(
            ["sensor_id", "transformation", "scope_id", "n", "run_id"],
            ascending=[True, True, True, False, True],
        )
        .groupby(["sensor_id", "transformation", "scope_id"], sort=False)
        .head(1)["run_id"]
    )
    return runs.loc[runs["run_id"].isin(chosen)].copy()


def stationarity_diagnostics(series: pd.DataFrame, minimum_n: int = 120) -> pd.DataFrame:
    """Apply ADF and KPSS jointly to defensible contiguous daily runs."""

    runs = longest_contiguous_runs(series, minimum_n)
    rows: list[dict[str, object]] = []
    if runs.empty:
        return pd.DataFrame()
    for run_id, run in runs.groupby("run_id", sort=True):
        values = run.sort_values("local_date")["value"].to_numpy(dtype=float)
        if np.std(values) == 0:
            continue
        adf_result = adfuller(values, regression="c", autolag="AIC")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            kpss_result = kpss(values, regression="c", nlags="auto")
        adf_p = float(adf_result[1])
        kpss_p = float(kpss_result[1])
        if adf_p < 0.05 and kpss_p >= 0.05:
            joint = "consistent_with_level_stationarity"
        elif adf_p >= 0.05 and kpss_p < 0.05:
            joint = "consistent_with_nonstationarity"
        else:
            joint = "tests_disagree_or_are_inconclusive"
        first = run.iloc[0]
        rows.append(
            {
                "run_id": run_id,
                "sensor_id": first["sensor_id"],
                "transformation": first["transformation"],
                "scope_id": first["scope_id"],
                "start_date": run["local_date"].min().date().isoformat(),
                "end_date": run["local_date"].max().date().isoformat(),
                "n": len(values),
                "adf_statistic": float(adf_result[0]),
                "adf_p_value": adf_p,
                "adf_used_lags": int(adf_result[2]),
                "kpss_statistic": float(kpss_result[0]),
                "kpss_p_value": kpss_p,
                "kpss_used_lags": int(kpss_result[2]),
                "joint_interpretation": joint,
                "test_warning": " | ".join(str(item.message) for item in caught) or "none",
            }
        )
    return pd.DataFrame(rows)


def dependence_diagnostics(
    series: pd.DataFrame, minimum_n: int = 120, requested_max_lag: int = 60
) -> pd.DataFrame:
    """Compute ACF/PACF with daily lag units and approximate confidence bands."""

    runs = longest_contiguous_runs(series, minimum_n)
    rows: list[dict[str, object]] = []
    if runs.empty:
        return pd.DataFrame()
    for run_id, run in runs.groupby("run_id", sort=True):
        values = run.sort_values("local_date")["value"].to_numpy(dtype=float)
        if np.std(values) == 0:
            continue
        max_lag = min(requested_max_lag, len(values) // 4, len(values) // 2 - 1)
        if max_lag < 1:
            continue
        acf_values = acf(values, nlags=max_lag, fft=True)
        pacf_values = pacf(values, nlags=max_lag, method="ywmle")
        bound = 1.96 / math.sqrt(len(values))
        first = run.iloc[0]
        for lag in range(max_lag + 1):
            rows.append(
                {
                    "run_id": run_id,
                    "sensor_id": first["sensor_id"],
                    "transformation": first["transformation"],
                    "scope_id": first["scope_id"],
                    "start_date": run["local_date"].min().date().isoformat(),
                    "end_date": run["local_date"].max().date().isoformat(),
                    "n": len(values),
                    "lag_days": lag,
                    "maximum_lag_days": max_lag,
                    "acf": float(acf_values[lag]),
                    "pacf": float(pacf_values[lag]),
                    "approximate_95_percent_bound": bound,
                }
            )
    return pd.DataFrame(rows)


def decomposition_diagnostics(
    series: pd.DataFrame, periods: tuple[int, ...] = (365, 366), minimum_cycles: int = 2
) -> pd.DataFrame:
    """Apply STL only to regular contiguous runs at least two annual cycles long."""

    minimum_n = max(periods) * minimum_cycles
    runs = longest_contiguous_runs(series, minimum_n)
    rows: list[dict[str, object]] = []
    if runs.empty:
        return pd.DataFrame()
    for run_id, run in runs.groupby("run_id", sort=True):
        values = run.sort_values("local_date")["value"].to_numpy(dtype=float)
        first = run.iloc[0]
        for period in periods:
            if len(values) < period * minimum_cycles:
                continue
            fit = STL(values, period=period, robust=True).fit()
            remainder_var = float(np.var(fit.resid, ddof=1))
            seasonal_strength = max(
                0.0,
                1 - remainder_var / float(np.var(fit.resid + fit.seasonal, ddof=1)),
            )
            trend_strength = max(
                0.0,
                1 - remainder_var / float(np.var(fit.resid + fit.trend, ddof=1)),
            )
            rows.append(
                {
                    "run_id": run_id,
                    "sensor_id": first["sensor_id"],
                    "transformation": first["transformation"],
                    "scope_id": first["scope_id"],
                    "start_date": run["local_date"].min().date().isoformat(),
                    "end_date": run["local_date"].max().date().isoformat(),
                    "n": len(values),
                    "seasonal_period_days": period,
                    "robust_stl": True,
                    "seasonal_strength": seasonal_strength,
                    "trend_strength": trend_strength,
                }
            )
    return pd.DataFrame(rows)


def exact_lag_pairs(
    predictor: pd.Series, response: pd.Series, lag_days: int
) -> pd.DataFrame:
    """Align exact dates; positive lag means the predictor leads the response."""

    left = predictor.rename("predictor").dropna().rename_axis("predictor_date").reset_index()
    left["response_date"] = pd.to_datetime(left["predictor_date"]) + pd.Timedelta(days=lag_days)
    right = response.rename("response").dropna().rename_axis("response_date").reset_index()
    left["response_date"] = pd.to_datetime(left["response_date"])
    right["response_date"] = pd.to_datetime(right["response_date"])
    return left.merge(right, on="response_date", how="inner", validate="one_to_one")


def _lag_curve(
    predictor: pd.Series, response: pd.Series, maximum_lag_days: int
) -> pd.DataFrame:
    rows = []
    for lag in range(maximum_lag_days + 1):
        pairs = exact_lag_pairs(predictor, response, lag)
        correlation = (
            float(pairs[["predictor", "response"]].corr().iloc[0, 1])
            if len(pairs) >= 3
            else np.nan
        )
        rows.append({"lag_days": lag, "n": len(pairs), "correlation": correlation})
    return pd.DataFrame(rows)


def _prewhiten_with_predictor_ar1(
    predictor: pd.Series, response: pd.Series
) -> tuple[pd.Series, pd.Series, float]:
    joined = pd.concat([predictor.rename("x"), response.rename("y")], axis=1).sort_index()
    consecutive = joined.index.to_series().diff().dt.days.eq(1).to_numpy()
    x = joined["x"].astype(float)
    y = joined["y"].astype(float)
    valid_fit = consecutive & x.notna().to_numpy() & x.shift().notna().to_numpy()
    if valid_fit.sum() < 20:
        return pd.Series(dtype=float), pd.Series(dtype=float), np.nan
    x_centered = x - x.mean()
    denominator = float(np.sum(x_centered.shift()[valid_fit] ** 2))
    phi = (
        float(
            np.sum(x_centered[valid_fit] * x_centered.shift()[valid_fit]) / denominator
        )
        if denominator > 0
        else 0.0
    )
    valid = consecutive & x.notna().to_numpy() & x.shift().notna().to_numpy()
    x_filtered = x_centered - phi * x_centered.shift()
    y_centered = y - y.mean()
    y_filtered = y_centered - phi * y_centered.shift()
    x_filtered.loc[~valid] = np.nan
    y_filtered.loc[~(consecutive & y.notna().to_numpy() & y.shift().notna().to_numpy())] = np.nan
    return x_filtered.dropna(), y_filtered.dropna(), phi


def moving_block_bootstrap_ci(
    pairs: pd.DataFrame,
    block_length: int = 30,
    replicates: int = 500,
    seed: int = 170,
) -> tuple[float, float]:
    """Approximate a dependence-aware correlation interval with moving blocks."""

    clean = pairs[["predictor", "response"]].dropna().to_numpy(dtype=float)
    n = len(clean)
    block = min(block_length, max(2, n // 4))
    if n < max(20, 2 * block) or np.std(clean[:, 0]) == 0 or np.std(clean[:, 1]) == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    possible_starts = np.arange(n - block + 1)
    correlations = []
    blocks_needed = math.ceil(n / block)
    for _ in range(replicates):
        starts = rng.choice(possible_starts, size=blocks_needed, replace=True)
        indices = np.concatenate([np.arange(start, start + block) for start in starts])[:n]
        sample = clean[indices]
        if np.std(sample[:, 0]) > 0 and np.std(sample[:, 1]) > 0:
            correlations.append(float(np.corrcoef(sample[:, 0], sample[:, 1])[0, 1]))
    if not correlations:
        return np.nan, np.nan
    return tuple(np.quantile(correlations, [0.025, 0.975]))


def _series_for(
    daily_series: pd.DataFrame,
    sensor_id: str,
    transformation: str,
    window: AnalysisWindow,
) -> pd.Series:
    selected = daily_series.loc[
        daily_series["sensor_id"].eq(sensor_id)
        & daily_series["transformation"].eq(transformation)
        & daily_series["analysis_eligible"]
        & daily_series["local_date"].ge(pd.Timestamp(window.start))
        & daily_series["local_date"].lt(pd.Timestamp(window.end_exclusive))
    ]
    return selected.drop_duplicates("local_date").set_index("local_date")["value"].sort_index()


def daily_lag_diagnostics(
    daily_series: pd.DataFrame,
    maximum_lag_days: int = 30,
    bootstrap_replicates: int = 500,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare naive, transformed, and cautiously prewhitened daily lag curves."""

    curve_parts: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []
    for window in ANALYSIS_WINDOWS:
        for relationship in WINDOW_RELATIONSHIPS[window.window_id]:
            if relationship.predictor == "mid_R":
                configurations = [
                    (
                        "naive_levels",
                        "daily_cumulative_level",
                        "daily_level",
                        "published_cumulative",
                    ),
                    (
                        "transformed",
                        "daily_cumulative_difference",
                        "daily_first_difference",
                        "cumulative_daily_difference",
                    ),
                    (
                        "transformed",
                        "daily_interval_sum",
                        "daily_first_difference",
                        "15_minute_interval_sum",
                    ),
                    (
                        "prewhitened",
                        "daily_cumulative_difference",
                        "daily_first_difference",
                        "cumulative_daily_difference",
                    ),
                    (
                        "prewhitened",
                        "daily_interval_sum",
                        "daily_first_difference",
                        "15_minute_interval_sum",
                    ),
                ]
            else:
                configurations = [
                    ("naive_levels", "daily_level", "daily_level", "not_applicable"),
                    (
                        "transformed",
                        "daily_first_difference",
                        "daily_first_difference",
                        "not_applicable",
                    ),
                    (
                        "prewhitened",
                        "daily_first_difference",
                        "daily_first_difference",
                        "not_applicable",
                    ),
                ]
            for method, predictor_transform, response_transform, rain_definition in configurations:
                predictor = _series_for(
                    daily_series, relationship.predictor, predictor_transform, window
                )
                response = _series_for(
                    daily_series, relationship.response, response_transform, window
                )
                phi = np.nan
                if method == "prewhitened":
                    predictor, response, phi = _prewhiten_with_predictor_ar1(
                        predictor, response
                    )
                curve = _lag_curve(predictor, response, maximum_lag_days)
                curve["window_id"] = window.window_id
                curve["predictor"] = relationship.predictor
                curve["response"] = relationship.response
                curve["method"] = method
                curve["rain_definition"] = rain_definition
                curve["predictor_transformation"] = predictor_transform
                curve["response_transformation"] = response_transform
                curve["prewhitening_ar1_phi"] = phi
                curve_parts.append(curve)
                valid_curve = curve.dropna(subset=["correlation"])
                if valid_curve.empty:
                    continue
                peak = valid_curve.loc[valid_curve["correlation"].abs().idxmax()]
                pairs = exact_lag_pairs(predictor, response, int(peak["lag_days"]))
                ci_low, ci_high = moving_block_bootstrap_ci(
                    pairs, replicates=bootstrap_replicates
                )
                summaries.append(
                    {
                        "window_id": window.window_id,
                        "window_start": window.start.isoformat(),
                        "window_end_exclusive": window.end_exclusive.isoformat(),
                        "predictor": relationship.predictor,
                        "response": relationship.response,
                        "method": method,
                        "rain_definition": rain_definition,
                        "predictor_transformation": predictor_transform,
                        "response_transformation": response_transform,
                        "lag_sign_convention": "positive_lag_predictor_leads_response",
                        "searched_lag_min_days": 0,
                        "searched_lag_max_days": maximum_lag_days,
                        "peak_lag_days": int(peak["lag_days"]),
                        "peak_correlation": float(peak["correlation"]),
                        "peak_pair_count": int(peak["n"]),
                        "bootstrap_block_length_observations": min(
                            30, max(2, len(pairs) // 4)
                        ),
                        "bootstrap_replicates": bootstrap_replicates,
                        "conditional_peak_correlation_ci_low": ci_low,
                        "conditional_peak_correlation_ci_high": ci_high,
                        "prewhitening_ar1_phi": phi,
                    }
                )
    curves = pd.concat(curve_parts, ignore_index=True) if curve_parts else pd.DataFrame()
    return curves, pd.DataFrame(summaries)


def one_to_one_nearest_alignment(
    predictor: pd.DataFrame,
    response: pd.DataFrame,
    tolerance_minutes: float,
    predictor_time_column: str = "timestamp_pst_fixed",
    response_time_column: str = "timestamp_pst_fixed",
) -> pd.DataFrame:
    """Greedily choose deterministic nearest matches without reusing observations."""

    left = predictor.reset_index(drop=False).rename(columns={"index": "predictor_index"})
    right = response.reset_index(drop=False).rename(columns={"index": "response_index"})
    tolerance = pd.Timedelta(minutes=tolerance_minutes)
    candidates: list[tuple[int, pd.Timestamp, pd.Timestamp, int, int, float]] = []
    right_times = pd.DatetimeIndex(right[response_time_column])
    for left_position, left_time in enumerate(left[predictor_time_column]):
        lower = right_times.searchsorted(left_time - tolerance, side="left")
        upper = right_times.searchsorted(left_time + tolerance, side="right")
        for right_position in range(lower, upper):
            right_time = right_times[right_position]
            offset = (right_time - left_time).total_seconds() / 60
            candidates.append(
                (
                    int(abs(offset) * 1_000_000),
                    left_time,
                    right_time,
                    left_position,
                    right_position,
                    offset,
                )
            )
    candidates.sort()
    used_left: set[int] = set()
    used_right: set[int] = set()
    matches: list[dict[str, object]] = []
    for _, left_time, right_time, left_position, right_position, offset in candidates:
        if left_position in used_left or right_position in used_right:
            continue
        used_left.add(left_position)
        used_right.add(right_position)
        matches.append(
            {
                "predictor_index": left.iloc[left_position]["predictor_index"],
                "response_index": right.iloc[right_position]["response_index"],
                "predictor_time": left_time,
                "response_time": right_time,
                "offset_minutes": offset,
                "predictor_value": left.iloc[left_position]["value"],
                "response_value": right.iloc[right_position]["value"],
            }
        )
    return pd.DataFrame(matches).sort_values("predictor_time").reset_index(drop=True)


def select_rain_events(
    daily_series: pd.DataFrame,
    start: date = date(2006, 11, 30),
    end_exclusive: date = date(2016, 1, 22),
    event_count: int = 3,
    minimum_separation_days: int = 7,
) -> pd.DataFrame:
    """Select nonoverlapping events using only eligible interval-rain daily totals."""

    rain = daily_series.loc[
        daily_series["sensor_id"].eq("mid_R")
        & daily_series["transformation"].eq("daily_interval_sum")
        & daily_series["analysis_eligible"]
        & daily_series["local_date"].ge(pd.Timestamp(start))
        & daily_series["local_date"].lt(pd.Timestamp(end_exclusive))
    ].sort_values(["value", "local_date"], ascending=[False, True])
    chosen: list[pd.Series] = []
    for _, candidate in rain.iterrows():
        candidate_date = candidate["local_date"]
        if all(
            abs((candidate_date - prior["local_date"]).days) >= minimum_separation_days
            for prior in chosen
        ):
            chosen.append(candidate)
        if len(chosen) == event_count:
            break
    rows = []
    for rank, candidate in enumerate(chosen, start=1):
        rows.append(
            {
                "event_id": f"rain_event_{rank:02d}_{candidate['local_date'].date().isoformat()}",
                "selection_rank": rank,
                "event_date": candidate["local_date"],
                "daily_interval_rain_mm": float(candidate["value"]),
                "coverage_count": int(candidate["coverage_count"]),
                "selection_rule": (
                    f"top_{event_count}_eligible_daily_interval_rain_totals_"
                    f"minimum_{minimum_separation_days}_days_apart"
                ),
            }
        )
    return pd.DataFrame(rows)


def _event_series(
    fifteen_minute: pd.DataFrame,
    sensor_id: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    role = "interval_precipitation" if sensor_id == "mid_R" else "15_minute_observation"
    selected = fifteen_minute.loc[
        fifteen_minute["sensor_id"].eq(sensor_id)
        & fifteen_minute["measurement_role"].eq(role)
        & fifteen_minute["analysis_eligible_level"]
        & fifteen_minute["timestamp_pst_fixed"].ge(start)
        & fifteen_minute["timestamp_pst_fixed"].lt(end)
    ].sort_values("timestamp_pst_fixed")
    if sensor_id == "mid_R":
        return selected[["timestamp_pst_fixed", "value"]].drop_duplicates(
            "timestamp_pst_fixed", keep=False
        )
    previous_time = selected["timestamp_pst_fixed"].shift()
    previous_value = selected["value"].shift()
    previous_segment = selected["installation_segment_id"].shift()
    delta_minutes = (selected["timestamp_pst_fixed"] - previous_time).dt.total_seconds() / 60
    change_eligible = (
        delta_minutes.gt(0)
        & delta_minutes.le(20)
        & selected["installation_segment_id"].eq(previous_segment)
    )
    result = selected.loc[change_eligible, ["timestamp_pst_fixed"]].copy()
    result["value"] = selected.loc[change_eligible, "value"] - previous_value.loc[
        change_eligible
    ]
    return result.drop_duplicates("timestamp_pst_fixed", keep=False)


def event_alignment_diagnostics(
    fifteen_minute: pd.DataFrame,
    events: pd.DataFrame,
    tolerances_minutes: tuple[float, ...] = (8.0, 15.0),
    maximum_lag_hours: int = 48,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sensitivity-test event lags with one-to-one nearest matching."""

    if "analysis_eligible_level" not in fifteen_minute:
        fifteen_minute = add_level_eligibility(fifteen_minute)
    summaries: list[dict[str, object]] = []
    matched_parts: list[pd.DataFrame] = []
    response_sensors = ("toe_M1_A", "toe_P7_B", "toe_E5_C")
    lags = np.arange(0, maximum_lag_hours * 60 + 1, 15)
    for event in events.itertuples(index=False):
        event_date = pd.Timestamp(event.event_date)
        start = event_date.tz_localize("Etc/GMT+8") - pd.Timedelta(days=1)
        end = event_date.tz_localize("Etc/GMT+8") + pd.Timedelta(days=3)
        rain = _event_series(fifteen_minute, "mid_R", start, end)
        for response_sensor in response_sensors:
            response = _event_series(fifteen_minute, response_sensor, start, end)
            for tolerance in tolerances_minutes:
                lag_rows = []
                for lag_minutes in lags:
                    shifted = rain.copy()
                    shifted["timestamp_pst_fixed"] += pd.Timedelta(minutes=int(lag_minutes))
                    matches = one_to_one_nearest_alignment(
                        shifted, response, tolerance_minutes=tolerance
                    )
                    correlation = (
                        float(
                            matches[["predictor_value", "response_value"]]
                            .corr()
                            .iloc[0, 1]
                        )
                        if len(matches) >= 20
                        and matches["predictor_value"].std() > 0
                        and matches["response_value"].std() > 0
                        else np.nan
                    )
                    lag_rows.append((lag_minutes, correlation, len(matches)))
                    if lag_minutes == 0 and not matches.empty:
                        stored = matches.copy()
                        stored["event_id"] = event.event_id
                        stored["response_sensor"] = response_sensor
                        stored["tolerance_minutes"] = tolerance
                        matched_parts.append(stored)
                valid = [item for item in lag_rows if np.isfinite(item[1])]
                if not valid:
                    continue
                peak_lag, peak_correlation, peak_n = max(valid, key=lambda item: abs(item[1]))
                simultaneous = next(item for item in lag_rows if item[0] == 0)
                summaries.append(
                    {
                        "event_id": event.event_id,
                        "event_date": event_date.date().isoformat(),
                        "daily_interval_rain_mm": event.daily_interval_rain_mm,
                        "response_sensor": response_sensor,
                        "response_transformation": "15_minute_first_difference",
                        "alignment_rule": "one_to_one_nearest_shifted_predictor",
                        "tolerance_minutes": tolerance,
                        "event_window": "one_day_before_through_two_days_after",
                        "lag_sign_convention": "positive_lag_rain_leads_response",
                        "searched_lag_min_hours": 0,
                        "searched_lag_max_hours": maximum_lag_hours,
                        "peak_lag_hours": peak_lag / 60,
                        "peak_correlation": peak_correlation,
                        "peak_pair_count": peak_n,
                        "simultaneous_pair_count": simultaneous[2],
                    }
                )
    summary = pd.DataFrame(summaries)
    if not summary.empty:
        comparison = summary.pivot_table(
            index=["event_id", "response_sensor"],
            columns="tolerance_minutes",
            values=["peak_lag_hours", "peak_correlation"],
            aggfunc="first",
        )
        stable: dict[tuple[str, str], bool] = {}
        for key, row in comparison.iterrows():
            correlations = row["peak_correlation"].dropna()
            lag_values = row["peak_lag_hours"].dropna()
            stable[key] = bool(
                len(correlations) == len(tolerances_minutes)
                and np.sign(correlations).nunique() == 1
                and correlations.max() - correlations.min() <= 0.10
                and lag_values.max() - lag_values.min() <= 2.0
            )
        summary["stable_across_tolerances"] = [
            stable[(row.event_id, row.response_sensor)] for row in summary.itertuples()
        ]
    matches = pd.concat(matched_parts, ignore_index=True) if matched_parts else pd.DataFrame()
    return summary, matches


def synthetic_linear_process_diagnostics(
    seed: int = 170, sample_size: int = 1000, maximum_lag: int = 20
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate a clearly separate AR(1), MA(1), and random-walk learning example."""

    rng = np.random.default_rng(seed)
    noise = rng.normal(size=(sample_size + 1, 3))
    ar1 = np.zeros(sample_size + 1)
    ma1 = np.zeros(sample_size + 1)
    random_walk = np.zeros(sample_size + 1)
    for index in range(1, sample_size + 1):
        ar1[index] = 0.7 * ar1[index - 1] + noise[index, 0]
        ma1[index] = noise[index, 1] + 0.7 * noise[index - 1, 1]
        random_walk[index] = random_walk[index - 1] + noise[index, 2]
    simulated = pd.DataFrame(
        {
            "step": np.arange(sample_size),
            "synthetic_ar1_phi_0_7": ar1[1:],
            "synthetic_ma1_theta_0_7": ma1[1:],
            "synthetic_random_walk": random_walk[1:],
        }
    )
    rows = []
    for series_name in simulated.columns[1:]:
        values = simulated[series_name].to_numpy()
        acf_values = acf(values, nlags=maximum_lag, fft=True)
        pacf_values = pacf(values, nlags=maximum_lag, method="ywmle")
        for lag in range(maximum_lag + 1):
            rows.append(
                {
                    "data_origin": "synthetic_fixed_seed_not_usgs",
                    "seed": seed,
                    "sample_size": sample_size,
                    "series": series_name,
                    "lag": lag,
                    "acf": float(acf_values[lag]),
                    "pacf": float(pacf_values[lag]),
                    "approximate_95_percent_bound": 1.96 / math.sqrt(sample_size),
                }
            )
    return simulated, pd.DataFrame(rows)
