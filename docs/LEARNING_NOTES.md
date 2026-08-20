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
