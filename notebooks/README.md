# Instructional notebooks

The repository contains two executed, restart-and-run notebooks. Their numbers follow
the project phases rather than a one-notebook-per-topic syllabus:

1. [`02_phase3_exploratory_dynamics.ipynb`](02_phase3_exploratory_dynamics.ipynb)
   covers coverage and missingness, transformations, robust decomposition,
   stationarity, ACF/PACF, synthetic linear-process examples, daily lag analysis, and
   event-alignment sensitivity.
2. [`03_phase4_forecasting_validation.ipynb`](03_phase4_forecasting_validation.ipynb)
   covers the frozen forecasting design, baselines, ARIMA/ARIMAX comparisons,
   forecast-time feature availability, rolling-origin uncertainty, intervals,
   residuals, coefficient paths, changepoints, and a synthetic leakage demonstration.

Both notebooks display aggregate evidence and call reusable logic in `src/geotech_ts/`.
Observation-bearing rolling forecasts and event matches remain in Git-ignored local
data layers. Phase 5 adds no new analysis notebook: the
[final engineering report](../reports/CLEVELAND_CORRAL_FINAL_REPORT.md) is the canonical
synthesis, and the [learning map](../docs/LEARNING_MAP.md) connects its evidence to the
curriculum.

Execute clean verification copies with:

```powershell
./.venv/Scripts/python.exe ./scripts/execute_notebooks.py
```

The copies are written under the ignored `data/processed/` layer. Maintainers can use
`--in-place` when deliberately refreshing the committed executed notebooks. Notebook
execution fails on any cell error; analysis logic, validation, and tests remain outside
the notebooks so they are independently auditable.
