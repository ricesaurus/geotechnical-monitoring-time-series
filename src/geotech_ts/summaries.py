"""Metadata-only summaries derived from quality-flagged monitoring records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from functools import reduce

import numpy as np
import pandas as pd

SUMMARY_FLAG_COLUMNS = (
    "flag_timestamp_parse_failure",
    "flag_duplicate_timestamp_in_member",
    "flag_duplicate_timestamp",
    "flag_off_grid_timestamp",
    "flag_irregular_timestamp_step",
    "flag_gap_before",
    "flag_out_of_order_timestamp",
    "flag_missing_value",
    "flag_nonfinite_value",
    "flag_malformed_value",
    "flag_sentinel_candidate",
    "flag_metadata_range_concern",
    "flag_documented_change_boundary",
    "flag_documented_maintenance_or_outage",
    "flag_sly_park_estimate",
    "flag_toe_e5_topple_or_relocation",
    "flag_water_year_boundary",
    "flag_water_year_reset",
    "flag_negative_increment",
    "flag_unexplained_negative_increment",
)


@dataclass(frozen=True)
class CandidateDefinition:
    """A compatibility set that never merges successor installation IDs."""

    candidate_id: str
    sensor_ids: tuple[str, ...]
    start_date: date | None = None
    end_date_exclusive: date | None = None


CANDIDATE_DEFINITIONS = (
    CandidateDefinition("middle_core", ("mid_R", "mid_P1", "mid_P2", "mid_E2_B")),
    CandidateDefinition(
        "toe_core_pre_topple",
        ("mid_R", "toe_M1_A", "toe_P7_B", "toe_E5_C"),
        end_date_exclusive=date(2017, 3, 16),
    ),
    CandidateDefinition(
        "toe_core_successor_period",
        ("mid_R", "toe_M1_B", "toe_P7_B", "toe_E5_C"),
        start_date=date(2017, 5, 17),
    ),
    CandidateDefinition("middle_late_deep", ("mid_R", "mid_P5", "mid_P6", "mid_E2_B")),
    CandidateDefinition(
        "toe_late_deep_pre_topple",
        ("mid_R", "toe_M1_A", "toe_P8_C", "toe_P9_D", "toe_E5_C"),
        end_date_exclusive=date(2017, 3, 2),
    ),
    CandidateDefinition(
        "toe_late_deep_successor_period",
        ("mid_R", "toe_M1_B", "toe_P8_D", "toe_P9_D", "toe_E5_C"),
        start_date=date(2017, 5, 17),
    ),
)


def _pst_iso(value: pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return "not_available"
    return value.isoformat()


def coverage_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize actual nonmissing coverage and QC counts without observations."""

    group_columns = [
        "product_type",
        "sensor_id",
        "measurement_role",
        "installation_segment_id",
    ]
    rows: list[dict[str, object]] = []
    for keys, group in frame.groupby(group_columns, dropna=False, sort=True):
        nonmissing = group.loc[~group["flag_missing_value"] & group["value"].notna()]
        valid_times = group["timestamp_pst_fixed"].dropna()
        nonmissing_times = nonmissing["timestamp_pst_fixed"].dropna()
        phases = sorted({timestamp.strftime("%H:%M")[-2:] for timestamp in valid_times})
        row: dict[str, object] = dict(zip(group_columns, keys, strict=True))
        row.update(
            {
                "source_member_count": int(group["source_member"].nunique()),
                "row_count": int(len(group)),
                "parsed_timestamp_count": int(group["timestamp_pst_fixed"].notna().sum()),
                "nonmissing_value_count": int(len(nonmissing)),
                "missing_value_count": int(group["flag_missing_value"].sum()),
                "missing_value_percent": round(100 * group["flag_missing_value"].mean(), 6),
                "first_source_timestamp_pst": _pst_iso(valid_times.min()),
                "last_source_timestamp_pst": _pst_iso(valid_times.max()),
                "first_nonmissing_timestamp_pst": _pst_iso(nonmissing_times.min()),
                "last_nonmissing_timestamp_pst": _pst_iso(nonmissing_times.max()),
                "observed_clock_minute_phases": ";".join(phases),
                "missing_expected_interval_count": int(
                    group["missing_expected_intervals_before"].fillna(0).sum()
                ),
            }
        )
        row.update({f"{column}_count": int(group[column].sum()) for column in SUMMARY_FLAG_COLUMNS})
        rows.append(row)
    return pd.DataFrame(rows).sort_values(group_columns).reset_index(drop=True)


def _preferred_series(frame: pd.DataFrame, product_type: str, sensor_id: str) -> pd.DataFrame:
    selected = frame.loc[
        frame["product_type"].eq(product_type)
        & frame["sensor_id"].eq(sensor_id)
        & ~frame["flag_missing_value"]
        & frame["value"].notna()
        & frame["timestamp_pst_fixed"].notna()
    ]
    preferred_role = (
        "cumulative_precipitation"
        if product_type == "15_minute" and sensor_id == "mid_R"
        else "daily_rainfall_maximum"
        if product_type == "daily" and sensor_id == "mid_R"
        else "15_minute_observation"
        if product_type == "15_minute"
        else "daily_median"
    )
    return selected.loc[
        selected["measurement_role"].eq(preferred_role), ["timestamp_pst_fixed", "value"]
    ]


