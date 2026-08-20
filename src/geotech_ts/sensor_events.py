"""Documented installation regimes and maintenance intervals for Phase 2 sensors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SegmentStart:
    """A documented start of a distinct sensor or acquisition regime."""

    start_date: date
    segment_id: str
    reason: str


@dataclass(frozen=True)
class DocumentedInterval:
    """A half-open local-date interval with a documented data concern."""

    start_date: date
    end_date_exclusive: date
    flag_name: str
    description: str


SENSOR_OPERATING_DATES: dict[str, tuple[date, date]] = {
    "mid_E2_B": (date(2002, 10, 18), date(2018, 9, 25)),
    "mid_P1": (date(1997, 10, 16), date(2018, 9, 25)),
    "mid_P2": (date(1997, 10, 16), date(2018, 9, 25)),
    "mid_P5": (date(2013, 2, 5), date(2018, 9, 25)),
    "mid_P6": (date(2011, 10, 26), date(2018, 9, 25)),
    "mid_R": (date(1997, 3, 22), date(2018, 9, 25)),
    "toe_E5_C": (date(2006, 11, 30), date(2017, 9, 25)),
    "toe_P7_B": (date(2005, 6, 15), date(2017, 9, 25)),
    "toe_P8_C": (date(2013, 2, 6), date(2017, 3, 2)),
    "toe_P8_D": (date(2017, 3, 9), date(2017, 9, 25)),
    "toe_P9_D": (date(2013, 2, 5), date(2017, 9, 25)),
    "toe_M1_A": (date(2006, 11, 1), date(2017, 5, 17)),
    "toe_M1_B": (date(2017, 5, 17), date(2017, 9, 25)),
}


SEGMENT_STARTS: dict[str, tuple[SegmentStart, ...]] = {
    "mid_E2_B": (
        SegmentStart(date(2002, 10, 18), "mid_E2_B_s01_hx_pa_400_29030259", "installation"),
        SegmentStart(date(2005, 11, 29), "mid_E2_B_s02_hx_vpa_400_27090342", "replacement"),
        SegmentStart(date(2007, 6, 12), "mid_E2_B_s03_hx_pa_400_29030259", "replacement"),
        SegmentStart(date(2008, 1, 11), "mid_E2_B_s04_hx_vpa_400_27090342", "replacement"),
        SegmentStart(date(2008, 4, 24), "mid_E2_B_s05_hx_pa_400_29030259", "replacement"),
        SegmentStart(date(2009, 2, 12), "mid_E2_B_s06_hx_vpa_400_27090342", "replacement"),
        SegmentStart(
            date(2016, 6, 1),
            "mid_E2_B_s07_hx_pa_400_39070751",
            "broken cable and replacement",
        ),
    ),
    "mid_P1": (
        SegmentStart(date(1997, 10, 16), "mid_P1_s01_usgs5_depth_1_79m", "installation"),
        SegmentStart(date(2006, 5, 4), "mid_P1_s02_usgsct2_depth_1_82m", "sensor replacement"),
    ),
    "mid_P2": (
        SegmentStart(date(1997, 10, 16), "mid_P2_s01_usgs6_depth_3_69m", "installation"),
    ),
    "mid_P5": (
        SegmentStart(date(2013, 2, 5), "mid_P5_s01_sensor_2631015", "installation"),
        SegmentStart(
            date(2014, 11, 11),
            "mid_P5_s02_replacement_amplifier",
            "amplifier replacement",
        ),
        SegmentStart(date(2016, 11, 18), "mid_P5_s03_sensor_2631016", "sensor replacement"),
    ),
    "mid_P6": (
        SegmentStart(date(2011, 10, 26), "mid_P6_s01_sensor_2631022", "installation"),
    ),
    "mid_R": (
        SegmentStart(date(1997, 3, 22), "mid_R_s01_pre_fire", "installation"),
        SegmentStart(date(2002, 10, 18), "mid_R_s02_post_fire", "site rebuilt after fire"),
        SegmentStart(date(2016, 1, 27), "mid_R_s03_post_mechanical_failure", "gauge resumed"),
        SegmentStart(date(2017, 5, 18), "mid_R_s04_range_not_stated", "metadata regime start"),
    ),
    "toe_E5_C": (
        SegmentStart(date(2006, 11, 30), "toe_E5_C_s01_pre_topple", "installation"),
        SegmentStart(
            date(2017, 3, 16),
            "toe_E5_C_s02_topple_removed",
            "post toppled; event removed",
        ),
        SegmentStart(date(2017, 4, 25), "toe_E5_C_s03_post_relocation", "post relocated"),
    ),
    "toe_P7_B": (
        SegmentStart(date(2005, 6, 15), "toe_P7_B_s01_relocated_depth_1_03m", "new location"),
    ),
    "toe_P8_C": (
        SegmentStart(date(2013, 2, 6), "toe_P8_C_s01_relocated_depth_2_36m", "new location"),
    ),
    "toe_P8_D": (
        SegmentStart(
            date(2017, 3, 9),
            "toe_P8_D_s01_new_location_depth_1_62m",
            "new location and sensor",
        ),
    ),
    "toe_P9_D": (
        SegmentStart(date(2013, 2, 5), "toe_P9_D_s01_relocated_depth_4_45m", "new location"),
    ),
    "toe_M1_A": (
        SegmentStart(date(2006, 11, 1), "toe_M1_A_s01", "installation"),
    ),
    "toe_M1_B": (
        SegmentStart(date(2017, 5, 17), "toe_M1_B_s01_replacement", "replacement sensor"),
    ),
}


DOCUMENTED_INTERVALS: dict[str, tuple[DocumentedInterval, ...]] = {
    "mid_E2_B": (
        DocumentedInterval(
            date(2007, 6, 8),
            date(2007, 6, 12),
            "mid_E2_B_replacement_gap",
            "broken instrument interval before replacement resumed",
        ),
    ),
    "mid_P1": (
        DocumentedInterval(
            date(2006, 4, 27),
            date(2006, 5, 4),
            "mid_P1_replacement_gap",
            "interval between documented sensor installations",
        ),
    ),
    "mid_R": (
        DocumentedInterval(
            date(2002, 7, 26),
            date(2002, 10, 18),
            "mid_R_fire_outage",
            "site destroyed by St. Pauli fire",
        ),
        DocumentedInterval(
            date(2016, 1, 22),
            date(2016, 1, 28),
            "mid_R_sly_park_estimate",
            "rainfall from January 22 through January 27 estimated from Sly Park gauge",
        ),
    ),
    "toe_E5_C": (
        DocumentedInterval(
            date(2017, 3, 16),
            date(2017, 4, 25),
            "toe_E5_C_topple_to_relocation",
            "post toppled; topple event removed before post relocation",
        ),
    ),
}


PHASE2_SENSOR_IDS = (
    "mid_R",
    "mid_P1",
    "mid_P2",
    "mid_E2_B",
    "mid_P5",
    "mid_P6",
    "toe_M1_A",
    "toe_M1_B",
    "toe_P7_B",
    "toe_E5_C",
    "toe_P8_C",
    "toe_P8_D",
    "toe_P9_D",
)
