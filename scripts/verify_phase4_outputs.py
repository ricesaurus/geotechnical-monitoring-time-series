"""Verify Phase 4 aggregate, visual, notebook, and ignored processed deliverables."""

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase4_validation import validate_phase4_outputs


def main() -> None:
    """Fail when a required Phase 4 output is missing or unsafe."""

    errors = validate_phase4_outputs(PROJECT_ROOT, require_local_processed=True)
    if errors:
        raise SystemExit("\n".join(errors))
    print("Phase 4 tables, figures, notebook, and ignored processed outputs verified.")


if __name__ == "__main__":
    main()
