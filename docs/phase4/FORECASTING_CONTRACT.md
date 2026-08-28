# Phase 4 forecasting and changepoint contract

**Frozen:** 2026-08-27, before any Phase 4 model comparison

**Time basis:** fixed PST (UTC−08:00) local calendar dates

**Primary metric:** mean absolute error (MAE)

This document fixes the Phase 4 analysis choices before forecasts are evaluated. Phase
3 examined the complete record, including the periods used below. The later evaluation
period is therefore not a strictly unseen confirmatory dataset. Phase 4 nevertheless
prevents computational leakage at every forecast origin and does not revise this
candidate set after seeing Phase 4 results.

## Targets and windows

The target is the Phase 3 `daily_first_difference` value and eligibility mask. No value
is recalculated, interpolated, clipped, spliced, or differenced again.

| Window | Target | Role | Half-open fixed-PST dates | Declared use |
| --- | --- | --- | --- | --- |
| `middle_stable_2009_2016` | `mid_E2_B` | primary | 2009-02-12 to 2016-01-22 | model selection and later evaluation inside E2 segment 6 |
| `toe_pre_topple_long` | `toe_E5_C` | secondary primary-window analysis | 2006-11-30 to 2016-01-22 | model selection and later evaluation before the rain-gauge interruption |
| `toe_pre_topple_post_rain_resume` | `toe_E5_C` | external-time stability check | 2016-01-28 to 2017-03-16 | unchanged specifications only; never used to revise candidates or selection |

The middle window contains 2,389 eligible changes over 2,535 calendar days. The long
toe window contains 3,211 eligible changes over 3,340 days. The post-resume toe check
contains 367 eligible changes over 413 days. These are mask/coverage facts, not model
results.

## Forecast origins, training, and horizons

- Horizons are 1, 2, and 7 calendar days. No horizon is removed for the univariate
  baselines or ARIMA candidates.
- Primary validation uses an expanding calendar-day window. The daily index retains
  every calendar date; missing or ineligible targets remain missing and are never
  converted to zero or removed to compress time.
- Minimum training is 365 calendar days and 300 eligible target observations.
- Origins occur every 14 calendar days, anchored at 2010-02-12 for the middle window,
  2007-11-30 for the long toe window, and 2016-01-28 for the post-resume toe check.
  An anchor date that fails eligibility is recorded as skipped rather than moved to a
  convenient nearby date.
- A core origin/horizon is evaluable only when the target at the origin and every target
  change on the path through `origin + horizon` are eligible, remain in the same target
  installation segment and water year, and lie inside the declared window. This rule
  prevents forecasts from crossing gaps, resets, or target-regime boundaries.
- The middle selection stage ends 2013-08-31; its later evaluation begins 2013-09-01.
  The long-toe selection stage ends 2012-12-31; its later evaluation begins 2013-01-01.
  The post-resume window is labeled `external_time_check` throughout.
- The post-resume check begins with the long-toe history, appends post-resume target
  observations only after they become available, and keeps model specifications and
  retained decisions frozen. Its metrics are never pooled with the long-window metrics.
- No sliding-window analysis is included. Early/late evaluation halves and the separate
  post-resume toe check are the predeclared stability analyses.

## Baselines

All baselines operate directly on displacement change and receive the same core
origin/horizon masks.

1. `zero_change`: predict 0 cm/day.
2. `persistence`: repeat the eligible displacement change at the origin.
3. `expanding_median`: use the median of eligible training targets through the origin.
4. `prior_year_same_date`: use the eligible target on the same month and day one
   calendar year before the forecast target. February 29 or a missing/ineligible prior
   value is a recorded model-specific skip.

Baseline 80% and 95% intervals use empirical quantiles of that baseline's earlier
out-of-sample residuals for the same target/window/horizon. At a new origin, only
residuals whose outcomes were observable by that origin (`prior target date <= current
origin`) may calibrate the interval. At least 30 past residuals are required; otherwise
the point forecast remains but interval status is `insufficient_past_calibration`.

## ARIMA candidates

The eligible displacement-change target is not differenced again: every candidate has
`d=0`. The set is deliberately small and reflects Phase 3 stationarity and ACF/PACF
evidence.

| Model ID | Nonseasonal order | Seasonal order | Targets | Rationale |
| --- | --- | --- | --- | --- |
| `arima_mean` | (0,0,0) with constant | none | middle, toe | white-noise/mean reference |
| `arima_ar1` | (1,0,0) with constant | none | middle, toe | parsimonious short memory |
| `arima_ar2` | (2,0,0) with constant | none | middle, toe | limited second-lag structure, especially toe |
| `arima_arma11` | (1,0,1) with constant | none | middle, toe | one limited ARMA alternative |
| `arima_ar1_weekly` | (1,0,0) with constant | (1,0,0,7) | middle only | predeclared weekly-memory sensitivity supported by the middle ACF |

Models are fit with statsmodels state-space likelihood on the complete daily calendar,
with missing targets retained as missing states. Stationarity and invertibility are
enforced. Each origin records convergence, warnings, parameter estimates, stationarity
or invertibility failures, and forecast failures. A failed specification is never
silently replaced.

## ARIMAX candidate and feature availability

Only the long and post-resume toe targets admit an exogenous candidate:
`arimax_ar1_rain_lag2`. It is the conditional ARIMAX/ARX equation

`toe change[t] = constant + phi * toe change[t-1] + beta * rain[t-2] + error[t]`.

