"""Verify Phase 2 aggregate artifacts and preserved local raw resources."""

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase2_validation import validate_phase2_tables, verify_download_manifest


def main() -> None:
    """Fail if tracked aggregate tables or local raw checksums are invalid."""

    errors = validate_phase2_tables(PROJECT_ROOT)
    errors.extend(verify_download_manifest(PROJECT_ROOT))
    if errors:
        raise SystemExit("\n".join(errors))
    print("Phase 2 aggregate tables and local raw-file checksums verified.")


if __name__ == "__main__":
    main()
