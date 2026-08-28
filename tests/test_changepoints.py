from __future__ import annotations

import numpy as np
import pandas as pd

from geotech_ts.changepoints import detect_changepoints, exact_change_runs


def _target_rows(start: str, periods: int, water_year: int, values: np.ndarray) -> pd.DataFrame:
    dates = pd.date_range(start, periods=periods, freq="D")
    return pd.DataFrame(
        {
            "local_date": dates,
            "sensor_id": "mid_E2_B",
            "transformation": "daily_first_difference",
            "analysis_eligible": True,
            "value": values,
            "installation_segment_id": "mid_E2_B_s06_hx_vpa_400_27090342",
            "water_year": water_year,
        }
    )


def test_exact_changepoint_runs_never_join_water_years_or_gaps() -> None:
    first = _target_rows("2009-02-13", 200, 2009, np.zeros(200))
    second = _target_rows("2009-10-02", 200, 2010, np.ones(200))
    frame = pd.concat([first, second], ignore_index=True)

    runs = exact_change_runs(frame)

    assert len(runs) == 2
    assert {run.water_year for run in runs} == {2009, 2010}
    assert all(len(run.frame) == 200 for run in runs)


def test_changepoint_sensitivity_detects_synthetic_mean_shift() -> None:
    rng = np.random.default_rng(170)
    values = rng.normal(0, 0.2, 300)
    values[150:] += 3
    frame = _target_rows("2009-10-02", 300, 2010, values)

    detections, run_summary = detect_changepoints(frame)

    detected_dates = pd.to_datetime(detections["candidate_date"])
    expected = pd.Timestamp("2010-03-01")
    assert (detected_dates.sub(expected).dt.days.abs() <= 7).any()
    assert run_summary.iloc[0]["sensitivity_setting_count"] == 6
