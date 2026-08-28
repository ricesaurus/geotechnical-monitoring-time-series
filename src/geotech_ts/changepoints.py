"""Conservative, regime-bounded changepoint sensitivity analysis for Phase 4."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
import ruptures as rpt

from geotech_ts.forecasting import FORECAST_WINDOWS
from geotech_ts.sensor_events import SEGMENT_STARTS

MINIMUM_RUN_LENGTH = 180
MINIMUM_SEGMENT_LENGTH = 30
ALIGNMENT_TOLERANCE_DAYS = 7
PELT_MULTIPLIERS = (1, 2, 4)
BINSEG_CHANGES = (1, 2, 3)
PHASE3_RAIN_EVENTS = (
    date(2008, 1, 4),
    date(2010, 10, 24),
    date(2012, 11, 30),
)


@dataclass(frozen=True)
class ChangeRun:
    """One exact daily target run that crosses no known boundary."""

    run_id: str
    window_id: str
    target_id: str
    segment_id: str
    water_year: int
    frame: pd.DataFrame


def exact_change_runs(daily_series: pd.DataFrame) -> list[ChangeRun]:
    """Create exact contiguous eligible runs inside target segment and water year."""

    runs: list[ChangeRun] = []
    for window in FORECAST_WINDOWS:
        selected = daily_series.loc[
            daily_series["sensor_id"].eq(window.target_id)
            & daily_series["transformation"].eq("daily_first_difference")
            & daily_series["analysis_eligible"]
            & daily_series["value"].notna()
            & daily_series["local_date"].ge(pd.Timestamp(window.start))
            & daily_series["local_date"].lt(pd.Timestamp(window.end_exclusive))
        ].sort_values("local_date")
        group_columns = ["installation_segment_id", "water_year"]
        for keys, group in selected.groupby(group_columns, sort=True, dropna=False):
            ordered = group.drop_duplicates("local_date", keep=False).sort_values("local_date")
            run_number = ordered["local_date"].diff().dt.days.ne(1).cumsum()
            for number, run in ordered.groupby(run_number, sort=True):
                if len(run) < MINIMUM_RUN_LENGTH:
                    continue
                segment_id = str(keys[0])
                water_year = int(keys[1])
                run_id = (
                    f"{window.window_id}__{segment_id}__WY{water_year}__r{int(number)}"
                )
                runs.append(
                    ChangeRun(
                        run_id,
                        window.window_id,
                        window.target_id,
                        segment_id,
                        water_year,
                        run.reset_index(drop=True),
                    )
                )
    return runs


def _break_rows(
    run: ChangeRun,
    method: str,
    setting: str,
    break_indices: list[int],
) -> list[dict[str, object]]:
    rows = []
    for index in break_indices:
        if index >= len(run.frame):
            continue
        rows.append(
            {
                "run_id": run.run_id,
                "window_id": run.window_id,
                "target_id": run.target_id,
                "segment_id": run.segment_id,
                "water_year": run.water_year,
                "run_start_date": run.frame["local_date"].min().date().isoformat(),
                "run_end_date": run.frame["local_date"].max().date().isoformat(),
                "run_length_days": len(run.frame),
                "method": method,
                "setting": setting,
                "minimum_segment_length_days": MINIMUM_SEGMENT_LENGTH,
                "candidate_date": run.frame.iloc[index]["local_date"].date().isoformat(),
                "candidate_index": index,
            }
        )
    return rows


def detect_changepoints(daily_series: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the frozen PELT and binary-segmentation sensitivity settings."""

    runs = exact_change_runs(daily_series)
    detections: list[dict[str, object]] = []
    run_rows: list[dict[str, object]] = []
    for run in runs:
        values = run.frame["value"].to_numpy(dtype=float).reshape(-1, 1)
        variance = float(np.var(values, ddof=1))
        setting_count = 0
        for multiplier in PELT_MULTIPLIERS:
            penalty = multiplier * math.log(len(values)) * variance
            breakpoints = rpt.Pelt(
                model="l2", min_size=MINIMUM_SEGMENT_LENGTH, jump=1
            ).fit(values).predict(pen=penalty)
            setting = f"multiplier_{multiplier}_penalty_{penalty:.12g}"
            detections.extend(_break_rows(run, "PELT_l2", setting, breakpoints))
            setting_count += 1
        for change_count in BINSEG_CHANGES:
            if len(values) < (change_count + 1) * MINIMUM_SEGMENT_LENGTH:
                continue
            breakpoints = rpt.Binseg(
                model="l2", min_size=MINIMUM_SEGMENT_LENGTH, jump=1
            ).fit(values).predict(n_bkps=change_count)
            setting = f"n_bkps_{change_count}"
            detections.extend(_break_rows(run, "Binseg_l2", setting, breakpoints))
            setting_count += 1
        run_rows.append(
            {
                "run_id": run.run_id,
                "window_id": run.window_id,
                "target_id": run.target_id,
                "segment_id": run.segment_id,
                "water_year": run.water_year,
                "run_start_date": run.frame["local_date"].min().date().isoformat(),
                "run_end_date": run.frame["local_date"].max().date().isoformat(),
                "run_length_days": len(run.frame),
                "sensitivity_setting_count": setting_count,
            }
        )
    detection_frame = pd.DataFrame(detections)
    run_summary = pd.DataFrame(run_rows)
    if not detection_frame.empty:
        counts = detection_frame.groupby("run_id").size()
        run_summary["raw_detection_count"] = run_summary["run_id"].map(counts).fillna(0).astype(int)
    else:
        run_summary["raw_detection_count"] = 0
    return detection_frame, run_summary


