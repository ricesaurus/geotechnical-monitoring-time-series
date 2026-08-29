# Cumulative learning notes

## Phase 0 — project foundations

### Local environment versus GitHub

The local project folder is where code runs and uncommitted work exists. GitHub stores a
remote copy of committed Git history; it is not the Python runtime or a backup of files
that were never committed and pushed.

### Virtual environments

`.venv` isolates this project's Python interpreter and installed packages from global
Python installations and other projects. The environment is reproducible from the
dependency definition and is intentionally not committed.

### Dependency definitions

`pyproject.toml` declares the supported Python version, runtime packages, development
tools, and package layout. Installing the project with its `dev` extra supplies both the
analysis dependencies and quality-check tools.

### Notebooks versus reusable source code

Notebooks explain decisions and present exploration. Reusable ingestion, validation,
modeling, and plotting logic belongs in `src/geotech_ts/`, where automated tests can
exercise it without relying on notebook execution order.

### Git commits and pushes

A commit records an intentional local snapshot. A push transfers committed history to a
configured remote such as GitHub. Untracked or merely saved local files are included in
neither operation unless they are explicitly staged and committed first.

### Tests and automated checks

Tests verify expected behavior; Ruff checks code quality and import/style rules; the
environment check verifies key imports and records installed versions. GitHub Actions
runs repository checks independently on a clean hosted environment.

## Phase 1 — source and sensor compatibility

### Metadata versus observations

Metadata describe what a record is supposed to contain: sensor identity, variable,
unit, location, operating dates, cadence, and known changes. Observations are the actual
timestamped measurements. An operating-date range does not prove continuous data, and a
metadata audit cannot establish missingness, plausible values, event counts, or model
suitability on its own.

### Units and measurement datums

Matching units are not enough. Cleveland Corral pressure values are centimetres of
equivalent water depth above each sensor diaphragm, while extensometer and rain values
are cumulative within each water year and reset on October 1. Sensor depth, a local
zero, and an external elevation datum answer different questions and must not be
interchanged.

### Timestamp time zones

The monitoring release states Pacific Standard Time, but does not separately state a
daylight-saving rule. A future ingestion step must preserve the source timestamps and
verify their encoding before localization or conversion. An assumed one-hour shift can
create a false hydrologic lag.

### Sampling frequency

The official release supplies 15-minute records and daily summaries. Daily rainfall is
a maximum, while daily values for other sensors are medians of 15-minute data; those
products are not interchangeable. An approximately 10-minute GPS solution also uses the
previous hour of raw GPS data, so its timestamp has processing-window meaning beyond a
simple frequency label.

### Sensor location and depth

Hydrologic response depends on where and how deeply a sensor is installed. Middle-site
and toe sensors may see different conditions, and moving a piezometer or changing its
diaphragm depth creates a new physical context even when its name and units look similar.
The toe moisture-sensor depth is not stated, which limits physical interpretation until
more documentation or file metadata are inspected.

### Maintenance history

Broken cables, fire damage, gauge failure, amplifier swaps, sensor replacements, a
toppled extensometer post, and piezometer relocations can cause gaps or regime changes.
They should become explicit segments or quality flags, not be smoothed away or silently
treated as natural changepoints.

### Temporal overlap

Useful multivariate analysis requires the candidate predictor and response records to
coexist. Metadata show a long middle-site rain–pressure–displacement window and a
shorter all-variable toe window. The common window is determined by the latest start and
earliest end, but actual usable overlap can only be calculated after Phase 2 inspects
gaps and timestamps.

### Why compatibility comes before modeling

Modeling incompatible datums, resets, timestamps, locations, or instrument regimes can
produce precise-looking but physically misleading lags and forecasts. Establishing
identity, units, time basis, cadence, location, and change history first narrows Phase 2
to defensible records and makes every later transformation auditable.

## Phase 2 — time indexing, missingness, and sensor regimes

### Raw, interim, and processed data

