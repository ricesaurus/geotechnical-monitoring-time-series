"""Verify Phase 5 report, evidence, links, and instructional notebooks."""

from geotech_ts.paths import PROJECT_ROOT
from geotech_ts.phase5_validation import validate_phase5_outputs


def main() -> None:
    """Fail if any final deliverable is missing, inconsistent, or unsafe."""

    errors = validate_phase5_outputs(PROJECT_ROOT)
    if errors:
        raise SystemExit("\n".join(errors))
    print("Phase 5 report, evidence matrix, links, and notebooks verified.")


if __name__ == "__main__":
    main()
