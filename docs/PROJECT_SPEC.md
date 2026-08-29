# California Landslide Monitoring Time-Series Analysis — Project Specification

## Purpose

Build a reproducible, educational time-series analysis of landslide monitoring data
that connects statistical methods to a real geotechnical engineering question. The
project should be understandable to a civil/geotechnical audience and auditable by a
technical reader.

## Completion status

All six planned phases are complete. The canonical portfolio deliverable is the
[final engineering report](../reports/CLEVELAND_CORRAL_FINAL_REPORT.md), supported by a
validator-backed [claim-and-evidence matrix](../reports/tables/phase5/claim_evidence_matrix.csv),
executed instructional notebooks, inspected figures, and one top-level reproduction
route. Completion does not expand the scope: causal identification, operational
warning, threshold selection, and engineering design remain out of scope.

## Cleveland Corral context

The intended primary data source is the official USGS Cleveland Corral landslide
monitoring record near U.S. Highway 50 in El Dorado County, California. The site and
individual sensor records must be audited in Phase 1 before any series is selected for
analysis. This specification does not assume that every desired variable has compatible
coverage, sampling, units, or quality.

## Engineering questions

1. How do precipitation, rainfall, snowmelt, and antecedent wetness relate in time to
   soil-moisture and pore-water-pressure responses?
2. Do those hydrologic responses precede observed landslide displacement, and are the
   lags stable across events or seasons?
3. How much predictive value comes from a response series' own history versus external
   hydrologic drivers?
4. Which monitoring limitations, sensor changes, or missing intervals constrain the
   interpretation?

## Physical hypothesis

The motivating sequence is:

> precipitation or snowmelt → infiltration and soil-moisture response →
> pore-water-pressure response → possible slope-displacement response

This is a hypothesis to investigate. Temporal ordering, correlation, or forecast skill
may be consistent with the hypothesis but cannot by itself establish a causal mechanism.

## Variables of interest

- Precipitation, rainfall, snowmelt indicators, and defensible antecedent-wetness
  summaries
- Volumetric soil moisture or the site-specific moisture measurements actually provided
- Pore-water pressure, groundwater level, and piezometer measurements
- Observed landslide displacement or movement measurements
- Sensor metadata needed to interpret units, datum, location, sampling, maintenance, and
  instrument changes

The Phase 1 audit will determine which variables are truly available and mutually
comparable; unavailable values must never be invented or inferred without support.

## Statistical learning goals

- Understand time indexing, irregular sampling, gaps, trend, seasonality, stationarity,
  autocorrelation, and partial autocorrelation in environmental sensor records.
- Evaluate lagged relationships without confusing shared autocorrelation with physical
  response.
- Build transparent forecast baselines and, if justified, ARIMA/ARIMAX candidates.
- Use expanding- or sliding-window chronological validation with no future-data leakage.
- Diagnose residuals, uncertainty, stability, and possible regime changes.
- Use frequency-domain or spectral methods only if the data and engineering question
  justify them.

## Intended deliverables

1. A source and sensor inventory with provenance, units, datums, time zones, sampling,
   coverage, maintenance notes, and checksums.
2. Reproducible ingestion and sensor-aware quality-control code that preserves raw data.
3. Instructional notebooks for the methods actually used.
4. Tested reusable functions in `src/geotech_ts/`.
5. Chronologically validated model comparisons with diagnostics and uncertainty.
6. A concise technical report separating results, inference, engineering meaning, and
   limitations.
7. A public, documented repository that can reproduce the analysis from public sources.

## Scope and non-goals

In scope are official Cleveland Corral monitoring records, transparent sensor-aware
quality control, exploratory time-series methods, justified dependence and forecasting
methods, chronological validation, and engineering communication.

Out of scope are real-time operational warning, design recommendations, safety-critical
decision support, confidential data, unsupported interpolation, fabricated results, and
causal claims based only on observational association. A dashboard or website is not a
project requirement. Spectral analysis is optional, not a mandatory deliverable.

## Reproducibility standards

- Define dependencies in `pyproject.toml` and keep project packages in `.venv`.
- Preserve downloaded raw files unchanged and exclude datasets from Git.
- Version source URLs, provenance metadata, checksums, code, tests, and documentation.
- Implement every correction and transformation in code with explicit quality flags.
- Use deterministic settings where applicable and record analysis-relevant parameters.
- Test reusable code, run the repository checks, and inspect generated outputs.
- Use chronological train/validation/test logic; fit preprocessing only on information
  available at each forecast origin.

## Limits on causal interpretation

The monitoring data are observational and may contain common drivers, seasonality,
autocorrelation, missingness, measurement error, and instrument changes. Cross-
correlation, temporal precedence, regression coefficients, and predictive improvement
support statements about association or prediction only. Engineering interpretation
must identify alternative explanations and label any causal language as a hypothesis
unless a defensible identification strategy and supporting evidence exist.