def compatibility_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Report actual overlap and exact-grid compatibility for candidate sets."""

    rows: list[dict[str, object]] = []
    for candidate in CANDIDATE_DEFINITIONS:
        for product_type in sorted(frame["product_type"].unique()):
            series: list[pd.DataFrame] = []
            per_sensor_times: list[pd.DatetimeIndex] = []
            phase_parts: list[str] = []
            for sensor_id in candidate.sensor_ids:
                sensor = _preferred_series(frame, product_type, sensor_id).copy()
                local = sensor["timestamp_pst_fixed"].dt.tz_localize(None)
                if candidate.start_date is not None:
                    sensor = sensor.loc[local.ge(pd.Timestamp(candidate.start_date))]
                if candidate.end_date_exclusive is not None:
                    local = sensor["timestamp_pst_fixed"].dt.tz_localize(None)
                    sensor = sensor.loc[local.lt(pd.Timestamp(candidate.end_date_exclusive))]
                series.append(sensor)
                per_sensor_times.append(pd.DatetimeIndex(sensor["timestamp_pst_fixed"].unique()))
                phases = sorted(sensor["timestamp_pst_fixed"].dt.strftime("%M").unique())
                phase_parts.append(f"{sensor_id}={'|'.join(phases) if phases else 'none'}")

            starts = [sensor["timestamp_pst_fixed"].min() for sensor in series if not sensor.empty]
            ends = [sensor["timestamp_pst_fixed"].max() for sensor in series if not sensor.empty]
            all_present = len(starts) == len(candidate.sensor_ids)
            common = (
                reduce(lambda left, right: left.intersection(right), per_sensor_times)
                if all_present
                else pd.DatetimeIndex([])
            )
            sites = {
                "middle" if sensor_id.startswith("mid_") else "toe"
                for sensor_id in candidate.sensor_ids
            }
            if not all_present:
                alignment_note = "one_or_more_series_have_no_nonmissing_values"
            elif common.empty and product_type == "15_minute" and len(sites) > 1:
                alignment_note = "different_station_clock_phases_no_exact_timestamp_join"
            elif common.empty:
                alignment_note = "no_exact_common_nonmissing_timestamp"
            else:
                alignment_note = "exact_common_timestamps_available"
            rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "product_type": product_type,
                    "sensor_ids": "; ".join(candidate.sensor_ids),
                    "selection_start_constraint": candidate.start_date.isoformat()
                    if candidate.start_date
                    else "not_applicable",
                    "selection_end_exclusive_constraint": candidate.end_date_exclusive.isoformat()
                    if candidate.end_date_exclusive
                    else "not_applicable",
                    "all_series_have_nonmissing_values": all_present,
                    "common_window_start_pst": _pst_iso(max(starts) if all_present else None),
                    "common_window_end_pst": _pst_iso(min(ends) if all_present else None),
                    "exact_common_nonmissing_timestamp_count": len(common),
                    "clock_minute_phases_by_sensor": "; ".join(phase_parts),
                    "alignment_note": alignment_note,
                }
            )
    return pd.DataFrame(rows)


def daily_relationship_summary(
    fifteen_minute: pd.DataFrame, daily: pd.DataFrame
) -> pd.DataFrame:
    """Test the documented daily aggregations against the 15-minute product."""

    rows: list[dict[str, object]] = []
    sensor_ids = sorted(set(fifteen_minute["sensor_id"]) & set(daily["sensor_id"]))
    for sensor_id in sensor_ids:
        daily_sensor = _preferred_series(daily, "daily", sensor_id).copy()
        daily_sensor["local_date"] = daily_sensor["timestamp_pst_fixed"].dt.date
        daily_duplicates = int(daily_sensor["local_date"].duplicated(keep=False).sum())
        daily_by_date = daily_sensor.groupby("local_date", sort=True)["value"].first()

        if sensor_id == "mid_R":
            tests = (
                ("interval_precipitation", "maximum"),
                ("cumulative_precipitation", "maximum"),
            )
        else:
            tests = (("15_minute_observation", "median"),)

        for source_role, aggregation in tests:
            source = fifteen_minute.loc[
                fifteen_minute["sensor_id"].eq(sensor_id)
                & fifteen_minute["measurement_role"].eq(source_role)
                & fifteen_minute["value"].notna()
                & fifteen_minute["timestamp_pst_fixed"].notna()
            ].copy()
            source["local_date"] = source["timestamp_pst_fixed"].dt.date
            grouped = source.groupby("local_date", sort=True)["value"]
            aggregated = grouped.max() if aggregation == "maximum" else grouped.median()
            comparison = pd.concat(
                [daily_by_date.rename("daily"), aggregated.rename("recalculated")], axis=1
            ).dropna()
            matches = np.isclose(
                comparison["daily"], comparison["recalculated"], rtol=0, atol=1e-12
            )
            mismatch_years = sorted(
                {local_date.year for local_date in comparison.index[~matches]}
            )
            maximum_absolute_difference = (
                round(
                    float((comparison["daily"] - comparison["recalculated"]).abs().max()),
                    12,
                )
                if not comparison.empty
                else np.nan
            )
            rows.append(
                {
                    "sensor_id": sensor_id,
                    "daily_measurement_role": "daily_rainfall_maximum"
                    if sensor_id == "mid_R"
                    else "daily_median",
                    "tested_15_minute_role": source_role,
                    "tested_aggregation": aggregation,
                    "daily_nonmissing_date_count": int(len(daily_by_date)),
                    "fifteen_minute_nonmissing_date_count": int(len(aggregated)),
                    "comparable_date_count": int(len(comparison)),
                    "match_within_1e_12_count": int(matches.sum()),
                    "mismatch_count": int((~matches).sum()),
                    "mismatch_calendar_years": ";".join(map(str, mismatch_years))
                    if mismatch_years
                    else "none",
                    "maximum_absolute_difference": maximum_absolute_difference,
                    "duplicate_daily_date_row_count": daily_duplicates,
                }
            )
    return pd.DataFrame(rows)
