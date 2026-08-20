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
