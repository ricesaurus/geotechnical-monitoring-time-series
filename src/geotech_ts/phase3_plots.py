"""Curated plotting helpers for Phase 3 aggregate and explanatory outputs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.tsa.seasonal import STL

SENSOR_LABELS = {
    "mid_R": "Middle rain",
    "mid_P1": "Middle shallow pressure",
    "mid_P2": "Middle deep pressure",
    "mid_E2_B": "Middle displacement",
    "toe_M1_A": "Toe moisture",
    "toe_P7_B": "Toe pressure",
    "toe_E5_C": "Toe displacement",
}


def _save(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def _theme() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"figure.titlesize": 14, "axes.titlesize": 11})


def plot_daily_coverage(daily_series: pd.DataFrame, path: Path) -> None:
    """Plot monthly eligible-day coverage for the retained daily series."""

    _theme()
    levels = daily_series.loc[
        daily_series["transformation"].isin(["daily_cumulative_level", "daily_level"])
    ].copy()
    levels["month"] = levels["local_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        levels.groupby(["sensor_id", "month"], sort=True)["analysis_eligible"]
        .mean()
        .rename("eligible_fraction")
        .reset_index()
    )
    sensors = [sensor for sensor in SENSOR_LABELS if sensor in set(monthly["sensor_id"])]
    start = monthly["month"].min()
    end = monthly["month"].max()
    all_months = pd.date_range(start, end, freq="MS")
    matrix = (
        monthly.pivot(index="sensor_id", columns="month", values="eligible_fraction")
        .reindex(index=sensors, columns=all_months)
        .rename(index=SENSOR_LABELS)
    )
    matrix = pd.DataFrame(
        matrix.astype("Float64").to_numpy(dtype=float, na_value=np.nan),
        index=matrix.index,
        columns=matrix.columns,
    )
    figure, axis = plt.subplots(figsize=(14, 4.8))
    sns.heatmap(
        matrix,
        ax=axis,
        cmap=sns.color_palette("mako", as_cmap=True),
        vmin=0,
        vmax=1,
        cbar_kws={"label": "Eligible fraction of published daily rows"},
        xticklabels=False,
    )
    tick_positions = np.arange(0, len(all_months), 12) + 0.5
    axis.set_xticks(tick_positions)
    axis.set_xticklabels([str(month.year) for month in all_months[::12]], rotation=0)
    axis.set_xlabel("Calendar month (annual labels)")
    axis.set_ylabel("")
    axis.set_title("Daily coverage and missingness by retained sensor")
    figure.text(
        0.5,
        0.03,
        "Blank measurements and absent dates remain distinct in the aggregate tables",
        ha="center",
        fontsize=9,
    )
    figure.subplots_adjust(bottom=0.17)
    _save(figure, path)


def plot_temporal_regimes(daily_series: pd.DataFrame, path: Path) -> None:
    """Show daily evolution without joining installation regimes."""

    _theme()
    sensors = ("mid_P1", "mid_P2", "mid_E2_B", "toe_M1_A", "toe_P7_B", "toe_E5_C")
    figure, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=False)
    for axis, sensor_id in zip(axes.flat, sensors, strict=True):
        sensor = daily_series.loc[
            daily_series["sensor_id"].eq(sensor_id)
            & daily_series["transformation"].eq("daily_level")
        ].sort_values("local_date")
        for segment, group in sensor.groupby("installation_segment_id", sort=False):
            eligible = group.loc[group["analysis_eligible"]]
            if eligible.empty:
                continue
            axis.plot(
                eligible["local_date"],
                eligible["value"],
                linewidth=0.8,
                label=str(segment).replace(f"{sensor_id}_", ""),
            )
        concerns = sensor.loc[
            sensor["analysis_eligible"] & sensor["flag_metadata_range_concern"]
        ]
        if not concerns.empty:
            axis.scatter(
                concerns["local_date"], concerns["value"], color="#c44e52", s=8, label="range flag"
            )
        axis.set_title(SENSOR_LABELS[sensor_id])
        axis.set_ylabel("Published level")
        axis.legend(fontsize=6, loc="best")
    figure.suptitle("Daily levels by documented sensor regime (no successor splicing)")
    figure.tight_layout()
    _save(figure, path)


def plot_water_year_patterns(daily_series: pd.DataFrame, path: Path) -> None:
    """Plot robust water-year patterns for hydrologic level series."""

    _theme()
    sensors = ("mid_P1", "mid_P2", "toe_M1_A", "toe_P7_B")
    figure, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True)
    for axis, sensor_id in zip(axes.flat, sensors, strict=True):
        sensor = daily_series.loc[
            daily_series["sensor_id"].eq(sensor_id)
            & daily_series["transformation"].eq("daily_level")
            & daily_series["analysis_eligible"]
        ].copy()
        water_year_start = pd.to_datetime((sensor["water_year"] - 1).astype(str) + "-10-01")
        sensor["water_year_day"] = (sensor["local_date"] - water_year_start).dt.days + 1
        grouped = sensor.groupby("water_year_day")["value"]
        summary = grouped.agg(
            median="median",
            q10=lambda values: values.quantile(0.10),
            q90=lambda values: values.quantile(0.90),
            n="count",
        )
        summary = summary.loc[summary["n"].ge(3)]
        x = summary.index.to_numpy(dtype=float)
        axis.fill_between(
            x,
            summary["q10"].to_numpy(dtype=float),
            summary["q90"].to_numpy(dtype=float),
            alpha=0.25,
        )
        axis.plot(x, summary["median"], linewidth=1.3)
        axis.set_title(SENSOR_LABELS[sensor_id])
        axis.set_ylabel("Published level")
        axis.set_xlim(1, 366)
    for axis in axes[-1]:
        axis.set_xlabel("Water-year day (October 1 = 1)")
    figure.suptitle("Water-year seasonality: median and 10th–90th percentile envelope")
    figure.tight_layout()
    _save(figure, path)


def plot_distributions(daily_series: pd.DataFrame, path: Path) -> None:
    """Plot robustly scaled distributions of selected valid transformations."""

    _theme()
    selections = (
        ("mid_R", "daily_interval_sum"),
        ("mid_P1", "daily_first_difference"),
        ("mid_P2", "daily_first_difference"),
        ("mid_E2_B", "daily_first_difference"),
        ("toe_M1_A", "daily_first_difference"),
        ("toe_E5_C", "daily_first_difference"),
    )
    figure, axes = plt.subplots(3, 2, figsize=(13, 10))
    for axis, (sensor_id, transformation) in zip(axes.flat, selections, strict=True):
        values = daily_series.loc[
            daily_series["sensor_id"].eq(sensor_id)
            & daily_series["transformation"].eq(transformation)
            & daily_series["analysis_eligible"],
            "value",
        ]
        if values.empty:
            axis.set_visible(False)
            continue
        lower, upper = values.quantile([0.005, 0.995])
        shown = values.loc[values.between(lower, upper)]
        sns.histplot(shown, bins=45, ax=axis, color="#4c72b0")
        axis.axvline(values.median(), color="#c44e52", linewidth=1, label="median")
        axis.set_title(f"{SENSOR_LABELS[sensor_id]} — {transformation.replace('_', ' ')}")
        axis.set_xlabel("Value (display limited to 0.5th–99.5th percentiles)")
        axis.legend(fontsize=7)
    figure.suptitle("Segment-aware daily distributions; no values were clipped in calculations")
    figure.tight_layout()
    _save(figure, path)


def plot_representative_decomposition(
    daily_series: pd.DataFrame, decomposition: pd.DataFrame, path: Path
) -> None:
    """Plot one inspected STL example from a qualifying contiguous run."""

    _theme()
    candidates = decomposition.loc[decomposition["seasonal_period_days"].eq(365)].sort_values(
        ["n", "sensor_id"], ascending=[False, True]
    )
    if candidates.empty:
        return
    chosen = candidates.iloc[0]
    start = pd.Timestamp(chosen["start_date"])
    end = pd.Timestamp(chosen["end_date"])
    series = daily_series.loc[
        daily_series["sensor_id"].eq(chosen["sensor_id"])
        & daily_series["transformation"].eq(chosen["transformation"])
        & daily_series["analysis_eligible"]
        & daily_series["local_date"].between(start, end)
    ].drop_duplicates("local_date")
    series = series.set_index("local_date")["value"].sort_index().asfreq("D")
    if series.isna().any():
        return
    fit = STL(series, period=365, robust=True).fit()
    figure, axes = plt.subplots(4, 1, figsize=(13, 9), sharex=True)
    axes[0].plot(series.index, series, linewidth=0.8)
    axes[0].set_ylabel("Observed")
    axes[1].plot(series.index, fit.trend, linewidth=0.8, color="#55a868")
    axes[1].set_ylabel("Trend")
    axes[2].plot(series.index, fit.seasonal, linewidth=0.8, color="#c44e52")
    axes[2].set_ylabel("Seasonal")
    axes[3].plot(series.index, fit.resid, linewidth=0.6, color="#8172b2")
    axes[3].set_ylabel("Remainder")
    axes[3].set_xlabel("Fixed-PST local date")
    figure.suptitle(
        f"Robust STL example: {SENSOR_LABELS[chosen['sensor_id']]} "
        f"({chosen['start_date']} to {chosen['end_date']}, period 365 days)"
    )
    figure.tight_layout()
    _save(figure, path)


def plot_acf_pacf(dependence: pd.DataFrame, path: Path) -> None:
    """Plot representative daily ACF/PACF diagnostics."""

    _theme()
    priorities = {
        "mid_R": "daily_interval_sum",
        "mid_P1": "daily_level",
        "mid_P2": "daily_level",
        "mid_E2_B": "daily_first_difference",
        "toe_M1_A": "daily_level",
        "toe_E5_C": "daily_first_difference",
    }
    figure, axes = plt.subplots(len(priorities), 2, figsize=(13, 15), sharex=False)
    for row_number, (sensor_id, transformation) in enumerate(priorities.items()):
        subset = dependence.loc[
            dependence["sensor_id"].eq(sensor_id)
            & dependence["transformation"].eq(transformation)
        ]
        if subset.empty:
            axes[row_number, 0].set_visible(False)
            axes[row_number, 1].set_visible(False)
            continue
        run_sizes = subset.groupby("run_id")["n"].first().sort_values(ascending=False)
        chosen = subset.loc[subset["run_id"].eq(run_sizes.index[0])]
        bound = chosen["approximate_95_percent_bound"].iloc[0]
        for column_number, diagnostic in enumerate(("acf", "pacf")):
            axis = axes[row_number, column_number]
            axis.vlines(chosen["lag_days"], 0, chosen[diagnostic], linewidth=0.8)
            axis.axhline(bound, linestyle="--", linewidth=0.7, color="#c44e52")
            axis.axhline(-bound, linestyle="--", linewidth=0.7, color="#c44e52")
            axis.axhline(0, color="black", linewidth=0.5)
            axis.set_title(
                f"{SENSOR_LABELS[sensor_id]} {diagnostic.upper()} — "
                f"{transformation.replace('_', ' ')} (n={int(chosen['n'].iloc[0])})"
            )
            axis.set_xlabel("Lag (days)")
    figure.suptitle("Daily ACF/PACF within one contiguous documented regime per panel")
    figure.tight_layout()
    _save(figure, path)


def plot_synthetic_demo(simulated: pd.DataFrame, diagnostics: pd.DataFrame, path: Path) -> None:
    """Plot the fixed-seed learning demonstration, clearly labeled synthetic."""

    _theme()
    series_names = [column for column in simulated if column != "step"]
    figure, axes = plt.subplots(3, 3, figsize=(14, 10))
    for row_number, series_name in enumerate(series_names):
        axes[row_number, 0].plot(
            simulated["step"].iloc[:250], simulated[series_name].iloc[:250], linewidth=0.8
        )
        axes[row_number, 0].set_title(f"{series_name} — first 250 synthetic steps")
        selected = diagnostics.loc[diagnostics["series"].eq(series_name)]
        bound = selected["approximate_95_percent_bound"].iloc[0]
        for column_number, diagnostic in ((1, "acf"), (2, "pacf")):
            axes[row_number, column_number].vlines(
                selected["lag"], 0, selected[diagnostic], linewidth=0.9
            )
            axes[row_number, column_number].axhline(bound, linestyle="--", color="#c44e52")
            axes[row_number, column_number].axhline(-bound, linestyle="--", color="#c44e52")
            axes[row_number, column_number].set_title(f"Synthetic {diagnostic.upper()}")
            axes[row_number, column_number].set_xlabel("Lag")
    figure.suptitle("SYNTHETIC LEARNING DEMONSTRATION — seed 170; not USGS observations")
    figure.tight_layout()
    _save(figure, path)


def plot_daily_lag_curves(curves: pd.DataFrame, path: Path) -> None:
    """Compare rain definitions and dependence adjustments for selected pairs."""

    _theme()
    relationships = (
        ("middle_stable_2009_2016", "mid_R", "mid_P1"),
        ("middle_stable_2009_2016", "mid_R", "mid_P2"),
        ("middle_stable_2009_2016", "mid_R", "mid_E2_B"),
        ("toe_pre_topple_long", "mid_R", "toe_M1_A"),
        ("toe_pre_topple_long", "mid_R", "toe_P7_B"),
        ("toe_pre_topple_long", "mid_R", "toe_E5_C"),
    )
    figure, axes = plt.subplots(3, 2, figsize=(14, 11), sharex=True)
    for axis, (window_id, predictor, response) in zip(axes.flat, relationships, strict=True):
        selected = curves.loc[
            curves["window_id"].eq(window_id)
            & curves["predictor"].eq(predictor)
            & curves["response"].eq(response)
            & curves["method"].isin(["transformed", "prewhitened"])
        ]
        for keys, group in selected.groupby(["method", "rain_definition"], sort=True):
            method, definition = keys
            axis.plot(
                group["lag_days"],
                group["correlation"],
                linewidth=1,
                label=f"{method}; {definition.replace('_', ' ')}",
            )
        axis.axhline(0, color="black", linewidth=0.5)
        axis.set_title(f"Rain → {SENSOR_LABELS[response]} ({window_id})")
        axis.set_ylabel("Lag correlation")
        axis.legend(fontsize=6)
    for axis in axes[-1]:
        axis.set_xlabel("Positive lag (days): rain leads response")
    figure.suptitle("Exact-date daily lag sensitivity; association is not causation")
    figure.tight_layout()
    _save(figure, path)


def plot_event_sensitivity(event_summary: pd.DataFrame, path: Path) -> None:
    """Show whether event peak lags persist across alignment tolerances."""

    _theme()
    if event_summary.empty:
        return
    figure, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.lineplot(
        data=event_summary,
        x="tolerance_minutes",
        y="peak_lag_hours",
        hue="response_sensor",
        style="event_id",
        markers=True,
        dashes=False,
        ax=axes[0],
    )
    sns.lineplot(
        data=event_summary,
        x="tolerance_minutes",
        y="peak_correlation",
        hue="response_sensor",
        style="event_id",
        markers=True,
        dashes=False,
        ax=axes[1],
        legend=False,
    )
    axes[0].set_title("Peak lag sensitivity")
    axes[0].set_ylabel("Peak positive lag (hours)")
    axes[1].set_title("Peak correlation sensitivity")
    axes[1].set_ylabel("Exploratory correlation")
    for axis in axes:
        axis.set_xlabel("One-to-one match tolerance (minutes)")
    figure.suptitle("Rain-selected events: alignment sensitivity (no interpolation or reuse)")
    figure.tight_layout()
    _save(figure, path)
