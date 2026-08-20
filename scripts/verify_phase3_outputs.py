"""Verify Phase 3 aggregate, visual, and ignored processed deliverables."""

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase3_validation import validate_phase3_outputs


def main() -> None:
    """Fail when a required Phase 3 output is missing or unsafe."""

    errors = validate_phase3_outputs(PROJECT_ROOT, require_local_processed=True)
    if errors:
        raise SystemExit("\n".join(errors))
    print("Phase 3 aggregate tables, figures, and ignored processed outputs verified.")


if __name__ == "__main__":
    main()