Raw data are the exact official bytes. Their checksums are identities: if a byte
changes, the file is no longer the acquired source. Interim data are reproducible views
of those bytes with parsed fields, retained source strings, sensor IDs, installation
segments, and quality flags. Processed data will contain later analysis-specific
transformations such as defensible event increments or aligned model tables. Keeping
these layers separate makes it possible to revise a parser or scientific decision
without rewriting history.

### Timestamp grids and irregular sampling

A nominal 15-minute cadence does not mean every timestamp falls on `:00`, `:15`,
`:30`, or `:45`, or that every interval exists. Cleveland Corral station loggers use
several minute phases and sometimes change phase after a gap. Phase 2 therefore checks
the interval between source rows and records phase changes, gaps, and out-of-order rows
instead of forcing timestamps onto a new grid. Fixed PST is attached as UTC−08:00 in
both winter and summer; an automatic daylight-saving shift could manufacture a false
one-hour response lag.

### Missing intervals are not recorded zeros

An absent interval means there is no source row for an expected time. A blank field
means the station row exists but that sensor has no recorded value. A recorded zero is
an observation and may mean no interval rain, a cumulative series at its reset, or a
reading near a sensor reference. Turning either kind of missingness into zero changes
means, variances, event totals, regression coefficients, ACF values, and forecast
errors. Phase 2 inserts no rows and fills no values.

### Cumulative series and water-year resets

Rain and extensometer values accumulate within a water year and reset around October 1.
A negative difference at that boundary is expected behavior, not negative rainfall or
upslope motion. A negative difference elsewhere may be measurement noise, a source
adjustment, an instrument change, or a real concern. Phase 2 retains cumulative values
and separately flags water-year boundaries, observed resets, and unexplained negative
increments. Later event increments must never difference across a reset, gap, or regime
boundary.

### Sensor changes create statistical regimes

Changing a sensor, amplifier, cable, post, depth, or location can change bias,
resolution, physical support, and the relationship between the measurement and the
landslide. The value may keep the same unit while its data-generating process changes.
That makes a replacement a statistical and geotechnical regime boundary. Cleveland
Corral's E2 replacements, P1 depth change, P5 amplifier/sensor changes, M1 replacement,
E5 topple/relocation, and P8/P9 relocations are kept as explicit segments rather than
silently spliced.

### Why interpolation is deferred

Interpolation asserts a shape between observations. Across a storm peak, logger gap,
water-year reset, instrument failure, or relocated sensor, that shape can be both
statistically convenient and physically false. It also creates synthetic
autocorrelation and can make regression or forecasting look better than it is. Phase 2
therefore records the missingness mechanism available from source metadata and stops.
Any later interpolation would require a specific estimand, method, sensitivity check,
and prohibition against crossing documented boundaries.

### Protection for later ACF, regression, and forecasting

ACF assumes meaningful, ordered lags on a defined grid. Regression can mistake shared
seasonality, offsets, or successor regimes for a relationship. Forecast validation can
leak future information if gap filling or scaling sees later data. Preserved timestamps,
separate missingness types, fixed-PST conversion, source roles, and installation
segments give later work the inputs needed to define lags honestly and keep every
transformation inside chronological training windows.

