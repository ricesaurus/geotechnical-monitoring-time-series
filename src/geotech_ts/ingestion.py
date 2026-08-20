"""Sensor-aware ingestion for Cleveland Corral monitoring products."""

from __future__ import annotations

import csv
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import timedelta, timezone
from io import TextIOWrapper
from pathlib import Path

import numpy as np
import pandas as pd

from geotech_ts.archives import PREAMBLE_LINE_COUNT, product_type_from_archive
from geotech_ts.sensor_events import (
    DOCUMENTED_INTERVALS,
    PHASE2_SENSOR_IDS,
    SEGMENT_STARTS,
    SENSOR_OPERATING_DATES,
)

FIXED_PST = timezone(timedelta(hours=-8), name="PST")
COMMON_SENTINEL_CANDIDATES = frozenset({-9999.0, -999.0, -99.99, 999.0, 9999.0})
NONFINITE_TOKENS = frozenset({"nan", "+nan", "-nan", "inf", "+inf", "-inf", "infinity"})

# These are concern limits taken from the official sensor table. Pressure-transducer
# psi ranges are converted to centimetres of water only for transparent range flags.
PSI_TO_CM_WATER = 70.3069578296
SENSOR_CONCERN_RANGES: dict[str, tuple[float | None, float | None]] = {
    "mid_E2_B": (0.0, 1016.0),
    "mid_P1": (0.0, 15 * PSI_TO_CM_WATER),
    "mid_P2": (0.0, 15 * PSI_TO_CM_WATER),
    "mid_P5": (0.0, 10 * PSI_TO_CM_WATER),
    "mid_P6": (0.0, 10 * PSI_TO_CM_WATER),
    "mid_R": (0.0, None),
    "toe_E5_C": (0.0, 1016.0),
    "toe_P7_B": (0.0, 15 * PSI_TO_CM_WATER),
    "toe_P8_C": (0.0, 5 * PSI_TO_CM_WATER),
    "toe_P8_D": (0.0, 5 * PSI_TO_CM_WATER),
    "toe_P9_D": (0.0, 5 * PSI_TO_CM_WATER),
    "toe_M1_A": (0.0, 100.0),
    "toe_M1_B": (0.0, 100.0),
}


class IngestionError(RuntimeError):
    """Raised when a raw product does not match the verified schema contract."""


def sensor_id_from_column(column: str, sensor_ids: Iterable[str]) -> str | None:
    """Match a measurement column to an official ID without splitting ID suffixes."""

    matches = [sensor_id for sensor_id in sensor_ids if column.endswith(f"_{sensor_id}")]
    if len(matches) > 1:
        raise IngestionError(f"Ambiguous sensor ID in column {column!r}: {matches}")
    return matches[0] if matches else None


def measurement_role(
    product_type: str,
    sensor_id: str,
    source_column: str,
    sensor_field_ordinal: int = 1,
) -> str:
    """Retain the distinct semantics of raw and daily product columns."""

    if product_type == "daily":
        return "daily_rainfall_maximum" if sensor_id == "mid_R" else "daily_median"
    if sensor_id == "mid_R":
        return "cumulative_precipitation" if sensor_field_ordinal == 2 else "interval_precipitation"
    return "15_minute_observation"


def _station_from_member(member: str) -> str:
    folded = Path(member).name.casefold()
    for station in ("middle", "toe", "upper"):
        if station in folded:
            return station
    raise IngestionError(f"Cannot identify station for member {member}")


