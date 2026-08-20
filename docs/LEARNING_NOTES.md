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
