"""Execute the two instructional notebooks from clean kernels."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import nbformat
from nbclient import NotebookClient

from geotech_ts.paths import PROJECT_ROOT

NOTEBOOKS = (
    "02_phase3_exploratory_dynamics.ipynb",
    "03_phase4_forecasting_validation.ipynb",
)


def execute_notebook(source: Path, target: Path) -> None:
    """Clear, execute, and write one notebook without allowing cell errors."""

    notebook = nbformat.read(source, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.execution_count = None
            cell.outputs = []
    client = NotebookClient(
        notebook,
        timeout=900,
        kernel_name="python3",
        resources={"metadata": {"path": str(PROJECT_ROOT)}},
    )
    client.execute()
    target.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, target)


def main() -> None:
    """Execute in place or write ignored verification copies."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="replace the committed notebooks with freshly executed copies",
    )
    args = parser.parse_args()
    source_directory = PROJECT_ROOT / "notebooks"
    output_directory = (
        source_directory
        if args.in_place
        else PROJECT_ROOT / "data/processed/cleveland_corral/executed_notebooks"
    )
    if not args.in_place and output_directory.exists():
        shutil.rmtree(output_directory)
    for filename in NOTEBOOKS:
        source = source_directory / filename
        target = output_directory / filename
        execute_notebook(source, target)
        location = target.relative_to(PROJECT_ROOT)
        print(f"Executed without cell errors: {location}")


if __name__ == "__main__":
    main()
