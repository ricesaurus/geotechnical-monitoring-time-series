# Time-series learning roadmap

This roadmap turns the project into a compact, applied course. Each module should end
with three outputs: a concept note, an implemented method, and a geotechnical
interpretation.

## Module 1 — Time-series foundations

Learn the time index, sampling frequency, lag operators, weak stationarity, means,
variances, autocovariance, and autocorrelation. Connect each idea to real sensor
behavior and monitoring intervals.

**Checkpoint:** explain why irregular sampling and long gaps change what an ACF means.

## Module 2 — Quality control and exploratory structure

Learn missing-data mechanisms, robust summaries, transformations, resampling, trend,
seasonality, and classical/STL decomposition.

**Checkpoint:** produce a quality-control report that preserves raw values and assigns
defensible flags.

## Module 3 — ACF, PACF, and linear processes

Learn white noise, random walks, AR, MA, and ARMA processes; derive their qualitative
ACF/PACF signatures; use simulation before fitting field data.

**Checkpoint:** simulate known AR and MA processes and correctly diagnose them without
looking at the generating parameters.

## Optional module 4 — Frequency-domain thinking

Learn periodic components, the periodogram, spectral density, aliasing, leakage, and
how sampling interval limits detectable cycles. Use this module only if the available
Cleveland Corral records and engineering question justify frequency-domain analysis.

**Checkpoint:** distinguish a real periodic component from trend leakage or an artifact
of the monitoring schedule.

## Module 5 — Coupled environmental series

Learn cross-covariance, lagged cross-correlation, spurious correlation from shared
autocorrelation, prewhitening, distributed lags, and antecedent rainfall indices.

**Checkpoint:** state exactly what a rainfall-to-pore-pressure lag peak does and does
not establish.

## Module 6 — ARIMA and ARIMAX

Learn differencing, model identification, estimation, information criteria, residual
diagnostics, exogenous predictors, forecasts, and prediction intervals.

**Checkpoint:** beat a persistence baseline on unseen rolling windows and explain why.

## Module 7 — Changepoints and nonstationarity

Learn abrupt versus gradual change, penalties, multiple testing, variance changes, and
the distinction between physical regime shifts and instrument artifacts.

**Checkpoint:** triangulate every candidate changepoint with metadata or an independent
series.

## Module 8 — Honest time-series validation

Learn forecast origins, expanding/sliding windows, horizon-specific error, leakage,
hyperparameter selection, interval calibration, and forecast comparison.

**Checkpoint:** produce one table that compares all candidates under identical rolling
origins and horizons.

## Module 9 — Engineering communication

Translate statistical results into monitoring implications while communicating data
limitations, uncertainty, and the boundary between prediction and mechanism.

**Checkpoint:** write an executive summary that a civil engineer can understand without
removing the statistical caveats.

## Supporting probability and statistics review

Review these topics as they become necessary rather than as a separate prerequisite:

- Conditional expectation and variance
- Linear regression and least squares
- Likelihood, confidence intervals, and hypothesis testing
- Matrix notation for regression
- Multiple comparisons and model-selection bias
- Basic numerical optimization
