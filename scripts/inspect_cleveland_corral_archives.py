"""Write the metadata-only archive-member inventory."""

from __future__ import annotations

import csv
from dataclasses import asdict

from geotech_ts.archives import inspect_archives
from geotech_ts.paths import PROJECT_ROOT, RAW_DATA_DIR


def main() -> None:
    """Inspect the raw ZIPs and write no measurement observations."""

    raw_directory = RAW_DATA_DIR / "cleveland_corral"
    paths = [
        raw_directory / "Cleveland_Corral_15_Minute_Data.zip",
        raw_directory / "Cleveland_Corral_Daily_Data.zip",
    ]
    records = inspect_archives(paths)
    output = PROJECT_ROOT / "data/provenance/cleveland_corral_archive_inventory.csv"
    fieldnames = list(asdict(records[0]))
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["columns"] = "; ".join(record.columns)
            writer.writerow(row)
    print(f"Inspected {len(records)} CSV members; wrote {output.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