def _timestamp_frame(original: pd.Series, product_type: str) -> pd.DataFrame:
    expected_minutes = 15 if product_type == "15_minute" else 24 * 60
    timestamp_format = "%m/%d/%Y %H:%M" if product_type == "15_minute" else "%m/%d/%Y"
    parsed = pd.to_datetime(original, format=timestamp_format, errors="coerce")
    valid = parsed.notna()
    fixed_pst = parsed.dt.tz_localize(FIXED_PST)
    timestamp_utc = fixed_pst.dt.tz_convert("UTC")

    delta_minutes = parsed.diff().dt.total_seconds().div(60)
    off_grid = (
        valid
        & delta_minutes.gt(0)
        & delta_minutes.mod(expected_minutes).ne(0)
    )

    positive_delta = delta_minutes.gt(0)
    missing_before = np.floor(delta_minutes.div(expected_minutes)).sub(1)
    missing_before = missing_before.where(delta_minutes.gt(expected_minutes), 0).clip(lower=0)
    local_year = parsed.dt.year.astype("Int64")
    water_year = local_year.where(parsed.dt.month.lt(10), local_year + 1)
    return pd.DataFrame(
        {
            "timestamp_original": original,
            "timestamp_pst_fixed": fixed_pst,
            "timestamp_utc": timestamp_utc,
            "water_year": water_year,
            "expected_interval_minutes": expected_minutes,
            "delta_minutes_from_previous_source_row": delta_minutes,
            "missing_expected_intervals_before": missing_before.astype("Int64"),
            "flag_timestamp_parse_failure": ~valid,
            "flag_duplicate_timestamp_in_member": valid & parsed.duplicated(keep=False),
            "flag_off_grid_timestamp": off_grid,
            "flag_irregular_timestamp_step": valid
            & delta_minutes.notna()
            & delta_minutes.ne(expected_minutes),
            "flag_gap_before": valid & delta_minutes.gt(expected_minutes),
            "flag_out_of_order_timestamp": valid & ~positive_delta & delta_minutes.lt(0),
        }
    )


def _read_member(
    archive_path: Path,
    archive: zipfile.ZipFile,
    member: str,
    selected_sensor_ids: tuple[str, ...],
) -> pd.DataFrame:
    product_type = product_type_from_archive(archive_path)
    with archive.open(member, "r") as binary:
        with TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text:
            for _ in range(PREAMBLE_LINE_COUNT):
                text.readline()
            header = next(csv.reader([text.readline()]))
    expected_timestamp = "date_time_PST" if product_type == "15_minute" else "date"
    if not header or header[0] != expected_timestamp:
        raise IngestionError(f"Unexpected timestamp column in {member}")
    duplicate_official_columns = {
        name for name, count in Counter(header).items() if count > 1
    }
    for duplicate in duplicate_official_columns:
        duplicate_sensor = sensor_id_from_column(duplicate, selected_sensor_ids)
        if product_type != "15_minute" or duplicate_sensor != "mid_R":
            raise IngestionError(f"Unsupported duplicate CSV column in {member}: {duplicate}")

    internal_columns = [f"source_field_{position:03d}" for position in range(len(header))]
    with archive.open(member, "r") as handle:
        wide = pd.read_csv(
            handle,
            skiprows=PREAMBLE_LINE_COUNT + 1,
            header=None,
            names=internal_columns,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="error",
        )

    field_metadata: dict[str, tuple[str, int, str, int]] = {}
    sensor_ordinals: defaultdict[str, int] = defaultdict(int)
    source_fields: list[str] = []
    for position, (internal, official) in enumerate(
        zip(internal_columns[1:], header[1:], strict=True), start=2
    ):
        sensor_id = sensor_id_from_column(official, selected_sensor_ids)
        if sensor_id is None:
            continue
        sensor_ordinals[sensor_id] += 1
        field_metadata[internal] = (official, position, sensor_id, sensor_ordinals[sensor_id])
        source_fields.append(internal)
    if not source_fields:
        return pd.DataFrame()

    timestamps = _timestamp_frame(wide[internal_columns[0]], product_type)
    timestamps["source_row_number"] = np.arange(len(wide), dtype=np.int64) + 5
    timestamps["source_archive"] = archive_path.name
    timestamps["source_member"] = member
    timestamps["product_type"] = product_type
    timestamps["station"] = _station_from_member(member)
    indexed = pd.concat([timestamps, wide[source_fields]], axis=1)
    identifier_columns = list(timestamps.columns)
    long = indexed.melt(
        id_vars=identifier_columns,
        value_vars=source_fields,
        var_name="source_field_internal",
        value_name="value_original",
    )
    long["source_column"] = long["source_field_internal"].map(
        lambda field: field_metadata[field][0]
    )
    long["source_column_position"] = long["source_field_internal"].map(
        lambda field: field_metadata[field][1]
    )
    long["sensor_id"] = long["source_field_internal"].map(lambda field: field_metadata[field][2])
    long["source_sensor_field_ordinal"] = long["source_field_internal"].map(
        lambda field: field_metadata[field][3]
    )
    long["measurement_role"] = [
        measurement_role(product_type, sensor_id, column, ordinal)
        for sensor_id, column, ordinal in zip(
            long["sensor_id"],
            long["source_column"],
            long["source_sensor_field_ordinal"],
            strict=True,
        )
    ]
    long = long.drop(columns="source_field_internal")
    return long


