from __future__ import annotations

import zipfile
from pathlib import Path

from geotech_ts.archives import inspect_archive
from geotech_ts.ingestion import read_monitoring_archive, sensor_id_from_column
from geotech_ts.summaries import daily_relationship_summary

PREAMBLE = (
    "Synthetic Cleveland Corral fixture\n"
    "U.S. Geological Survey data release: https://doi.org/10.5066/P1P9DMFX\n"
)


def _write_zip(path: Path, member: str, description: str, header: str, rows: list[str]) -> None:
    content = PREAMBLE + description + "\n" + header + "\n" + "\n".join(rows) + "\n"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, content)


def test_archive_inspection_and_fixed_pst_quality_flags(tmp_path: Path) -> None:
    archive_path = tmp_path / "Cleveland_Corral_15_Minute_Data.zip"
    member = "Cleveland_Corral_middle_15minute/CCmiddle_WY2017.csv"
    _write_zip(
        archive_path,
        member,
        "15 minute data for middle station, water year 2017",
        "date_time_PST,mid_downslope_extensometer_cm_mid_E2_B,"
        "mid_precipitation_mm_mid_R,mid_precipitation_mm_mid_R",
        [
            "9/30/2016 23:49,10,0,50",
            "10/1/2016 0:04,0,0,0",
            "10/1/2016 0:19,-1,,9999",
            "10/1/2016 0:19,-1,oops,9999",
            "10/1/2016 0:50,-2,0,9999",
            "7/1/2017 0:05,-2,0,9999",
            "bad timestamp,,0,9999",
        ],
    )

    inspection = inspect_archive(archive_path)
    frame = read_monitoring_archive(archive_path, ["mid_E2_B", "mid_R"])

    assert len(inspection) == 1
    assert inspection[0].timestamp_column == "date_time_PST"
    assert inspection[0].column_count == 4
    assert set(frame["measurement_role"]) == {
        "15_minute_observation",
        "interval_precipitation",
        "cumulative_precipitation",
    }
    assert frame["flag_timestamp_parse_failure"].sum() == 3
    assert frame["flag_duplicate_timestamp"].any()
    assert frame["flag_gap_before"].any()
    assert frame["flag_off_grid_timestamp"].any()
    assert frame["flag_malformed_value"].any()
    assert frame["flag_sentinel_candidate"].any()
    assert frame["flag_metadata_range_concern"].any()
    assert frame["flag_water_year_reset"].any()
    assert frame["flag_unexplained_negative_increment"].any()

    january_or_july = frame.loc[frame["timestamp_original"].eq("7/1/2017 0:05")].iloc[0]
    assert january_or_july["timestamp_utc"].hour == 8


def test_daily_semantics_match_cumulative_rain_maximum_and_sensor_median(
    tmp_path: Path,
) -> None:
    fifteen_path = tmp_path / "Cleveland_Corral_15_Minute_Data.zip"
    daily_path = tmp_path / "Cleveland_Corral_Daily_Data.zip"
    _write_zip(
        fifteen_path,
        "Cleveland_Corral_middle_15minute/CCmiddle_WY2017.csv",
        "15 minute data for middle station, water year 2017",
        "date_time_PST,mid_downslope_extensometer_cm_mid_E2_B,"
        "mid_precipitation_mm_mid_R,mid_cumprecipitation_mm_mid_R",
        ["3/1/2017 0:04,0,0,10", "3/1/2017 0:19,2,1,11"],
    )
    _write_zip(
        daily_path,
        "Cleveland_Corral_Daily_Data/CCmiddle_daily_2002_2018.csv",
        "daily rainfall maxima and daily medians other sensors at middle station",
        "date,mid_downslope_extensometer_cm_mid_E2_B,mid_precipitation_mm_mid_R",
        ["3/1/2017,1,11"],
    )
    fifteen = read_monitoring_archive(fifteen_path, ["mid_E2_B", "mid_R"])
    daily = read_monitoring_archive(daily_path, ["mid_E2_B", "mid_R"])

    summary = daily_relationship_summary(fifteen, daily)
    rain = summary.loc[summary["sensor_id"].eq("mid_R")]
    cumulative = rain.loc[rain["tested_15_minute_role"].eq("cumulative_precipitation")]
    interval = rain.loc[rain["tested_15_minute_role"].eq("interval_precipitation")]
    displacement = summary.loc[summary["sensor_id"].eq("mid_E2_B")]

    assert cumulative.iloc[0]["match_within_1e_12_count"] == 1
    assert interval.iloc[0]["mismatch_count"] == 1
    assert displacement.iloc[0]["match_within_1e_12_count"] == 1


def test_sensor_id_matching_preserves_successor_installations() -> None:
    sensor_ids = ("toe_M1_A", "toe_M1_B")

    assert sensor_id_from_column("toe_volumetric_water_contentA_toe_M1_A", sensor_ids) == "toe_M1_A"
    assert sensor_id_from_column("toe_volumetric_water_contentB_toe_M1_B", sensor_ids) == "toe_M1_B"
    assert sensor_id_from_column("unrelated", sensor_ids) is None
