from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from geotech_ts.forecast_metrics import moving_block_mean_ci, synthetic_leakage_demo
from geotech_ts.forecasting import (
    ARIMA_SPECS,
    ArimaxFit,
    ForecastWindow,
    _add_empirical_baseline_intervals,
    _arimax_forecasts,
    _baseline_prediction,
    core_origin_eligible,
    scheduled_origins,
    training_mase_scale,
)


def _grid(start: str, periods: int) -> pd.DataFrame:
    index = pd.date_range(start, periods=periods, freq="D")
    return pd.DataFrame(
        {
            "target_value": np.arange(periods, dtype=float),
            "target_eligible": True,
            "target_segment": "segment_1",
            "target_water_year": 2020,
            "rain_value": np.arange(periods, dtype=float) / 10,
            "rain_eligible": True,
            "rain_segment": "rain_1",
        },
        index=index,
    )


def _window(start: date, end: date, anchor: date) -> ForecastWindow:
    return ForecastWindow(
        "synthetic_window",
        "synthetic_target",
        start,
        end,
        anchor,
        date(2020, 1, 31),
        start,
        "synthetic",
    )


def test_core_origin_path_rejects_gap_and_water_year_reset() -> None:
    grid = _grid("2020-01-01", 20)
    window = _window(date(2020, 1, 1), date(2020, 1, 21), date(2020, 1, 2))
    origin = pd.Timestamp("2020-01-05")

    assert core_origin_eligible(grid, origin, 2, window)

    grid.loc[pd.Timestamp("2020-01-06"), "target_eligible"] = False
    assert not core_origin_eligible(grid, origin, 2, window)

    grid.loc[pd.Timestamp("2020-01-06"), "target_eligible"] = True
    grid.loc[pd.Timestamp("2020-01-07"), "target_water_year"] = 2021
    assert not core_origin_eligible(grid, origin, 2, window)


def test_origin_schedule_never_moves_ineligible_anchor_dates() -> None:
    window = _window(date(2020, 1, 1), date(2020, 2, 15), date(2020, 1, 10))

    origins = scheduled_origins(window)

    assert origins.tolist() == [
        pd.Timestamp("2020-01-10"),
        pd.Timestamp("2020-01-24"),
        pd.Timestamp("2020-02-07"),
    ]


def test_mase_scale_uses_only_exact_same_regime_pairs() -> None:
    training = _grid("2020-01-01", 40)
    training.loc[pd.Timestamp("2020-01-20"), "target_eligible"] = False
    training.loc[pd.Timestamp("2020-01-25") :, "target_segment"] = "segment_2"

    scale = training_mase_scale(training)

    assert scale == 1.0


def test_prior_year_baseline_does_not_map_february_29_to_february_28() -> None:
    grid = _grid("2019-01-01", 500)
    training = grid.loc[: pd.Timestamp("2020-02-20")]

    prediction, status = _baseline_prediction(
        "prior_year_same_date",
        training,
        grid,
        pd.Timestamp("2020-02-20"),
        pd.Timestamp("2020-02-29"),
    )

    assert np.isnan(prediction)
    assert status == "feature_unavailable"


def test_arimax_forecast_uses_only_one_and_two_day_available_rain() -> None:
    grid = _grid("2020-01-01", 20)
    fit = ArimaxFit(
        coefficients=np.array([0.1, 0.5, 0.2]),
        covariance=np.eye(3),
        innovation_variance=1.0,
        equation_count=300,
        warning="none",
    )

    forecasts = _arimax_forecasts(fit, grid, pd.Timestamp("2020-01-10"))

    assert set(forecasts) == {1, 2}
    assert 7 not in forecasts


def test_empirical_baseline_intervals_use_only_realized_past_errors() -> None:
    origins = pd.date_range("2020-01-01", periods=35, freq="14D")
    predictions = pd.DataFrame(
        {
            "window_id": "window",
            "target_id": "target",
            "model_id": "zero_change",
            "horizon_days": 7,
            "status": "ok",
            "origin_date": origins,
            "target_date": origins + pd.Timedelta(days=7),
            "error": np.arange(35, dtype=float),
            "prediction": 0.0,
            "lower_80": np.nan,
            "upper_80": np.nan,
            "lower_95": np.nan,
            "upper_95": np.nan,
            "interval_status": "not_available",
        }
    )

    calibrated = _add_empirical_baseline_intervals(predictions)

    assert calibrated.loc[29, "interval_status"] == "insufficient_past_calibration"
    assert calibrated.loc[30, "interval_status"] == "ok_past_residuals"
    expected_lower = pd.Series(np.arange(30, dtype=float)).quantile(0.10)
    assert np.isclose(calibrated.loc[30, "lower_80"], expected_lower)


def test_arima_candidates_never_difference_change_target_again() -> None:
    assert all(spec.order[1] == 0 for spec in ARIMA_SPECS)
    assert all(spec.seasonal_order[1] == 0 for spec in ARIMA_SPECS)


def test_block_bootstrap_and_synthetic_demo_are_reproducible() -> None:
    first_interval = moving_block_mean_ci(np.arange(30), seed=170)
    second_interval = moving_block_mean_ci(np.arange(30), seed=170)
    first_summary, first_values = synthetic_leakage_demo(seed=170)
    second_summary, second_values = synthetic_leakage_demo(seed=170)

    assert first_interval == second_interval
    pd.testing.assert_frame_equal(first_summary, second_summary)
    pd.testing.assert_frame_equal(first_values, second_values)
    random_row = first_summary.loc[
        first_summary["validation_design"].eq("random_split_leaks_later_regime")
    ].iloc[0]
    assert bool(random_row["training_includes_post_shift"])
    assert set(first_summary["data_origin"]) == {"synthetic_seed_170_not_usgs"}