def _apply_value_quality_flags(frame: pd.DataFrame) -> None:
    original = frame["value_original"].astype(str)
    stripped = original.str.strip()
    folded = stripped.str.casefold()
    numeric = pd.to_numeric(stripped, errors="coerce")
    frame["value"] = numeric
    frame["flag_missing_value"] = stripped.eq("")
    frame["flag_nonfinite_value"] = folded.isin(NONFINITE_TOKENS) | np.isinf(numeric)
    frame["flag_malformed_value"] = (
        ~frame["flag_missing_value"]
        & numeric.isna()
        & ~frame["flag_nonfinite_value"]
    )
    frame["flag_sentinel_candidate"] = numeric.isin(COMMON_SENTINEL_CANDIDATES)
    frame["flag_metadata_range_concern"] = False
    for sensor_id, (lower, upper) in SENSOR_CONCERN_RANGES.items():
        sensor_rows = frame["sensor_id"].eq(sensor_id) & numeric.notna()
        concern = pd.Series(False, index=frame.index)
        if lower is not None:
            concern |= numeric.lt(lower)
        if upper is not None:
            concern |= numeric.gt(upper)
        frame.loc[sensor_rows, "flag_metadata_range_concern"] = concern[sensor_rows]


def _apply_documented_events(frame: pd.DataFrame) -> None:
    local = frame["timestamp_pst_fixed"].dt.tz_localize(None)
    frame["installation_segment_id"] = "outside_documented_operation"
    frame["documented_event_flags"] = ""
    frame["flag_documented_change_boundary"] = False
    frame["flag_documented_maintenance_or_outage"] = False
    frame["flag_sly_park_estimate"] = False
    frame["flag_toe_e5_topple_or_relocation"] = False

    for sensor_id, segments in SEGMENT_STARTS.items():
        sensor_rows = frame["sensor_id"].eq(sensor_id) & local.notna()
        for segment in segments:
            start = pd.Timestamp(segment.start_date)
            frame.loc[sensor_rows & local.ge(start), "installation_segment_id"] = segment.segment_id
            boundary = sensor_rows & local.dt.date.eq(segment.start_date)
            frame.loc[boundary, "flag_documented_change_boundary"] = True
            frame.loc[boundary, "documented_event_flags"] = segment.reason

    for sensor_id, (start_date, end_date) in SENSOR_OPERATING_DATES.items():
        sensor_rows = frame["sensor_id"].eq(sensor_id) & local.notna()
        outside = sensor_rows & (
            local.lt(pd.Timestamp(start_date))
            | local.ge(pd.Timestamp(end_date) + pd.Timedelta(days=1))
        )
        frame.loc[outside, "installation_segment_id"] = "outside_documented_operation"

    for sensor_id, intervals in DOCUMENTED_INTERVALS.items():
        sensor_rows = frame["sensor_id"].eq(sensor_id) & local.notna()
        for interval in intervals:
            selected = (
                sensor_rows
                & local.ge(pd.Timestamp(interval.start_date))
                & local.lt(pd.Timestamp(interval.end_date_exclusive))
            )
            frame.loc[selected, "flag_documented_maintenance_or_outage"] = True
            existing = frame.loc[selected, "documented_event_flags"]
            frame.loc[selected, "documented_event_flags"] = np.where(
                existing.eq(""), interval.flag_name, existing + ";" + interval.flag_name
            )
            if interval.flag_name == "mid_R_sly_park_estimate":
                frame.loc[selected, "flag_sly_park_estimate"] = True
            if interval.flag_name == "toe_E5_C_topple_to_relocation":
                frame.loc[selected, "flag_toe_e5_topple_or_relocation"] = True


