# Notebooks

Number notebooks in the order a reader should follow them:

```text
00_environment_and_data_inventory.ipynb
01_quality_control.ipynb
02_exploratory_analysis.ipynb
03_decomposition_stationarity.ipynb
04_acf_pacf_linear_processes.ipynb
05_spectral_analysis.ipynb  # optional; create only if justified
06_lagged_cross_correlation.ipynb
07_arima_arimax.ipynb
08_changepoints.ipynb
09_rolling_validation.ipynb
10_engineering_synthesis.ipynb
```

Notebooks should explain decisions and show results. Reusable ingestion, quality-control,
modeling, and validation logic belongs in `src/geotech_ts/`, where it can be tested.
The sequence is a long-term outline, not a signal to create notebooks before their
assigned phase.
