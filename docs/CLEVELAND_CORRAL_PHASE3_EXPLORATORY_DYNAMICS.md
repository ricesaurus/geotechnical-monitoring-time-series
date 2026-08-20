# Cleveland Corral Phase 3 exploratory structure and dynamics

**Phase:** 3 — exploratory structure and dynamics

**Report date:** 2026-08-20

**Official release:** [USGS DOI 10.5066/P1P9DMFX](https://doi.org/10.5066/P1P9DMFX)

**Time basis:** fixed PST, UTC−08:00 year-round

## Decision

**Proceed to Phase 4 with narrow, regime-specific targets.** Daily precipitation is
associated with same-day or next-day hydrologic changes in the retained middle and toe
records. A modest two-day rain-to-toe-displacement association persists in the long
pre-topple daily window after differencing and cautious AR(1) prewhitening. The
corresponding middle-displacement result is weak, and the shorter post-rain-gauge-resume
toe period is uncertain. Event-scale lags vary substantially between storms, so no
single 15-minute physical response lag is accepted.

These are exploratory temporal associations, not causal findings, stability claims,
forecast results, or engineering design conclusions. Phase 3 did not interpolate,
splice successors, fit ARIMA/ARIMAX models, detect changepoints, or begin forecasting.

## Scope and analysis masks

The primary set is `mid_R`, `mid_P1`, `mid_P2`, and `mid_E2_B`. The secondary set is
`mid_R`, `toe_M1_A`, `toe_P7_B`, and pre-topple `toe_E5_C`. Later deep instruments and
successors remain deferred from primary inference.

The level-eligibility mask requires a parsed numeric observation inside documented
operation, with no duplicate, non-finite, malformed, sentinel, out-of-order, or
documented maintenance/outage flag. Metadata range concerns are retained and counted;
they are not treated as proof that an observation is invalid. Changes require current
and previous eligible observations on consecutive dates in the same installation
segment. Displacement changes additionally require one water year. Negative
displacement changes remain in the analysis.

Two precipitation definitions were compared:

1. Differences of the published daily cumulative rain level, only for consecutive
   eligible dates inside one water year and rain regime. Both dates must match the
   corresponding daily maximum of the 15-minute cumulative product, which prevents
   differencing across the documented daily-product offsets.
2. Sums of the published 15-minute interval-rain field on days with at least 90 of 96
   nominal intervals, one rain regime, and no fatal eligibility flag. Missing intervals
   are not treated as zero. Two retained range-concern days produce slightly negative
   totals; they are preserved rather than silently clipped.

The complete parameter record is in
[`analysis_configuration.csv`](../reports/tables/phase3/analysis_configuration.csv).
Observation-bearing daily transformations and event matches are reproducible in the
git-ignored processed layer. Only aggregate diagnostics are version controlled.

## Coverage and missingness — observed data

Blank sensor cells and absent timestamps are distinct. For example, the first `mid_P1`
and `mid_P2` operational segments each contain an 83-date absence across the 2002 fire
outage, while many other daily operational segments contain every station date but
still contain blank sensor measurements. The retained pre-topple toe records contain
143 blank daily `toe_E5_C` values, 126 blank `toe_M1_A` values, and 134 blank
`toe_P7_B` values. These patterns shorten exact-date overlaps and can preferentially
remove storm or maintenance periods; missingness cannot be assumed independent of the
process being studied.

The heatmap in
[`01_daily_coverage_missingness.png`](../reports/figures/phase3/01_daily_coverage_missingness.png)
shows the published-row and eligibility pattern. Exact segment-level blank, absent,
eligible, and retained-range counts are in
[`coverage_missingness.csv`](../reports/tables/phase3/coverage_missingness.csv); exact
gap-length counts are in
[`gap_length_distribution.csv`](../reports/tables/phase3/gap_length_distribution.csv).

## Distributions, trend, and seasonality

### Observed data

Daily pressure and displacement distributions are strongly concentrated near zero with
long event tails. Eligible daily displacement changes include negative values:
`mid_E2_B` ranges from −2.5 to 23.6 cm/day and pre-topple `toe_E5_C` from −4.5 to
16.0 cm/day. These negative changes were not clipped. Metadata lower-range concerns
are common in the pressure and displacement level records: 3,763 eligible `mid_P1`,
2,962 `mid_P2`, 818 `mid_E2_B`, 164 `toe_P7_B`, and 1,964 pre-topple `toe_E5_C`
daily levels retain the flag. A range flag is a comparison with released metadata, not
an adjudication of sensor validity.

The temporal plots show pronounced wet-season pulses in both pressure series and toe
moisture, cumulative displacement resets, and major displacement excursions that must
remain inside their water year and documented instrument regime. The water-year
median patterns rise broadly during the wet season and fall during the dry season, but
the cross-year envelopes are wide.

### Statistical interpretation

Robust STL was permitted only on exact, regular, contiguous daily runs at least two
annual cycles long. Pressure and toe-moisture/pressure levels qualified; rain and
displacement levels did not because resets and gaps broke the required continuity. A
365-day period was selected and 366 days was used as a sensitivity check. Level-series
seasonal strength was approximately 0.51 for `mid_P1`, 0.61 for `mid_P2`, 0.95–0.96
for `toe_M1_A`, and 0.61–0.65 for `toe_P7_B`. The similar 365/366 results support an
annual pattern within the selected runs, but STL components remain descriptive and
can absorb event asymmetry or structural behavior.

See the inspected
[`02_daily_levels_sensor_regimes.png`](../reports/figures/phase3/02_daily_levels_sensor_regimes.png),
[`03_daily_distributions.png`](../reports/figures/phase3/03_daily_distributions.png),
[`04_water_year_seasonality.png`](../reports/figures/phase3/04_water_year_seasonality.png),
and
[`05_robust_stl_decomposition.png`](../reports/figures/phase3/05_robust_stl_decomposition.png).

## Stationarity and within-series dependence

### Statistical interpretation

ADF treats a unit root as the null; KPSS treats level stationarity as the null. They
were interpreted jointly on one longest exact-daily run per segment-aware scope, never
across a successor, documented regime, gap, or cumulative reset.

- Representative cumulative rain and displacement levels are generally consistent
  with nonstationarity or yield inconclusive/disagreeing tests.
- The longest `mid_P1`, `mid_P2`, and `toe_M1_A` level runs are inconclusive; the
  longest `toe_P7_B` level run is consistent with level stationarity. Seasonality and
  event pulses limit the simple test interpretation.
- First differences are usually consistent with level stationarity: this holds for the
  longest middle pressure, toe moisture/pressure, and middle/toe displacement-change
  runs. Daily interval-rain totals are also consistent with level stationarity in the
  three qualifying runs.
- Published cumulative-rain differences are less clean: one qualifying run is
  consistent with nonstationarity and three are inconclusive, reinforcing the need for
  precipitation-definition sensitivity rather than assuming the published daily field
  is a daily total.

ACF/PACF use daily lags, a maximum of 60 days or the sample-size limit, and approximate
`±1.96/sqrt(n)` bands. Representative level ACFs decay very slowly: at lag 1,
`mid_P1` is 0.979, `mid_P2` is 0.990, and `toe_M1_A` is 0.987; their PACFs are
dominated by lag 1 with smaller later terms. Daily interval rain has ACF 0.567 at lag
1 and 0.299 at lag 2, while its PACF is 0.567 at lag 1 and approximately −0.033 at
lag 2. Middle displacement changes retain substantial dependence (ACF 0.879 at lag 1
and 0.497 at lag 7); toe displacement changes are much closer to weak short-memory
behavior (ACF −0.050 at lag 1 and −0.206 at lag 2 in the representative run).

The complete results are in
[`stationarity_diagnostics.csv`](../reports/tables/phase3/stationarity_diagnostics.csv)
and
[`acf_pacf_diagnostics.csv`](../reports/tables/phase3/acf_pacf_diagnostics.csv), with
the inspected plot in
[`06_daily_acf_pacf.png`](../reports/figures/phase3/06_daily_acf_pacf.png).

The fixed-seed AR(1), MA(1), and random-walk example is explicitly synthetic and never
mixed with USGS observations. It demonstrates the expected gradual AR ACF decay,
one-lag MA ACF cutoff, and persistent random-walk ACF in
[`09_synthetic_linear_processes.png`](../reports/figures/phase3/09_synthetic_linear_processes.png).

## Daily cross-series relationships

**Lag convention:** positive lag means the predictor occurs earlier and leads the
response. Exact fixed-PST local dates were joined without interpolation. The declared
search is 0–30 days. Uncertainty uses a 500-replicate moving-block bootstrap with
blocks up to 30 observations. The intervals are conditional on the selected peak and
do not correct for searching multiple lags.

### Observed association

In the stable middle window (2009-02-12 through 2016-01-21):

- rain leads `mid_P1` changes by one day: transformed correlations are 0.340 and 0.319
  for the cumulative-difference and interval-sum rain definitions; cautious
  prewhitening reduces them to 0.286 and 0.273;
- rain leads `mid_P2` changes by one day: transformed correlations are 0.224 and 0.227,
  reduced to 0.167 and 0.172 after prewhitening;
- the naive cumulative-rain to middle-displacement level correlation is 0.603 at lag
  zero, but transformed rain-to-displacement peaks are only 0.094–0.104 at the 30-day
  search boundary with intervals spanning zero. Prewhitened lag-zero values are
  0.073–0.077 and remain weak;
- transformed `mid_P1` change to displacement change is approximately −0.024 at 22
  days with an interval spanning zero. `mid_P2` change to displacement change peaks at
  −0.078 at three days (−0.095 after prewhitening). The negative sign and small
  magnitude do not support a simple positive pressure-to-movement lag claim.

In the long toe pre-topple window (2006-11-30 through 2016-01-21):

- rain and toe-moisture changes peak at lag zero (0.432–0.434 transformed;
  0.337–0.342 prewhitened);
- rain and toe-pressure changes peak at lag zero (0.374–0.376 transformed;
  approximately 0.272 prewhitened);
- rain to toe-displacement change peaks at two days (0.189–0.193 transformed;
  0.148–0.155 prewhitened). The two precipitation definitions agree closely;
- moisture/pressure change to displacement-change correlations are weak and negative
  at their selected peaks, so the proposed full sequence is not established by these
  pairwise diagnostics.

The shorter 2016-01-28 to 2017-03-15 toe period produces rain-to-displacement peaks at
18 days before prewhitening and 14 days after it, with bootstrap intervals spanning
zero. This regime-specific result is not stable enough to generalize.

### Interpretation limits

The large naive level correlations (for example, 0.603 for middle rain/displacement
and 0.661 for long-window toe rain/displacement) shrink sharply after valid changes
and prewhitening. Shared accumulation, seasonality, autocorrelation, and resets can
therefore manufacture convincing-looking lag relationships. The adjusted results are
associations only; peak selection, common weather drivers, measurement error,
missingness, and nonlinear/event-specific response remain alternatives.

The full curves and aggregate peaks are in
[`daily_lag_curves.csv`](../reports/tables/phase3/daily_lag_curves.csv) and
[`daily_lag_summary.csv`](../reports/tables/phase3/daily_lag_summary.csv). The
precipitation-definition comparison is plotted in
[`07_daily_lag_sensitivity.png`](../reports/figures/phase3/07_daily_lag_sensitivity.png).

## Event-focused 15-minute behavior

Events were selected using hydrologic input only: the three largest eligible daily
15-minute interval-rain totals in the long pre-topple window, at least seven days
apart. They are 2010-10-24 (135.382 mm; 93 intervals), 2008-01-04 (104.140 mm; 95
intervals), and 2012-11-30 (83.566 mm; 94 intervals).

For each event, interval rain was shifted from 0 to 48 hours in 15-minute steps and
matched to toe-moisture, toe-pressure, or pre-topple toe-displacement changes. Matching
is deterministic nearest-neighbor, one-to-one, and does not reuse observations.
Eight- and 15-minute tolerances were compared.

Only the 2010-10-24 rain-to-moisture peak changed materially with tolerance: 2.00 hours
at 8 minutes versus 4.25 hours at 15 minutes, so it is labeled alignment-unstable.
Most other within-event tolerance results are numerically stable, but the event-to-event
lags and even signs are not:

- rain-to-toe-pressure peaks are +0.624 at 7.75 hours, −0.334 at 11.5 hours, and
  +0.221 at 0 hours across the three events;
- rain-to-toe-displacement peaks are −0.198 at 2.25 hours, −0.515 at 35.5 hours, and
  +0.087 at 43.75 hours.

Because the event results are inconsistent across storms and are based on local peak
searches, Phase 3 defers a general high-frequency lag conclusion. The results are in
[`event_selection.csv`](../reports/tables/phase3/event_selection.csv) and
[`event_alignment_sensitivity.csv`](../reports/tables/phase3/event_alignment_sensitivity.csv),
with the inspected comparison in
[`08_event_alignment_sensitivity.png`](../reports/figures/phase3/08_event_alignment_sensitivity.png).

## Engineering interpretation and speculation

**Engineering interpretation:** the same-day/next-day rain–moisture/pressure
associations are compatible with rapid wetting and pressure response at the monitored
locations, and the long-window two-day toe rain–displacement association is compatible
with delayed movement during wetter conditions. Sensor depth, location, antecedent
wetness, snowmelt, event shape, and kinematic differences could all modify the response.

**Speculation:** different storms may activate different flow paths or landslide
elements, but this dataset and Phase 3 design do not identify those mechanisms. The
observed timing could also reflect autocorrelation, sensor response, unmeasured common
drivers, or selective missingness. No causal mechanism or operational threshold is
claimed.

## Limitations and unresolved questions

- Negative pressure/displacement readings and range concerns remain unresolved rather
  than automatically invalidated.
- The daily cumulative-rain offsets in 1999–2000, 2007, and 2013 remain unexplained;
  affected differences are masked.
- The toe moisture depth and soil-specific calibration remain undocumented.
- ADF/KPSS and approximate ACF/PACF bands are sensitive to seasonality, event pulses,
  structural changes, and finite samples.
- Bootstrap intervals are dependence-aware but conditional on a peak chosen from 31
  lags; they are not simultaneous confidence bands.
- The event analysis covers three large eligible rain days, not every storm, snowmelt
  period, or antecedent-wetness condition.
- Later deep and successor instruments remain secondary and unspliced.

## Reproduction and validation

Run Phase 2 verification, then the Phase 3 build and output validation:

```powershell
./.venv/Scripts/python.exe ./scripts/verify_phase2_data.py
./.venv/Scripts/python.exe ./scripts/build_phase3_analysis.py
./.venv/Scripts/python.exe ./scripts/verify_phase3_outputs.py
./scripts/check.ps1
```

The full workflow writes 97,868 ignored daily-analysis rows, 3,974 ignored event-match
rows, 12 aggregate diagnostic tables, and nine inspected figures. The instructional
notebook can restart the build when processed outputs are absent and otherwise reuses
the verified products.

## Exact recommended Phase 4 objective

Using only Phase 3’s eligible, regime-specific daily transformations, develop and
chronologically validate leakage-free displacement-change forecast baselines and
parsimonious ARIMA/ARIMAX candidates for the stable middle and long pre-topple toe
windows; compare persistence, zero-change, and seasonal baselines at identical rolling
origins and horizons; admit hydrologic predictors only when their availability and
Phase 3 lag evidence justify them; evaluate residual dependence, interval calibration,
and stability; investigate metadata-informed changepoints separately without crossing
instrument regimes; and stop before final engineering synthesis or any causal or
operational-warning claim.
