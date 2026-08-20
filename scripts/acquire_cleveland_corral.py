"""Download and verify the required Cleveland Corral monitoring archives."""

from geotech_ts.acquisition import acquire_required_resources, write_local_receipt
from geotech_ts.paths import RAW_DATA_DIR


def main() -> None:
    """Acquire only the official primary data archives and sensor metadata."""

    raw_directory = RAW_DATA_DIR / "cleveland_corral"
    records = acquire_required_resources(raw_directory)
    receipt = raw_directory / "acquisition_receipt.json"
    write_local_receipt(records, receipt)
    for record in records:
        print(f"{record.filename}: {record.byte_size} bytes sha256={record.sha256}")
    print(f"Local receipt: {receipt.relative_to(RAW_DATA_DIR.parent.parent)}")


if __name__ == "__main__":
    main()