Rain is Phase 3's eligible `daily_interval_sum` from the 15-minute interval-rain field.
Every fitted equation requires exact calendar dates, an eligible current and lag-1 toe
change, and eligible lag-2 rain; incomplete equations are absent rather than compressed
or filled. At least 240 exact training equations are required. No scaling is applied.

At origin `t`, the one-day forecast uses rain at `t-1`; the two-day recursive forecast
uses rain at `t`. Both are observed by the origin. A 7-day forecast would require rain
after `t`, so this candidate is explicitly unavailable at horizon 7 and receives zero
coverage there. Future rain is never assumed known, held constant, or set to zero.
Pressure and moisture are excluded because Phase 3 displacement associations were weak
or negative. Middle hydrologic predictors are excluded because their adjusted
rain-to-displacement evidence was weak.

ARIMAX parameters use conditional least squares on the exact dated equations. Gaussian
model-based intervals propagate the fitted innovation variance through the AR(1)
recursion; parameter and distribution limitations are reported.

## Metrics, subsets, and uncertainty

- Primary: MAE. Secondary: RMSE, signed bias, and MASE.
- Each origin's MASE denominator is the mean absolute one-day change between consecutive
  eligible training targets, using exact dates within one water year and installation
  segment. It is computed from training information only and requires 30 differences.
- Wet season is October through April; dry season is May through September.
- Results are reported overall, by horizon, water year, season, selection/evaluation
  stage, and early/late half of the fixed evaluation calendar interval.
- A high-movement forecast is one whose absolute realized target exceeds the 95th
  percentile of absolute eligible target values available in that origin's training
  data. The threshold is recomputed at every origin and never uses future values.
- Paired MAE differences use identical common origins. A seed-170 moving-block bootstrap
  with 1,000 replicates and three-origin blocks gives a dependence-aware 95% interval.
  The interval is descriptive and does not remove model-selection bias.

## Prediction intervals and residual diagnostics

Declared interval levels are 80% and 95%. Baselines use the past-residual rule above.
ARIMA uses statsmodels forecast intervals; ARIMAX uses its declared Gaussian recursive
interval. For every level, report empirical coverage, average width, and the Winkler
interval score.

Out-of-sample error diagnostics include bias, median absolute error, 95th-percentile
absolute error, skewness, excess kurtosis, ACF through lag 10, and a Ljung–Box statistic
at `min(10, floor(n/5))`. Ljung–Box results are labeled approximate because skipped
origins, horizon overlap in forecast construction, model selection, and non-Gaussian
tails complicate its null distribution. In-sample fit diagnostics are never presented
as out-of-sample evidence.

Stability outputs include performance by water year, wet/dry season, high-movement
status, early/late period, coefficient median/IQR/range, convergence and forecast
failure rates, and model coverage.

## Selection and missing-origin handling

- Candidate definitions are frozen here; there is no automated order, lag, or feature
  search.
- A candidate must produce point forecasts at at least 80% of core selection origins
  for a target/horizon to be selection-eligible. The prior-year and ARIMAX candidates
  remain reported as secondary comparisons if lower coverage prevents selection.
- Selection-stage MAE is compared on the intersection of origins available to all
  selection-eligible candidates. At least 30 common forecasts are required. If fewer
  remain, retain `zero_change` and report the comparison as insufficient.
- The lowest selection-stage MAE is retained separately for each target and horizon.
  If candidates are within 5% of the best MAE, retain the simpler candidate according
  to the fixed order: zero, expanding median, persistence, prior-year seasonal, ARIMA
  mean, AR(1), AR(2), ARMA(1,1), weekly AR, then ARIMAX.
- Later evaluation and the post-resume check do not revise the retained model. Their
  best observed model may be described, but it is not retroactively selected.
- Every scheduled attempt is stored in the ignored processed layer with `ok`,
  `ineligible_core_origin`, `insufficient_training`, `feature_unavailable`,
  `fit_failure`, `forecast_failure`, or `insufficient_interval_calibration`. Aggregate
  coverage and failure counts are versioned.

## Changepoint analysis

Changepoints are separate from forecast fitting and selection. Analysis uses each exact
contiguous eligible target-change run of at least 180 days, never a sequence spanning a
gap, water-year reset, installation change, topple/relocation, or successor ID.

- Minimum segment length: 30 days.
- PELT with L2 cost and penalties `k * log(n) * variance`, for `k = 1, 2, 4`.
- Binary segmentation with L2 cost and 1, 2, or 3 changes when run length permits.
- Candidate dates within seven days are grouped for sensitivity support.
- A group supported by at least two settings and both methods is `method_stable`; one
  supported by at least two settings but one method is `within_method_only`; otherwise
  it is `unstable`.
- Metadata comparison uses documented target instrument/cable changes, the rain-gauge
  interruption, toe topple/relocation, and water-year resets. Event comparison uses the
  three Phase 3 rain-selected storms and run-specific days above the 95th percentile of
  absolute displacement change. A candidate within seven days is classified
  `metadata_aligned` first, otherwise `event_aligned`, otherwise `unexplained`.

These classifications are temporal comparisons, not proof of a physical slope-regime
change. Penalty- or method-unstable results remain explicitly unstable.

## Reproducibility boundary

Per-origin predictions, observation-bearing residuals, coefficients, and changepoint
work tables stay under git-ignored `data/processed/cleveland_corral/`. Version control
contains this contract, model specifications, aggregate diagnostics, aggregate tables,
curated figures, tests, notebook, and documentation only. The build uses deterministic
ordering and seed 170 wherever randomness is required.