def _apply_cumulative_quality_flags(frame: pd.DataFrame) -> None:
    cumulative = frame["measurement_role"].isin(
        {"cumulative_precipitation", "daily_rainfall_maximum"}
    ) | frame["sensor_id"].isin({"mid_E2_B", "toe_E5_C"})
    frame["is_cumulative_source_series"] = cumulative
    frame["value_change_from_previous_source_row"] = np.nan
    frame["flag_water_year_boundary"] = False
    frame["flag_water_year_reset"] = False
    frame["flag_negative_increment"] = False
    frame["flag_unexplained_negative_increment"] = False

    selected = frame.loc[cumulative].sort_values(
        ["product_type", "sensor_id", "measurement_role", "timestamp_utc", "source_row_number"]
    )
    group_columns = ["product_type", "sensor_id", "measurement_role"]
    previous_value = selected.groupby(group_columns, sort=False)["value"].shift()
    previous_water_year = selected.groupby(group_columns, sort=False)["water_year"].shift()
    change = selected["value"] - previous_value
    boundary = (
        previous_water_year.notna() & selected["water_year"].ne(previous_water_year)
    ).fillna(False)
    negative = change.lt(0)
    frame.loc[selected.index, "value_change_from_previous_source_row"] = change
    frame.loc[selected.index, "flag_water_year_boundary"] = boundary
    frame.loc[selected.index, "flag_water_year_reset"] = boundary & negative
    frame.loc[selected.index, "flag_negative_increment"] = negative
    explained = (
        boundary
        | selected["flag_documented_change_boundary"]
        | selected["flag_documented_maintenance_or_outage"]
        | selected["flag_gap_before"]
    )
    frame.loc[selected.index, "flag_unexplained_negative_increment"] = negative & ~explained


def read_monitoring_archive(
    archive_path: Path, selected_sensor_ids: Iterable[str] = PHASE2_SENSOR_IDS
) -> pd.DataFrame:
    """Parse selected official IDs from an archive and attach transparent QC flags."""

    selected = tuple(selected_sensor_ids)
    unknown = sorted(set(selected) - set(SENSOR_OPERATING_DATES))
    if unknown:
        raise IngestionError(f"No operating metadata configured for sensors: {unknown}")
    with zipfile.ZipFile(archive_path, "r") as archive:
        corrupt_member = archive.testzip()
        if corrupt_member is not None:
            raise IngestionError(f"ZIP CRC failure in member: {corrupt_member}")
        frames = [
            _read_member(archive_path, archive, info.filename, selected)
            for info in archive.infolist()
            if not info.is_dir() and info.filename.casefold().endswith(".csv")
        ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        raise IngestionError(f"No selected sensor columns found in {archive_path.name}")
    combined = pd.concat(frames, ignore_index=True)
    valid_timestamp = combined["timestamp_utc"].notna()
    combined["flag_duplicate_timestamp"] = False
    duplicate_columns = ["product_type", "sensor_id", "measurement_role", "timestamp_utc"]
    combined.loc[valid_timestamp, "flag_duplicate_timestamp"] = combined.loc[
        valid_timestamp
    ].duplicated(duplicate_columns, keep=False)
    _apply_value_quality_flags(combined)
    _apply_documented_events(combined)
    _apply_cumulative_quality_flags(combined)
    return combined
