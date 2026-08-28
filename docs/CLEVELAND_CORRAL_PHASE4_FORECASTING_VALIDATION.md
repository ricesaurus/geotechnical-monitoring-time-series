# Cleveland Corral Phase 4 forecasting and chronological validation

**Phase:** 4 — forecasting, regime analysis, and chronological validation

**Report date:** 2026-08-29

**Official release:** [USGS DOI 10.5066/P1P9DMFX](https://doi.org/10.5066/P1P9DMFX)

**Time basis:** fixed PST, UTC−08:00 year-round

## Decision

**Proceed to Phase 5 with a negative forecasting result and explicit limits.** The
frozen selection procedure retained zero change for middle displacement at one day,
AR(1) and AR(2) models for middle displacement at two and seven days, persistence for
toe displacement at one day, and ARMA(1,1) models for toe displacement at two and
seven days. On the later, untouched evaluation periods, however, zero change (tied
numerically with the expanding median) had the lowest observed MAE at every target and
horizon. Paired moving-block bootstrap intervals for each nonzero retained model's MAE
difference relative to zero were wholly above zero. The frozen choices were not
revised after evaluation.

The predeclared rain-lag-2 ARIMAX candidate did not improve on zero change in the long
toe evaluation at one or two days and was unavailable by construction at seven days.
Some dynamic models performed better than zero during the short post-rain-resume
external-time check, but that check contains only 25–26 forecast origins and did not
trigger reselection. Prediction intervals were generally conservative, residuals were
often heavy-tailed, and changepoint dates were mostly method-dependent. These results
do not justify a causal mechanism, a warning threshold, or operational deployment.

## Frozen design and leakage controls

The forecasting contract was version controlled before any Phase 4 comparison in
[`FORECASTING_CONTRACT.md`](phase4/FORECASTING_CONTRACT.md). It declares:

- Phase 3 eligible daily first differences for `mid_E2_B` and `toe_E5_C` as targets;
- stable middle (2009-02-12 to 2016-01-21), long pre-topple toe (2006-11-30 to
  2016-01-21), and post-rain-resume external-check (2016-01-28 to 2017-03-15)
  windows, without successor splicing;
- 1-, 2-, and 7-day horizons on fixed, never-shifted 14-day origin schedules;
- expanding calendar histories with missing days retained as missing, minimum training
  of 365 calendar days and 300 eligible target observations, and an origin-through-
  target path confined to one segment and water year;
- earlier selection cutoffs of 2013-08-31 for the middle window and 2012-12-31 for the
  toe window, with later dates held untouched for evaluation;
- zero change, persistence, expanding median, and prior-year baselines; predeclared
  ARIMA candidates in levels of the already differenced target (`d=0`); and a toe-only
  ARIMAX using target lag 1 and rain lag 2;
- MAE as the primary metric, common-origin comparison, at least 80% candidate coverage,
  a 5% complexity tie rule, training-only MASE scaling, and moving-block uncertainty;
- forecast-time feature availability, empirical baseline intervals from prior realized
  residuals only, explicit fit failures, and no silent replacement model.

At horizon 1, rain lag 2 is known at the forecast origin; at horizon 2 it is the
origin-day rain value. The same feature would require future rain at horizon 7, so the
ARIMAX candidate is deliberately unavailable there. Prior-year February 29 forecasts
are likewise unavailable rather than shifted. A seed-170 synthetic regime-shift
example demonstrates why random splitting can leak the later regime: its apparent MAE
is 2.023 versus 4.696 under the honest chronological split. It is labeled synthetic
and is not a USGS result.

## Forecast results

### Frozen selection and untouched evaluation

| Target window | Horizon | Frozen model | Selection MAE | Later MAE | Later zero MAE | Paired MAE difference vs zero (95% block CI) |
|---|---:|---|---:|---:|---:|---:|
| Middle stable | 1 day | Zero change | 0.253 | 0.056 | 0.056 | 0.000 (same model) |
| Middle stable | 2 days | AR(1) | 0.213 | 0.114 | 0.070 | +0.044 (+0.026, +0.059) |
| Middle stable | 7 days | AR(2) | 0.142 | 0.105 | 0.069 | +0.036 (+0.021, +0.048) |
| Toe pre-topple | 1 day | Persistence | 0.351 | 0.203 | 0.114 | +0.088 (+0.051, +0.126) |
| Toe pre-topple | 2 days | ARMA(1,1) | 0.387 | 0.201 | 0.157 | +0.044 (+0.027, +0.063) |
| Toe pre-topple | 7 days | ARMA(1,1) | 0.323 | 0.154 | 0.115 | +0.039 (+0.020, +0.056) |

MAE units are centimetres per day because the forecast target is the published daily
displacement first difference. Differences above are model MAE minus zero-change MAE
at identical successful origins; positive values favor zero. The retained model and
observed later best are recorded together in
[`selection_decisions.csv`](../reports/tables/phase4/selection_decisions.csv), with an
explicit field stating that evaluation does not revise selection. Complete MAE, RMSE,
bias, MASE, counts, and coverage are in
[`validation_metrics.csv`](../reports/tables/phase4/validation_metrics.csv).

The later result is not evidence that movement is physically always zero. It means
that, at the predeclared sparse origins and under MAE, a zero-change point forecast was
hard to beat because most eligible daily changes were small and occasional excursions
dominated error. This is a forecast-design result, not a statement that the slope was
stationary or inactive.

### Rain-conditioned candidate

The long-toe ARIMAX model had later MAE 0.179 at one day and 0.211 at two days, compared
with zero-change MAE 0.114 and 0.157. Its paired MAE differences were +0.066 (95% block
CI +0.044 to +0.090) and +0.055 (+0.031 to +0.077). The later rain coefficient was
positive and comparatively tight around 0.0103, but coefficient sign and stability do
not establish incremental forecast value or causation.

The post-rain-resume external-time check is informative but small. The lowest observed
MAE was 0.184 for ARIMAX at one day, 0.212 for AR(2) at two days, and 0.213 for AR(2)
at seven days, versus zero-change MAE of 0.285, 0.385, and 0.260. The frozen long-window
models were not reselected, and the 25–26 origins are insufficient for a broad
generalization.

### Regime and high-movement diagnostics

Later errors varied by water year and evaluation half. For example, the middle AR(1)
two-day MAE rose from 0.082 in the early half to 0.145 in the late half, while the toe
ARMA(1,1) two-day MAE fell from 0.267 to 0.138. Zero change remained lower within each
of those halves. Wet/dry results were also target- and horizon-dependent rather than a
consistent seasonal advantage.

High movement is defined separately at every origin using only the absolute training
target's 95th percentile. Later high-movement origins were rare: zero to two per
target/horizon stratum. Their errors were much larger, but such tiny counts cannot
support stable high-movement skill claims. Full water-year, season, evaluation-half,
and training-q95 subsets are in
[`stratified_metrics.csv`](../reports/tables/phase4/stratified_metrics.csv).

## Prediction intervals and residual diagnostics

Baseline intervals use only previously realized residuals, with at least 30 residuals;
ARIMA/ARIMAX intervals use their state-space forecast distribution. At later origins,
the retained middle AR(1)/AR(2) 80% and 95% intervals both achieved 100% coverage and
the retained toe ARMA(1,1) models achieved 96.1–100% at 80% and 98.7–100% at 95%.
Their widths show that this apparent coverage came with conservative intervals. The
toe persistence interval was closer to nominal at 86.8% and 97.4%. Zero-change 80%
coverage ranged from 79.3% to 92.1% across the six evaluations; its 95% coverage ranged
from 97.2% to 100% and became very wide for the heavy-tailed toe target.

Approximate Ljung–Box checks through lag 10 did not show strong residual sequence
dependence for the retained later forecasts, but tail shape remains a concern. Excess
kurtosis was about 11.1 for toe persistence at one day and 16.8 for toe ARMA(1,1) at
two days. Middle AR(2) seven-day residuals also had excess kurtosis about 4.6. Small
origin counts and sparse extremes limit formal diagnostic power. Aggregate interval,
Winkler-score, residual ACF, skew, tail, and Ljung–Box results are in
[`interval_diagnostics.csv`](../reports/tables/phase4/interval_diagnostics.csv) and
[`residual_diagnostics.csv`](../reports/tables/phase4/residual_diagnostics.csv).

## Model stability, coverage, and failures

Expanding AR coefficients underwent pronounced early-record shifts before stabilizing:
the middle AR(1) coefficient moved from near zero to above 0.8 in 2011, and the toe
AR(1) coefficient passed through several early regimes before settling near 0.75–0.80.
The toe ARIMAX rain coefficient likewise changed materially before the later period.
Within the later evaluation, the middle AR(1) median was about 0.818, the toe AR(1)
median about 0.760, and the toe ARIMAX rain coefficient median about 0.0103. Later
tightness must not be rewritten as whole-record stability.

Every scheduled attempt is accounted for. Of 10,746 rows, 9,427 are successful, 905
are ineligible core origins, 309 are feature-unavailable, and 105 are explicit fit
failures. ARIMAX horizon-7 and prior-year February 29 absences are contractual feature
unavailability. The largest model-stage-horizon fit-failure fraction is 7.52%, for the
mean-only ARIMA; no failure is replaced by another forecast. See
[`parameter_stability.csv`](../reports/tables/phase4/parameter_stability.csv) and
[`model_coverage_failures.csv`](../reports/tables/phase4/model_coverage_failures.csv).

## Changepoint sensitivity

Changepoints were analyzed separately from forecasting and only inside exact eligible
target runs of at least 180 days, within one segment and water year. PELT L2 used three
predeclared penalty multipliers and binary segmentation used one, two, or three breaks,
all with a minimum 30-day segment. The workflow found 90 raw detections across 14 runs
and grouped dates within ±7 days into 42 candidates.

Only 4 groups were supported by both method families; 24 were supported across settings
within binary segmentation only, and 14 appeared in a single sensitivity setting. Of
the 42 groups, 23 lay within ±7 days of a Phase 3 rain-selected event or a run-specific
training-q95 displacement episode, while 19 remained unexplained by those declared
contexts. PELT produced only six raw detections, all under the least or second-least
penalized settings; binary segmentation produced 84 by construction. This sensitivity
precludes declaring a unique physical regime boundary. A nearby event is context, not
evidence that rain caused the detected statistical change.

Exact runs, raw sensitivity detections, grouped candidates, support classes, and
context offsets are in
[`changepoint_run_summary.csv`](../reports/tables/phase4/changepoint_run_summary.csv),
[`changepoint_sensitivity.csv`](../reports/tables/phase4/changepoint_sensitivity.csv),
and [`changepoint_candidates.csv`](../reports/tables/phase4/changepoint_candidates.csv).

## Evidence categories

**Observed data:** eligible published displacement changes, published interval rain,
missingness, documented instrument segments, and the aggregate counts derived from
them.

**Statistical inference:** rolling-origin errors, paired block intervals, interval
coverage, residual diagnostics, fitted coefficients, and algorithmic changepoint
candidates under the frozen design.

**Engineering interpretation:** a predominantly small-change target with rare large
excursions makes zero change a strong MAE benchmark; time-varying forecast skill and
coefficient paths are compatible with changing hydrologic or kinematic conditions and
measurement regimes.

**Speculation:** particular coefficient shifts or changepoints may relate to changing
flow paths, antecedent wetness, snowmelt, deformation modes, or sensor behavior. Phase
4 cannot identify among those mechanisms and makes no causal attribution.

## Reproducibility and deliverables

Rebuild and verify from the preserved Phase 2/3 local layers:

```powershell
./.venv/Scripts/python.exe ./scripts/build_phase4_analysis.py
./.venv/Scripts/python.exe ./scripts/verify_phase4_outputs.py
```

The build writes observation-bearing rolling forecasts, fitted parameters, and
changepoint detections only to ignored Parquet files under
`data/processed/cleveland_corral/`. The 15 version-controlled CSVs are aggregate-only.
Nine curated figures were visually inspected, and
`notebooks/03_phase4_forecasting_validation.ipynb` was executed from a clean kernel.
Reusable logic is in `src/geotech_ts/`; synthetic leakage, calendar-boundary,
forecast-time availability, interval, bootstrap, and changepoint behavior is covered by
tests.

## Phase 5 handoff — not started

Using only verified Phase 1–4 artifacts, synthesize the Cleveland Corral findings into
a reproducible engineering-facing report that explicitly separates observed data,
statistical inference, engineering interpretation, and speculation; reconcile the
negative long-window forecasting result, uncertainty, temporal instability,
changepoint sensitivity, sensor and missingness limitations, and the exploratory
rain-response evidence without new model selection, threshold optimization, causal
claims, or operational-warning recommendations; reproduce and inspect every cited
table and figure; and stop before any deployment, alarm design, or engineering design
decision.
