"""Build local quality-flagged outputs and versioned aggregate summaries."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from geotech_ts.ingestion import read_monitoring_archive
from geotech_ts.paths import INTERIM_DATA_DIR, PROJECT_ROOT, RAW_DATA_DIR
from geotech_ts.summaries import (
    compatibility_summary,
    coverage_summary,
    daily_relationship_summary,
)


def _write_csv(frame: pd.DataFrame, relative_path: str) -> None:
    path = PROJECT_ROOT / relative_path
    frame.to_csv(path, index=False, lineterminator="\n")
    print(f"Wrote {len(frame)} aggregate rows: {relative_path}")


def _write_parquet_atomic(frame: pd.DataFrame, path: Path) -> None:
    partial = path.with_name(f"{path.name}.partial")
    if partial.exists():
        raise RuntimeError(f"Inspect interrupted output before retrying: {partial}")
    frame.to_parquet(partial, index=False)
    metadata = pq.read_metadata(partial)
    if metadata.num_rows != len(frame):
        partial.unlink()
        raise RuntimeError(f"Parquet row-count verification failed for {path.name}")
    partial.replace(path)


def _categorize_repeated_text(frame: pd.DataFrame) -> None:
    for column in (
        "source_archive",
        "source_member",
        "product_type",
        "station",
        "source_column",
        "sensor_id",
        "measurement_role",
        "installation_segment_id",
        "documented_event_flags",
    ):
        frame[column] = frame[column].astype("category")


def _write_summaries(fifteen: pd.DataFrame, daily: pd.DataFrame) -> None:
    _write_csv(
        pd.concat([coverage_summary(fifteen), coverage_summary(daily)], ignore_index=True),
        "data/provenance/cleveland_corral_qc_summary.csv",
    )
    _write_csv(
        pd.concat(
            [compatibility_summary(fifteen), compatibility_summary(daily)], ignore_index=True
        ),
        "data/provenance/cleveland_corral_actual_compatibility.csv",
    )
    _write_csv(
        daily_relationship_summary(fifteen, daily),
        "data/provenance/cleveland_corral_product_semantics.csv",
    )


def main() -> None:
    """Reproduce Phase 2 outputs directly from preserved raw archives."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summaries-only",
        action="store_true",
        help="reuse verified local Parquet files instead of reparsing raw archives",
    )
    parser.add_argument(
        "--product-semantics-only",
        action="store_true",
        help="refresh only the daily-versus-15-minute aggregate comparison",
    )
    args = parser.parse_args()

    raw_directory = RAW_DATA_DIR / "cleveland_corral"
    interim_directory = INTERIM_DATA_DIR / "cleveland_corral"
    interim_directory.mkdir(parents=True, exist_ok=True)
    fifteen_path = interim_directory / "selected_15_minute_quality_flagged.parquet"
    daily_path = interim_directory / "selected_daily_quality_flagged.parquet"
    if args.summaries_only or args.product_semantics_only:
        fifteen = pd.read_parquet(fifteen_path)
        daily = pd.read_parquet(daily_path)
    else:
        fifteen = read_monitoring_archive(
            raw_directory / "Cleveland_Corral_15_Minute_Data.zip"
        )
        daily = read_monitoring_archive(raw_directory / "Cleveland_Corral_Daily_Data.zip")
        _categorize_repeated_text(fifteen)
        _categorize_repeated_text(daily)
        _write_parquet_atomic(fifteen, fifteen_path)
        _write_parquet_atomic(daily, daily_path)
        print(f"Wrote {len(fifteen)} local rows: {fifteen_path.relative_to(PROJECT_ROOT)}")
        print(f"Wrote {len(daily)} local rows: {daily_path.relative_to(PROJECT_ROOT)}")
    if args.product_semantics_only:
        _write_csv(
            daily_relationship_summary(fifteen, daily),
            "data/provenance/cleveland_corral_product_semantics.csv",
        )
    else:
        _write_summaries(fifteen, daily)


if __name__ == "__main__":
    main()
