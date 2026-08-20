# California Landslide Monitoring Time-Series Analysis

An end-to-end portfolio project for analyzing official U.S. Geological Survey (USGS)
monitoring records from the Cleveland Corral landslide near U.S. Highway 50 in El
Dorado County, California. The intended records include precipitation and snowmelt,
soil moisture, pore-water pressure or piezometer measurements, and landslide
displacement.

The project has two goals:

1. Develop a reproducible geotechnical monitoring workflow.
2. Learn the core ideas of an undergraduate time-series course through a real civil
   engineering application.

## Planned analysis

- Data ingestion, provenance, and sensor-aware quality control
- Exploratory time-series analysis and decomposition
- Stationarity, autocorrelation (ACF), and partial autocorrelation (PACF)
- Optional frequency-domain and spectral analysis, only if justified by the data and
  engineering question
- Lagged cross-correlation between rainfall, pore pressure, soil moisture, and movement
- ARIMA and ARIMAX models with residual diagnostics
- Changepoint detection
- Rolling-origin out-of-sample validation and benchmark comparison
- Engineering interpretation, limitations, and a reproducible final report

The motivating physical hypothesis is that precipitation or snowmelt may lead to
infiltration and soil-moisture response, followed by pore-water-pressure response and
possibly slope-displacement response. The project will test temporal association and
predictive value; it will not treat correlation, lag structure, or forecast skill as
proof of causation.

## Current status

**Phase 0 — environment and repository setup.** The project foundation is being
validated and published. No monitoring data have been downloaded. See the
[active execution plan](docs/exec-plans/active/PROJECT_EXECUTION_PLAN.md) for current
state; Phase 1 is the site and data-source audit.

## Quick start on Windows

From PowerShell in the project folder:

```powershell
./scripts/setup.ps1
./scripts/check.ps1
```

Activate the environment for an interactive session:

```powershell
./.venv/Scripts/Activate.ps1
```

Then open the folder in VS Code if desired:

```powershell
code .
```

VS Code is optional. The code and environment live in this folder; GitHub stores a
versioned copy of committed files.

## Repository layout

```text
data/                  Local data layers and provenance notes
docs/                  Specification, active plan, and learning records
notebooks/             Numbered exploratory and instructional notebooks
reports/figures/       Curated figures suitable for the final report
scripts/               Repeatable setup and quality-check commands
src/geotech_ts/        Reusable analysis code
tests/                  Automated tests
```

Raw and derived datasets are intentionally excluded from Git. Download scripts,
source URLs, metadata, and small documentation files will be versioned so that the
analysis remains reproducible without committing bulky or mutable data.

## Reproducibility rule

Every result in the final report should be regenerable from a documented public data
source by running code in this repository. Manual spreadsheet edits are not part of
the analysis pipeline. Raw data remain immutable, time-series validation remains
chronological, and future observations must never leak into training or preprocessing.

## License

Code in this repository is released under the [MIT License](LICENSE). USGS data retain
their original terms and attribution.
