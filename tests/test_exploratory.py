from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from geotech_ts.exploratory import (
    add_level_eligibility,
    build_daily_analysis_series,
    exact_lag_pairs,
    one_to_one_nearest_alignment,
    select_rain_events,
    synthetic_linear_process_diagnostics,
)


def _quality_rows(
    timestamps: pd.DatetimeIndex,
    sensor_id: str,
    role: str,
    values: list[float | None],
    product_type: str,
    segment: str = "segment_1",
) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp_pst_fixed": timestamps,
            "timestamp_utc": timestamps.tz_convert("UTC"),
            "sensor_id": sensor_id,
            "measurement_role": role,
            "product_type": product_type,
            "value": values,
            "water_year": [2020] * len(timestamps),
            "expected_interval_minutes": 1440 if product_type == "daily" else 15,
            "installation_segment_id": segment,
        }
    )
    for flag in (
        "flag_timestamp_parse_failure",
        "flag_duplicate_timestamp_in_member",
        "flag_duplicate_timestamp",
        "flag_out_of_order_timestamp",
        "flag_missing_value",
        "flag_nonfinite_value",
        "flag_malformed_value",
        "flag_sentinel_candidate",
        "flag_documented_maintenance_or_outage",
        "flag_metadata_range_concern",
        "flag_unexplained_negative_increment",
    ):
        frame[flag] = False
    frame["flag_missing_value"] = frame["value"].isna()
    return frame


def test_level_mask_retains_but_labels_range_concerns() -> None:
    timestamps = pd.date_range("2020-01-01", periods=2, freq="D", tz="Etc/GMT+8")
    frame = _quality_rows(timestamps, "mid_P1", "daily_median", [-2.0, 3.0], "daily")
    frame.loc[0, "flag_metadata_range_concern"] = True

    masked = add_level_eligibility(frame)

    assert masked["analysis_eligible_level"].tolist() == [True, True]
    assert masked["analysis_retains_range_concern"].tolist() == [True, False]


def test_daily_changes_do_not_bridge_missing_dates_or_water_years() -> None:
    dates = pd.DatetimeIndex(
        ["2019-09-29", "2019-09-30", "2019-10-01", "2019-10-03"], tz="Etc/GMT+8"
    )
    rain_daily = _quality_rows(
        dates,
        "mid_R",
        "daily_rainfall_maximum",
        [10.0, 12.0, 0.0, 3.0],
        "daily",
    )
    rain_daily["water_year"] = [2019, 2019, 2020, 2020]
    cumulative_15 = _quality_rows(
        dates + pd.Timedelta(hours=12),
        "mid_R",
        "cumulative_precipitation",
        [10.0, 12.0, 0.0, 3.0],
        "15_minute",
    )
    interval_15 = _quality_rows(
        dates + pd.Timedelta(hours=12),
        "mid_R",
        "interval_precipitation",
        [0.0, 2.0, 0.0, 3.0],
        "15_minute",
    )
    fifteen = pd.concat([cumulative_15, interval_15], ignore_index=True)

    series = build_daily_analysis_series(rain_daily, fifteen, minimum_interval_rain_count=1)
    differences = series.loc[series["transformation"].eq("daily_cumulative_difference")]

    eligibility = dict(
        zip(
            differences["local_date"].dt.date,
            differences["analysis_eligible"],
            strict=True,
        )
    )
    assert eligibility[date(2019, 9, 30)]
    assert not eligibility[date(2019, 10, 1)]
    assert not eligibility[date(2019, 10, 3)]


def test_positive_daily_lag_means_predictor_leads_response() -> None:
    dates = pd.date_range("2020-01-01", periods=5, freq="D")
    predictor = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=dates)
    response = pd.Series([10.0, 1.0, 2.0, 3.0, 4.0], index=dates)

    pairs = exact_lag_pairs(predictor, response, lag_days=1)

    assert pairs["predictor"].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert pairs["response"].tolist() == [1.0, 2.0, 3.0, 4.0]


def test_nearest_alignment_never_reuses_an_observation() -> None:
    predictor = pd.DataFrame(
        {
            "timestamp_pst_fixed": pd.to_datetime(
                ["2020-01-01 00:00", "2020-01-01 00:15"]
            ).tz_localize("Etc/GMT+8"),
            "value": [1.0, 2.0],
        }
    )
    response = pd.DataFrame(
        {
            "timestamp_pst_fixed": pd.to_datetime(
                ["2020-01-01 00:06", "2020-01-01 00:21"]
            ).tz_localize("Etc/GMT+8"),
            "value": [3.0, 4.0],
        }
    )

    matched = one_to_one_nearest_alignment(predictor, response, tolerance_minutes=8)

    assert len(matched) == 2
    assert matched["predictor_index"].is_unique
    assert matched["response_index"].is_unique


def test_event_selection_uses_rain_only_and_enforces_separation() -> None:
    dates = pd.date_range("2020-01-01", periods=12, freq="D")
    series = pd.DataFrame(
        {
            "local_date": dates,
            "sensor_id": "mid_R",
            "transformation": "daily_interval_sum",
            "analysis_eligible": True,
            "value": [0, 10, 9, 0, 0, 0, 0, 8, 0, 0, 0, 7],
            "coverage_count": 96,
        }
    )

    events = select_rain_events(
        series,
        start=date(2020, 1, 1),
        end_exclusive=date(2020, 1, 13),
        event_count=2,
        minimum_separation_days=5,
    )

    assert events["event_date"].dt.date.tolist() == [date(2020, 1, 2), date(2020, 1, 8)]


def test_synthetic_demo_is_reproducible_and_separate_from_usgs() -> None:
    first_values, first_diagnostics = synthetic_linear_process_diagnostics(
        seed=170, sample_size=200, maximum_lag=5
    )
    second_values, second_diagnostics = synthetic_linear_process_diagnostics(
        seed=170, sample_size=200, maximum_lag=5
    )

    pd.testing.assert_frame_equal(first_values, second_values)
    pd.testing.assert_frame_equal(first_diagnostics, second_diagnostics)
    assert set(first_diagnostics["data_origin"]) == {"synthetic_fixed_seed_not_usgs"}
    assert np.isfinite(first_diagnostics[["acf", "pacf"]]).all().all()
