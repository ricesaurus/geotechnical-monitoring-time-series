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

**Phase 3 — exploratory structure and dynamics complete.** Reusable, tested code now
builds explicit analysis masks, two defensible precipitation transformations,
segment-aware coverage/distribution/decomposition/stationarity/ACF/PACF diagnostics,
exact-date daily lag sensitivity, and rain-selected 15-minute event alignment. Twelve
aggregate tables, nine inspected figures, and a restart-and-run notebook reproduce the
findings without committing observation rows. No interpolation, successor splicing,
forecasting, ARIMA/ARIMAX fitting, changepoint detection, or causal claim has begun.
See the
[Phase 3 exploratory-dynamics report](docs/CLEVELAND_CORRAL_PHASE3_EXPLORATORY_DYNAMICS.md)
and the [active execution plan](docs/exec-plans/active/PROJECT_EXECUTION_PLAN.md).

## Quick start on Windows

From PowerShell in the project folder:

```powershell
./scripts/setup.ps1
./scripts/check.ps1
```

After setup, reproduce the local Phase 2 data layers from the official release:

```powershell
./.venv/Scripts/python.exe ./scripts/acquire_cleveland_corral.py
./.venv/Scripts/python.exe ./scripts/inspect_cleveland_corral_archives.py
./.venv/Scripts/python.exe ./scripts/build_phase2_interim.py
./.venv/Scripts/python.exe ./scripts/verify_phase2_data.py
```

Then reproduce and verify Phase 3:

```powershell
./.venv/Scripts/python.exe ./scripts/build_phase3_analysis.py
./.venv/Scripts/python.exe ./scripts/verify_phase3_outputs.py
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
data/                  Local data layers and version-controlled provenance metadata
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
