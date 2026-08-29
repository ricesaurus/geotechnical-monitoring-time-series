# Learning map: time-series methods to engineering evidence

This map connects the UCLA Statistics 170-style time-series curriculum to the
Cleveland Corral implementation. The notebooks explain the methods; reusable code and
validators make the evidence auditable; the final report states what the results do
and do not support.

| Learning topic | Project artifact | Engineering relevance |
|---|---|---|
| Time index, cadence, and time zones | [Phase 2 ingestion/QC report](data/CLEVELAND_CORRAL_PHASE2_INGESTION_QC.md) | Fixed PST, source cadence, gaps, and logger phase must be explicit before sensors can be aligned. |
| Missingness and sensor-aware quality control | [Phase 2 provenance tables](../data/provenance/) | Flags preserve observations while separating gaps, resets, installation changes, and metadata concerns from verified errors. |
| Trend, seasonality, and decomposition | [Phase 3 notebook](../notebooks/02_phase3_exploratory_dynamics.ipynb) | Robust STL describes long exact-contiguous runs without filling gaps or assigning a physical cause. |
| Stationarity and transformations | [Phase 3 exploratory report](CLEVELAND_CORRAL_PHASE3_EXPLORATORY_DYNAMICS.md) | Levels, valid changes, and cumulative rain answer different questions; transformations cannot cross known boundaries. |
| ACF, PACF, and linear processes | [ACF/PACF diagnostics](../reports/tables/phase3/acf_pacf_diagnostics.csv) | Persistence explains why naive correlations and sophisticated forecasts can look attractive without adding useful skill. |
| Lagged cross-correlation and prewhitening | [Lag summary](../reports/tables/phase3/daily_lag_summary.csv) | A declared predictor-leads convention and dependence adjustment distinguish temporal association from a causal response time. |
| Event alignment under irregular timing | [Event sensitivity table](../reports/tables/phase3/event_alignment_sensitivity.csv) | No-reuse matching and tolerance sensitivity expose how logger phase and event selection affect apparent lag. |
| Forecast baselines and ARIMA/ARIMAX | [Phase 4 notebook](../notebooks/03_phase4_forecasting_validation.ipynb) | Dynamic models must improve on defensible simple forecasts at the same origins; external features must be available at forecast time. |
| Chronological validation and leakage prevention | [Frozen forecasting contract](phase4/FORECASTING_CONTRACT.md) | Earlier selection and untouched later evaluation prevent future regimes from influencing model choice. |
| Forecast uncertainty and residual diagnostics | [Phase 4 forecast report](CLEVELAND_CORRAL_PHASE4_FORECASTING_VALIDATION.md) | Paired error intervals, calibration, width, heavy tails, and failure counts qualify every skill statement. |
| Changepoints and sensitivity | [Changepoint candidates](../reports/tables/phase4/changepoint_candidates.csv) | Algorithmic boundaries depend on method and tuning; event alignment supplies context, not a cause. |
| Engineering synthesis and evidence boundaries | [Final report](../reports/CLEVELAND_CORRAL_FINAL_REPORT.md) and [claim matrix](../reports/tables/phase5/claim_evidence_matrix.csv) | Observed data, statistical inference, engineering interpretation, and speculation remain visibly separate. |

Frequency-domain analysis remains intentionally optional. It was not added because the
final engineering questions were addressed by the justified time-domain analyses, and
Phase 5 was limited to synthesis rather than new scientific work.
