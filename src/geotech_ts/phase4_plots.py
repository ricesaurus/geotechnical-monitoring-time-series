"""Curated Phase 4 forecast, stability, and changepoint figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

TARGET_LABELS = {
    "mid_E2_B": "Middle displacement change",
    "toe_E5_C": "Toe displacement change",
}


def _theme() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({"figure.titlesize": 14, "axes.titlesize": 10})


def _save(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def plot_validation_mae(metrics: pd.DataFrame, path: Path) -> None:
    """Compare later-evaluation MAE at every horizon."""

    _theme()
    selected = metrics.loc[
        metrics["stage"].eq("evaluation")
        & metrics["window_id"].isin(
            ["middle_stable_2009_2016", "toe_pre_topple_long"]
        )
    ].copy()
    figure, axes = plt.subplots(2, 3, figsize=(16, 8), sharey=False)
    for row_number, target_id in enumerate(("mid_E2_B", "toe_E5_C")):
        for column_number, horizon in enumerate((1, 2, 7)):
            axis = axes[row_number, column_number]
            panel = selected.loc[
                selected["target_id"].eq(target_id)
                & selected["horizon_days"].eq(horizon)
                & selected["mae"].notna()
            ].sort_values("mae")
            sns.barplot(data=panel, x="model_id", y="mae", ax=axis, color="#4c72b0")
            axis.tick_params(axis="x", rotation=75, labelsize=7)
            axis.set_xlabel("")
            axis.set_ylabel("MAE (cm/day)")
            axis.set_title(f"{TARGET_LABELS[target_id]} — horizon {horizon} day(s)")
    figure.suptitle("Later chronological evaluation: forecast MAE by frozen candidate")
    figure.tight_layout()
    _save(figure, path)


def plot_relative_mae(metrics: pd.DataFrame, path: Path) -> None:
    """Show performance relative to the zero-change baseline."""

    _theme()
    selected = metrics.loc[
        metrics["stage"].isin(["evaluation", "external_time_check"])
        & metrics["mae"].notna()
    ].copy()
    zero = selected.loc[selected["model_id"].eq("zero_change"), [
        "window_id",
        "stage",
        "horizon_days",
        "mae",
    ]].rename(columns={"mae": "zero_mae"})
    selected = selected.merge(
        zero, on=["window_id", "stage", "horizon_days"], how="left", validate="many_to_one"
    )
    selected["mae_ratio_to_zero"] = selected["mae"] / selected["zero_mae"]
    figure, axes = plt.subplots(1, 3, figsize=(17, 5), sharey=True)
    for axis, horizon in zip(axes, (1, 2, 7), strict=True):
        panel = selected.loc[selected["horizon_days"].eq(horizon)]
        sns.pointplot(
            data=panel,
            x="model_id",
            y="mae_ratio_to_zero",
            hue="window_id",
            dodge=0.35,
            ax=axis,
        )
        axis.axhline(1, color="#c44e52", linestyle="--", linewidth=1)
        axis.tick_params(axis="x", rotation=75, labelsize=7)
        axis.set_xlabel("")
        axis.set_ylabel("MAE / zero-change MAE")
        axis.set_title(f"Horizon {horizon} day(s)")
        if horizon != 1 and axis.legend_ is not None:
            axis.legend_.remove()
    figure.suptitle("Evaluation and external-time performance relative to zero change")
    figure.tight_layout()
    _save(figure, path)


def _retained_rows(
    frame: pd.DataFrame, decisions: pd.DataFrame, stage: str
) -> pd.DataFrame:
    rows = []
    for decision in decisions.itertuples(index=False):
        selected = frame.loc[
            frame["window_id"].eq(decision.window_id)
            & frame["target_id"].eq(decision.target_id)
            & frame["horizon_days"].eq(decision.horizon_days)
            & frame["model_id"].eq(decision.retained_model_id)
            & frame["stage"].eq(stage)
        ].copy()
        rows.append(selected)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def plot_interval_calibration(
    intervals: pd.DataFrame, decisions: pd.DataFrame, path: Path
) -> None:
    """Compare retained and zero-change empirical interval coverage."""

    _theme()
    retained = _retained_rows(intervals, decisions, "evaluation")
    zero = intervals.loc[
        intervals["stage"].eq("evaluation")
        & intervals["model_id"].eq("zero_change")
        & intervals["window_id"].isin(decisions["window_id"])
    ]
    selected = pd.concat([retained, zero], ignore_index=True).drop_duplicates()
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharex=True, sharey=True)
    for axis, target_id in zip(axes, ("mid_E2_B", "toe_E5_C"), strict=True):
        panel = selected.loc[selected["target_id"].eq(target_id)]
        sns.scatterplot(
            data=panel,
            x="nominal_level",
            y="empirical_coverage",
            hue="model_id",
            style="horizon_days",
            s=85,
            ax=axis,
        )
        axis.plot([0.75, 1], [0.75, 1], color="black", linestyle="--", linewidth=0.8)
        axis.set_xlim(0.77, 0.98)
        axis.set_ylim(0.5, 1.01)
        axis.set_title(TARGET_LABELS[target_id])
        axis.set_xlabel("Nominal interval level")
        axis.set_ylabel("Empirical coverage")
    figure.suptitle("Later-evaluation prediction-interval calibration")
    figure.tight_layout()
    _save(figure, path)


def plot_retained_residual_acf(
    residuals: pd.DataFrame, decisions: pd.DataFrame, path: Path
) -> None:
    """Plot evaluation error dependence for retained models and zero change."""

    _theme()
    retained = _retained_rows(residuals, decisions, "evaluation")
    zero = residuals.loc[
        residuals["stage"].eq("evaluation")
        & residuals["model_id"].eq("zero_change")
        & residuals["window_id"].isin(decisions["window_id"])
    ]
    selected = pd.concat([retained, zero], ignore_index=True).drop_duplicates()
    figure, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True, sharey=True)
    for row_number, target_id in enumerate(("mid_E2_B", "toe_E5_C")):
        for column_number, horizon in enumerate((1, 2, 7)):
            axis = axes[row_number, column_number]
            panel = selected.loc[
                selected["target_id"].eq(target_id)
                & selected["horizon_days"].eq(horizon)
            ]
            sns.lineplot(
                data=panel,
                x="lag_in_origin_sequence",
                y="residual_acf",
                hue="model_id",
                marker="o",
                ax=axis,
            )
            axis.axhline(0, color="black", linewidth=0.6)
            axis.set_title(f"{TARGET_LABELS[target_id]} — h={horizon}")
            axis.set_xlabel("Lag in scheduled-origin sequence")
            axis.set_ylabel("Out-of-sample error ACF")
    figure.suptitle("Later-evaluation residual dependence: retained versus zero change")
    figure.tight_layout()
    _save(figure, path)


def plot_water_year_stability(
    stratified: pd.DataFrame, decisions: pd.DataFrame, path: Path
) -> None:
    """Show retained and zero-change MAE by water year."""

    _theme()
    water_year = stratified.loc[
        stratified["dimension"].eq("water_year")
        & stratified["stage"].eq("evaluation")
    ]
    retained = _retained_rows(water_year, decisions, "evaluation")
    zero = water_year.loc[
        water_year["model_id"].eq("zero_change")
        & water_year["window_id"].isin(decisions["window_id"])
    ]
    selected = pd.concat([retained, zero], ignore_index=True).drop_duplicates()
    figure, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=False)
    for row_number, target_id in enumerate(("mid_E2_B", "toe_E5_C")):
        for column_number, horizon in enumerate((1, 2, 7)):
            axis = axes[row_number, column_number]
            panel = selected.loc[
                selected["target_id"].eq(target_id)
                & selected["horizon_days"].eq(horizon)
            ]
            sns.lineplot(
                data=panel,
                x="group_value",
                y="mae",
                hue="model_id",
                marker="o",
                ax=axis,
            )
            axis.tick_params(axis="x", rotation=45)
            axis.set_xlabel("Water year")
            axis.set_ylabel("MAE (cm/day)")
            axis.set_title(f"{TARGET_LABELS[target_id]} — h={horizon}")
    figure.suptitle("Later-evaluation water-year stability")
    figure.tight_layout()
    _save(figure, path)


def plot_parameter_paths(parameters: pd.DataFrame, path: Path) -> None:
    """Plot representative AR and rain coefficients across origins."""

    _theme()
    choices = (
        ("middle_stable_2009_2016", "arima_ar1", "ar.L1"),
        ("toe_pre_topple_long", "arima_ar1", "ar.L1"),
        ("toe_pre_topple_long", "arimax_ar1_rain_lag2", "rain_lag2"),
    )
    figure, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=False)
    for axis, (window_id, model_id, parameter) in zip(axes, choices, strict=True):
        selected = parameters.loc[
            parameters["window_id"].eq(window_id)
            & parameters["model_id"].eq(model_id)
            & parameters["parameter"].eq(parameter)
        ]
        axis.plot(selected["origin_date"], selected["parameter_value"], linewidth=0.9)
        axis.axhline(0, color="black", linewidth=0.6)
        axis.set_title(f"{window_id}: {model_id} — {parameter}")
        axis.set_ylabel("Rolling estimate")
        axis.set_xlabel("Forecast origin (fixed-PST date)")
    figure.suptitle("Predeclared coefficient stability across expanding origins")
    figure.tight_layout()
    _save(figure, path)


def plot_changepoint_sensitivity(
    detections: pd.DataFrame, candidates: pd.DataFrame, path: Path
) -> None:
    """Show method/setting support without implying a physical regime change."""

    _theme()
    figure, axes = plt.subplots(3, 1, figsize=(15, 9), sharex=False)
    windows = (
        "middle_stable_2009_2016",
        "toe_pre_topple_long",
        "toe_pre_topple_post_rain_resume",
    )
    for axis, window_id in zip(axes, windows, strict=True):
        panel = detections.loc[detections["window_id"].eq(window_id)].copy()
        panel["method_setting"] = panel["method"] + ": " + panel["setting"]
        if not panel.empty:
            sns.scatterplot(
                data=panel,
                x=pd.to_datetime(panel["candidate_date"]),
                y="method_setting",
                hue="method",
                s=40,
                ax=axis,
            )
        grouped = candidates.loc[candidates["window_id"].eq(window_id)]
        for candidate in grouped.itertuples(index=False):
            color = {
                "metadata_aligned": "#55a868",
                "event_aligned": "#dd8452",
                "unexplained": "#c44e52",
            }[candidate.context_classification]
            axis.axvline(pd.Timestamp(candidate.candidate_date), color=color, alpha=0.35)
        axis.set_title(window_id)
        axis.set_xlabel("Candidate date")
        axis.set_ylabel("Method and sensitivity setting")
        axis.tick_params(axis="y", labelsize=6)
    figure.suptitle(
        "Changepoint sensitivity inside exact runs; colored lines are context classes only"
    )
    figure.tight_layout()
    _save(figure, path)


def plot_synthetic_leakage(
    summary: pd.DataFrame, values: pd.DataFrame, path: Path
) -> None:
    """Illustrate why a random time-series split can see a later regime."""

    _theme()
    figure, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(values["step"], values["synthetic_value"], linewidth=0.8)
    axes[0].axvline(210, color="#4c72b0", linestyle="--", label="chronological split")
    axes[0].axvline(220, color="#c44e52", linestyle="--", label="synthetic shift")
    axes[0].set_title("Synthetic series with a later mean shift")
    axes[0].set_xlabel("Synthetic step")
    axes[0].set_ylabel("Synthetic value")
    axes[0].legend()
    sns.barplot(data=summary, x="validation_design", y="mae", ax=axes[1])
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].set_title("Same mean model, different validation design")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Synthetic test MAE")
    figure.suptitle("SYNTHETIC LEAKAGE DEMONSTRATION — seed 170; not USGS observations")
    figure.tight_layout()
    _save(figure, path)


def plot_forecast_coverage(metrics: pd.DataFrame, path: Path) -> None:
    """Display coverage and the deliberately unavailable ARIMAX horizon."""

    _theme()
    selected = metrics.loc[
        metrics["stage"].isin(["evaluation", "external_time_check"])
    ].copy()
    figure, axes = plt.subplots(1, 3, figsize=(17, 5), sharey=True)
    for axis, horizon in zip(axes, (1, 2, 7), strict=True):
        panel = selected.loc[selected["horizon_days"].eq(horizon)]
        sns.barplot(
            data=panel,
            x="model_id",
            y="point_coverage_fraction",
            hue="window_id",
            ax=axis,
        )
        axis.set_ylim(0, 1.05)
        axis.tick_params(axis="x", rotation=75, labelsize=7)
        axis.set_xlabel("")
        axis.set_ylabel("Point-forecast coverage")
        axis.set_title(f"Horizon {horizon} day(s)")
        if horizon != 1 and axis.legend_ is not None:
            axis.legend_.remove()
    figure.suptitle("Model coverage on eligible chronological origins")
    figure.tight_layout()
    _save(figure, path)