def _cluster_dates(dates: pd.Series) -> list[list[pd.Timestamp]]:
    ordered = sorted(pd.to_datetime(dates).drop_duplicates())
    clusters: list[list[pd.Timestamp]] = []
    for candidate in ordered:
        if not clusters or (candidate - clusters[-1][-1]).days > ALIGNMENT_TOLERANCE_DAYS:
            clusters.append([candidate])
        else:
            clusters[-1].append(candidate)
    return clusters


def _metadata_dates(
    target_id: str, start: pd.Timestamp, end: pd.Timestamp
) -> list[tuple[pd.Timestamp, str]]:
    contexts: list[tuple[pd.Timestamp, str]] = []
    for segment in SEGMENT_STARTS[target_id]:
        timestamp = pd.Timestamp(segment.start_date)
        if start - pd.Timedelta(days=ALIGNMENT_TOLERANCE_DAYS) <= timestamp <= end + pd.Timedelta(
            days=ALIGNMENT_TOLERANCE_DAYS
        ):
            contexts.append((timestamp, f"target_{segment.reason.replace(' ', '_')}"))
    fixed = (
        (pd.Timestamp("2016-01-22"), "rain_gauge_interruption_start"),
        (pd.Timestamp("2016-01-28"), "rain_gauge_resume"),
        (pd.Timestamp("2017-03-16"), "toe_extensometer_topple"),
        (pd.Timestamp("2017-04-25"), "toe_extensometer_relocation"),
    )
    contexts.extend(
        (timestamp, label)
        for timestamp, label in fixed
        if start - pd.Timedelta(days=ALIGNMENT_TOLERANCE_DAYS)
        <= timestamp
        <= end + pd.Timedelta(days=ALIGNMENT_TOLERANCE_DAYS)
    )
    for year in range(start.year, end.year + 1):
        reset = pd.Timestamp(year=year, month=10, day=1)
        if start - pd.Timedelta(days=ALIGNMENT_TOLERANCE_DAYS) <= reset <= end + pd.Timedelta(
            days=ALIGNMENT_TOLERANCE_DAYS
        ):
            contexts.append((reset, "water_year_reset"))
    return contexts


def _nearest_context(
    candidate: pd.Timestamp,
    contexts: list[tuple[pd.Timestamp, str]],
) -> tuple[pd.Timestamp | None, str, int | None]:
    if not contexts:
        return None, "none", None
    nearest_date, label = min(contexts, key=lambda item: abs((candidate - item[0]).days))
    offset = (candidate - nearest_date).days
    if abs(offset) <= ALIGNMENT_TOLERANCE_DAYS:
        return nearest_date, label, offset
    return None, "none", None


def summarize_changepoints(
    detections: pd.DataFrame,
    daily_series: pd.DataFrame,
) -> pd.DataFrame:
    """Group sensitivity dates and classify only by transparent temporal alignment."""

    if detections.empty:
        return pd.DataFrame()
    rows: list[dict[str, object]] = []
    runs = {run.run_id: run for run in exact_change_runs(daily_series)}
    for run_id, group in detections.groupby("run_id", sort=True):
        run = runs[run_id]
        start = run.frame["local_date"].min()
        end = run.frame["local_date"].max()
        metadata = _metadata_dates(run.target_id, start, end)
        high_threshold = float(run.frame["value"].abs().quantile(0.95))
        high_dates = run.frame.loc[
            run.frame["value"].abs().gt(high_threshold), "local_date"
        ].tolist()
        event_context = [
            (pd.Timestamp(item), "phase3_rain_selected_event")
            for item in PHASE3_RAIN_EVENTS
        ]
        event_context.extend(
            (pd.Timestamp(item), "run_q95_displacement_episode") for item in high_dates
        )
        for cluster_number, cluster in enumerate(_cluster_dates(group["candidate_date"]), start=1):
            cluster_start = min(cluster)
            cluster_end = max(cluster)
            representative_ns = int(np.median([item.value for item in cluster]))
            representative = pd.Timestamp(representative_ns)
            supported = group.loc[
                pd.to_datetime(group["candidate_date"]).between(cluster_start, cluster_end)
            ]
            setting_count = supported[["method", "setting"]].drop_duplicates().shape[0]
            methods = sorted(supported["method"].unique())
            if setting_count >= 2 and len(methods) >= 2:
                stability = "method_stable"
            elif setting_count >= 2:
                stability = "within_method_only"
            else:
                stability = "unstable"
            context_date, context_label, offset = _nearest_context(representative, metadata)
            if context_date is not None:
                classification = "metadata_aligned"
            else:
                context_date, context_label, offset = _nearest_context(
                    representative, event_context
                )
                classification = "event_aligned" if context_date is not None else "unexplained"
            rows.append(
                {
                    "candidate_group_id": f"{run_id}__c{cluster_number:02d}",
                    "run_id": run_id,
                    "window_id": run.window_id,
                    "target_id": run.target_id,
                    "segment_id": run.segment_id,
                    "water_year": run.water_year,
                    "candidate_date": representative.date().isoformat(),
                    "candidate_date_range_start": cluster_start.date().isoformat(),
                    "candidate_date_range_end": cluster_end.date().isoformat(),
                    "supporting_setting_count": setting_count,
                    "supporting_methods": ";".join(methods),
                    "sensitivity_stability": stability,
                    "context_classification": classification,
                    "nearest_context_date": (
                        context_date.date().isoformat() if context_date is not None else "none"
                    ),
                    "nearest_context_type": context_label,
                    "context_offset_days": offset if offset is not None else "not_applicable",
                    "interpretation_limit": (
                        "statistical_candidate_not_a_physical_slope_regime_claim"
                    ),
                }
            )
    return pd.DataFrame(rows)