These choices implement the applied learning goal of
[UCLA Statistics 170](https://catalog.registrar.ucla.edu/course/2024/stats170): explore
standard temporal methods on numerical time series and implement the techniques, while
first establishing that the numerical sequence and its time index mean what the method
assumes. In geotechnical terms, the same discipline prevents logger behavior, sensor
replacement, or data repair from being misread as infiltration, pressure response, or
landslide displacement.

## Phase 3 — exploratory structure and dynamics

### Regular versus irregular sampling

A time series is regular when adjacent observations occupy a consistent grid, such as
one value per calendar day. It is irregular when timestamps drift, intervals are
missing, or measurements occur at changing phases. A daily ACF interprets lag 1 as one
day only when the selected observations form an exact contiguous daily run. A
15-minute nearest match must additionally declare how far apart two logger times may
be and must not reuse one observation for multiple matches. Phase 3 therefore uses
exact dates for daily work and one-to-one 8- and 15-minute tolerance rules for selected
events, without interpolation.

### Levels, differences, and cumulative resets

A level is the published state at a time. A first difference is the current level minus
the previous level and describes change only when both observations are consecutive
and comparable. Cleveland Corral rain and displacement reset by water year, so a
difference across October 1 would combine a physical change with a bookkeeping reset.
Phase 3 differences only consecutive eligible observations inside one water year and
one instrument regime. Negative displacement changes are retained; their sign is not
silently reinterpreted as invalid measurement.

Published daily rain is a cumulative daily maximum rather than a verified daily total.
Phase 3 compares valid within-water-year differences with sums of the 15-minute
interval-rain field on adequately covered days. Agreement between conclusions under
both definitions is stronger evidence of robustness than selecting whichever
definition gives the largest correlation.

### Trend, seasonality, and stationarity

Trend is a gradual change in the typical level. Seasonality is repeatable structure at
a calendar period, such as the broad wet-season response visible across Cleveland
Corral water years. A weakly stationary process has a stable mean and variance and an
autocovariance that depends on lag rather than absolute time. A strongly seasonal or
cumulative series is generally not level-stationary even when its physical behavior is
repeatable.

STL can separate an observed series into trend, seasonal, and remainder components,
but it requires a regular sequence. Filling gaps just to make STL run would manufacture
data and dependence. Phase 3 uses robust STL only on exact contiguous daily segments at
least two annual cycles long, selects 365 days, and checks 366 days. Its components are
descriptions, not unique physical mechanisms.

### ADF versus KPSS

The augmented Dickey–Fuller test starts with a unit-root null: a small p-value argues
against that form of nonstationarity. KPSS reverses the burden of proof by starting
with a level-stationarity null: a small p-value argues against stationarity. ADF reject
plus KPSS not-reject is consistent with level stationarity; ADF not-reject plus KPSS
reject is consistent with nonstationarity. Other combinations are inconclusive or
disagreeing. Neither test resolves seasonality, structural changes, bounded event
pulses, or sensor-regime changes, so Phase 3 uses them only inside defensible segments
and alongside plots and ACF behavior.

### What ACF and PACF measure

The autocorrelation function (ACF) measures correlation between a series and its own
lagged values. The partial autocorrelation function (PACF) measures the additional
linear association at a lag after accounting for shorter lags. A gradual ACF decay with
a dominant lag-1 PACF is characteristic of an AR(1)-like process; an MA(1) has an ACF
that cuts off after lag 1 while its PACF decays. A random walk has persistently high
sample autocorrelations because its level is nonstationary. Phase 3 demonstrates these
patterns using a seed-170 synthetic example that is explicitly separate from USGS
observations.

### Why autocorrelation can mislead cross-correlation

Two slowly changing or seasonal series can be highly correlated because each remains
similar to its own recent history, not because one produces the other. Cumulative rain
and displacement levels also share water-year accumulation. Cleveland Corral naive
level correlations are therefore compared with valid changes and cautious
prewhitening. Their sharp reduction after those adjustments is a practical example of
why a large raw cross-correlation is not automatically a physical response signal.

### Lag-sign conventions

Phase 3 defines positive lag as **predictor leads response**. At daily lag 2, for
example, rain on date `t` is paired with displacement change on date `t + 2 days`.
Writing the convention beside every result prevents a common sign reversal when
software packages define or plot cross-correlation differently.

### Temporal association is not causation

Temporal order and dependence-adjusted association may be compatible with the physical
hypothesis, but they do not rule out common weather drivers, antecedent wetness,
snowmelt, missingness, measurement error, sensor response, regime changes, or selective
peak search. Event-to-event lag variation at Cleveland Corral is an additional warning
against a single mechanistic interpretation. The result belongs in one of four clearly
labeled categories: observed data, statistical inference, engineering interpretation,
or speculation.

This implements the UCLA Statistics 170 goals of visualizing time series, diagnosing
stationarity and dependence, and understanding linear-process signatures. The
geotechnical application adds essential constraints: fixed-PST timing, water-year
resets, documented installations, physical location/depth, and the difference between
an exploratory association and a landslide mechanism.

## Phase 4 — forecasting, validation, and regime sensitivity

### A forecast is defined by information time

A forecast is not just a prediction paired with a later observation. It must declare
the origin date, target date, horizon, training window, and exactly what was knowable at
the origin. A rolling-origin design repeatedly fits on the past and evaluates on the
future, preserving time order. Cleveland Corral origins stay on a fixed 14-day calendar
schedule: a missing or boundary-crossing target is marked ineligible rather than moving
the origin to a more convenient date.

The rain-lag-2 ARIMAX example makes feature availability concrete. At a one-day horizon,
the needed rain value is from the day before the origin; at two days, it is origin-day
rain. At seven days, the same equation would require rain after the origin, so the
forecast is unavailable. Using that future rain would answer a conditional scenario
question, not the declared real-time forecast question.

### Why random splits leak time-series regimes

Random train/test splitting assumes observations are exchangeable enough that their
order can be ignored. A time series with a later mean, variance, seasonal, sensor, or
physical regime violates that premise. Random training can then contain samples from
the future regime and make performance look better than it would have been at the
historical forecast origin. The seed-170 synthetic example deliberately shows this:
the same mean model has MAE 2.023 under a leaking random split and 4.696 under a
chronological split made before the shift. It is a learning example, not a USGS result.

### Baselines define whether complexity earns its place

Zero change, persistence, an expanding median, and a same-calendar-date prior-year
value answer different simple forecasting questions. A candidate model has practical
value only if it improves on defensible baselines at identical origins. Comparing
different successful-origin sets can reward a model for skipping hard dates, so Phase
4 first enforces coverage and then uses common-origin errors.

Selection and evaluation have different jobs. The earlier selection period chooses a
model using predeclared rules; the later evaluation estimates how that frozen choice
generalizes. Looking at evaluation and then changing the model would turn the test set
into another tuning set. At Cleveland Corral, frozen AR and ARMA choices lost to zero
change later. Preserving that negative result is the point of honest validation.

### ARIMA on an already differenced engineering target

The modeled target is a valid daily first difference of cumulative displacement. The
ARIMA integration order is therefore fixed at `d=0`; applying another difference would
change the estimand and can overdifference a short-memory change series. AR(1), AR(2),
MA/AR combinations, and a weekly seasonal AR term are alternative dependence
structures for the change target, not automatic upgrades over a baseline.

ARIMAX estimates conditional linear association after target persistence, but a stable
positive rain coefficient does not guarantee lower forecast error and does not prove
rain caused movement. Predictive increment, coefficient interpretation, and causal
identification are three distinct questions.

### Error scales, paired uncertainty, and rare movement

MAE averages absolute error in target units and is less dominated by rare extremes
than RMSE. Bias retains direction. MASE divides absolute error by a naive training
scale computed using only the origin's past, which permits comparison without allowing
future variability into the denominator. No single metric is a physical loss function
unless the decision problem says so.

Forecast errors at neighboring rolling origins are temporally related. Phase 4 uses a
moving-block bootstrap of paired model-minus-zero absolute-error differences, keeping
short local dependence and common origins together. An interval wholly above zero
means the candidate had larger MAE than zero under that design; it is not a universal
proof that the candidate can never help.

High movement is also origin-specific: the threshold is the 95th percentile of
absolute target changes available in training at that origin. A global threshold
computed from the full record would leak later extremes backward. The later validation
contains too few high-movement origins for a stable extreme-event skill claim.

### Prediction intervals need calibration and sharpness

An 80% interval should cover about 80% of future outcomes over repeated comparable
forecasts, but coverage alone is insufficient. Very wide intervals can cover nearly
everything and still be unhelpful. Width and the Winkler score add a sharpness penalty,
while separate 80% and 95% checks expose systematic over- or under-coverage.

Baseline intervals use only residuals already realized before each origin. Model-based
ARIMA intervals rely on the fitted state-space distribution. Heavy-tailed displacement
errors can make nominal Gaussian intervals conservative in ordinary periods yet still
vulnerable around rare excursions. Calibration with only dozens of origins is itself
uncertain.

### Residual diagnostics and coefficient paths

A useful residual should have limited remaining sequence dependence, but a non-small
Ljung–Box p-value is not proof of independence. Small samples, sparse origins, and
heavy tails reduce diagnostic power. Residual ACF, skew, kurtosis, quantiles, and
failure coverage must be interpreted together.

Expanding coefficients answer how the fitted relationship changes as more history is
admitted. A path that shifts sharply early and is tight later is not stable across the
whole record. It may reflect physical evolution, event composition, measurement
regimes, missingness, or model misspecification. Phase 4 reports the path without
choosing among those explanations.

### Changepoint algorithms propose dates; they do not name causes

PELT penalizes added breaks, while binary segmentation is asked for a fixed number of
breaks. Their outputs depend on penalty, break count, minimum segment length, cost
function, and the exact data run. Phase 4 detects only inside contiguous eligible runs
within one segment and water year, then groups nearby dates and labels cross-method,
within-method, or single-setting support.

A candidate near a rain-selected event or large displacement episode is event-aligned
context. It is not evidence that rain caused a new slope regime. Most Cleveland Corral
candidates are method-dependent, so the defensible output is a sensitivity inventory,
not a unique physical segmentation.

These choices extend the time-series curriculum from description to honest forecast
evaluation: define the information set, compare against meaningful baselines, preserve
chronology, diagnose uncertainty and failures, and keep statistical evidence separate
from geotechnical interpretation and speculation.

## Phase 5 — engineering synthesis and reproducible evidence

### A final claim needs a route, not just a citation

The final report is built from verified aggregate artifacts rather than copied notebook
outputs or recollection. Each important claim has an evidence category, source phase,
specific artifact and locator, exact reproduction command, and applicable caveat. A
validator rebuilds the claim text and key forecast values from the Phase 1–4 tables and
checks that the report contains them. This turns traceability into an executable
property of the project.

### Negative findings are engineering information

The untouched later forecast result does not justify replacing the frozen models after
seeing evaluation. Zero change and the expanding median were the lowest-MAE observed
forecasts across all six long-window target/horizon comparisons. Reporting that result
shows why a simple benchmark is part of the scientific question: complexity must earn
its place on future data, not merely fit historical dependence.

### Four evidence categories prevent interpretive drift

Observed data describe released measurements, metadata, gaps, and workflow counts.
Statistical inference covers estimates whose meaning depends on transformations,
windows, origins, and uncertainty procedures. Engineering interpretation relates those
patterns to plausible monitoring behavior while retaining alternatives. Speculation
and unresolved questions include mechanisms, causes, physical thresholds, and alarm
rules not identified by this design. Keeping these categories explicit prevents a
statistically interesting pattern from quietly becoming a safety claim.

### Reproduction has two audiences

A clean-checkout audit must validate committed aggregate evidence without requiring
large excluded datasets. A full reproduction must separately acquire checksum-verified
official files, rebuild observation-bearing local layers, rerun every phase, execute
the notebooks from clean kernels, and regenerate the synthesis. Both routes matter:
the first supports review and continuous integration, while the second demonstrates
end-to-end provenance.

The completed learning path now connects time indexing, quality control, decomposition,
stationarity, ACF/PACF, lag analysis, ARIMA/ARIMAX, chronological validation,
uncertainty, changepoints, and disciplined engineering communication. The durable
[learning map](LEARNING_MAP.md) points each topic to its concrete project artifact.
