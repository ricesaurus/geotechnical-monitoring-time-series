"""Validation for the final report, evidence matrix, links, and notebooks."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from geotech_ts.phase5_synthesis import (
    build_claim_evidence_matrix,
    build_key_forecast_results,
)

WINDOWS_ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
MARKDOWN_LINK = re.compile(r"!?(?:\[[^\]]*\])\(([^)]+)\)")
REQUIRED_REPORT_HEADINGS = tuple(
    f"## {number}. {title}"
    for number, title in enumerate(
        (
            "Executive summary",
            "Site and monitoring context",
            "Data sources and sensor selection",
            "Reproducible ingestion and quality control",
            "Exploratory structure, seasonality, and dependence",
            "Lagged relationships",
            "Forecasting and chronological validation",
            "Prediction intervals and residual behavior",
            "Changepoint sensitivity",
            "Answers to the engineering questions",
            "Engineering interpretation",
            "Limitations and threats to validity",
            "Conclusions",
            "Reproduction instructions",
            "References and data attribution",
        ),
        start=1,
    )
)
FORBIDDEN_OBSERVATION_COLUMNS = {
    "timestamp_original",
    "timestamp_pst_fixed",
    "timestamp_utc",
    "local_date",
    "origin_date",
    "target_date",
    "target_value",
    "prediction",
    "error",
    "parameter_value",
}


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _validate_notebook(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing instructional notebook: {path}"]
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid notebook {path}: {error}"]
    code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
    if not code_cells:
        return [f"{path}: expected instructional code cells"]
    for number, cell in enumerate(code_cells, start=1):
        if cell.get("execution_count") is None:
            errors.append(f"{path}: code cell {number} was not executed")
        if any(output.get("output_type") == "error" for output in cell.get("outputs", [])):
            errors.append(f"{path}: code cell {number} contains an error output")
    return errors


def validate_internal_links(project_root: Path, paths: tuple[Path, ...]) -> list[str]:
    """Check repository-relative Markdown links without requesting the network."""

    errors: list[str] = []
    resolved_root = project_root.resolve()
    for path in paths:
        if not path.is_file():
            errors.append(f"missing Markdown file for link validation: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().strip("<>").split("#", maxsplit=1)[0]
            if not target or target.startswith(("https://", "http://", "mailto:")):
                continue
            candidate = (path.parent / target).resolve()
            if candidate != resolved_root and resolved_root not in candidate.parents:
                errors.append(f"{path}: link escapes project root: {raw_target}")
            elif not candidate.exists():
                errors.append(f"{path}: missing linked path: {raw_target}")
    return errors


def _compare_generated_csv(
    project_root: Path,
    relative_path: str,
    expected: pd.DataFrame,
) -> list[str]:
    path = project_root / relative_path
    if not path.is_file():
        return [f"missing Phase 5 aggregate table: {path}"]
    observed = pd.read_csv(path)
    try:
        pd.testing.assert_frame_equal(
            observed,
            expected,
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
    except AssertionError as error:
        return [f"{path}: does not agree with Phase 1–4 source artifacts: {error}"]
    return []


def validate_phase5_outputs(
    project_root: Path,
    *,
    require_executed_notebooks: bool = True,
) -> list[str]:
    """Return errors for missing, inconsistent, unsafe, or unexecuted final outputs."""

    errors: list[str] = []
    report = project_root / "reports/CLEVELAND_CORRAL_FINAL_REPORT.md"
    claim_path = project_root / "reports/tables/phase5/claim_evidence_matrix.csv"
    forecast_path = project_root / "reports/tables/phase5/key_forecast_results.csv"
    software_path = project_root / "reports/tables/phase5/software_versions.csv"
    receipt_path = project_root / "reports/tables/phase5/full_reproduction_receipt.csv"

    expected_claims = build_claim_evidence_matrix(project_root)
    expected_forecasts = build_key_forecast_results(project_root)
    errors.extend(
        _compare_generated_csv(
            project_root,
            "reports/tables/phase5/claim_evidence_matrix.csv",
            expected_claims,
        )
    )
    errors.extend(
        _compare_generated_csv(
            project_root,
            "reports/tables/phase5/key_forecast_results.csv",
            expected_forecasts,
        )
    )

    for path, required in (
        (software_path, {"component", "version"}),
        (
            receipt_path,
            {"phase", "measure", "count", "source_layer", "verification_status"},
        ),
    ):
        if not path.is_file():
            errors.append(f"missing Phase 5 aggregate table: {path}")
            continue
        frame = pd.read_csv(path)
        missing = sorted(required - set(frame.columns))
        if missing:
            errors.append(f"{path}: missing columns: {', '.join(missing)}")
        if frame.empty:
            errors.append(f"{path}: expected at least one row")

    for path in (claim_path, forecast_path, software_path, receipt_path):
        if not path.is_file():
            continue
        frame = pd.read_csv(path)
        forbidden = sorted(FORBIDDEN_OBSERVATION_COLUMNS & set(frame.columns))
        if forbidden:
            errors.append(f"{path}: observation columns are forbidden: {', '.join(forbidden)}")
        if WINDOWS_ABSOLUTE_PATH.search(path.read_text(encoding="utf-8")):
            errors.append(f"{path}: machine-specific absolute path")

    if not report.is_file():
        errors.append(f"missing canonical final report: {report}")
    else:
        report_text = report.read_text(encoding="utf-8")
        normalized_report = _normalize(report_text)
        for heading in REQUIRED_REPORT_HEADINGS:
            if heading not in report_text:
                errors.append(f"{report}: missing required heading {heading!r}")
        for claim in expected_claims["claim"]:
            if _normalize(str(claim)) not in normalized_report:
                errors.append(f"{report}: missing validator-backed claim: {claim}")
        for row in expected_forecasts.itertuples():
            values = (
                f"{row.selection_mae_cm_per_day:.3f}",
                f"{row.later_frozen_mae_cm_per_day:.3f}",
                f"{row.later_zero_mae_cm_per_day:.3f}",
            )
            if not all(value in report_text for value in values):
                errors.append(
                    f"{report}: missing rounded forecast values for "
                    f"{row.sensor_id} horizon {row.horizon_days}"
                )
        if WINDOWS_ABSOLUTE_PATH.search(report_text):
            errors.append(f"{report}: machine-specific absolute path")
        figure_targets = [
            target
            for target in MARKDOWN_LINK.findall(report_text)
            if target.casefold().endswith(".png")
        ]
        if len(figure_targets) != 7:
            errors.append(f"{report}: expected exactly seven curated figure references")
        for category in (
            "Observed data",
            "Statistical inference",
            "Engineering interpretation",
            "Speculation and unresolved questions",
        ):
            if category not in report_text:
                errors.append(f"{report}: missing evidence category {category!r}")

    errors.extend(
        validate_internal_links(
            project_root,
            (
                project_root / "README.md",
                report,
                project_root / "notebooks/README.md",
                project_root / "data/README.md",
                project_root / "docs/LEARNING_MAP.md",
            ),
        )
    )
    if require_executed_notebooks:
        for filename in (
            "02_phase3_exploratory_dynamics.ipynb",
            "03_phase4_forecasting_validation.ipynb",
        ):
            errors.extend(_validate_notebook(project_root / "notebooks" / filename))
    return errors
