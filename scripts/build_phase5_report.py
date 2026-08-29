"""Build Phase 5 aggregate synthesis artifacts from verified Phase 1–4 evidence."""

from __future__ import annotations

import argparse

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase5_synthesis import (
    build_claim_evidence_matrix,
    build_key_forecast_results,
    local_reproduction_receipt,
    software_versions,
)

OUTPUT_DIRECTORY = PROJECT_ROOT / "reports/tables/phase5"


def _write(frame, filename: str) -> None:
    path = OUTPUT_DIRECTORY / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, lineterminator="\n")
    print(f"Wrote {len(frame)} aggregate rows: {path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    """Build the claim matrix, forecast summary, environment, and optional local receipt."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--record-full-reproduction",
        action="store_true",
        help="require all ignored local products and record their aggregate row counts",
    )
    args = parser.parse_args()
    _write(build_claim_evidence_matrix(), "claim_evidence_matrix.csv")
    _write(build_key_forecast_results(), "key_forecast_results.csv")
    _write(software_versions(), "software_versions.csv")
    if args.record_full_reproduction:
        _write(local_reproduction_receipt(), "full_reproduction_receipt.csv")


if __name__ == "__main__":
    main()
