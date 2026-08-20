# Project execution plan

**Project:** California Landslide Monitoring Time-Series Analysis  
**Primary intended site:** USGS Cleveland Corral, El Dorado County, California  
**Active phase:** Phase 2 — complete; stopped before Phase 3

**Last updated:** 2026-08-20

This is the single source of truth for current execution state. The project scope is in
`docs/PROJECT_SPEC.md`; the long-term curriculum is in `docs/LEARNING_ROADMAP.md`.

## Actual current state

Phase 2 began from verified `main` commit
`bc0fc8eeaad584857aa92b390b4d1ab18b83250e`, which matched a freshly fetched
`origin/main` with a clean working tree after Phase 1 pull request
[#1](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/1) was
confirmed merged. Work is isolated on `phase/2-ingestion-qc`. Acquisition, archive
inspection, ingestion, quality-control implementation, and actual-coverage assessment
are complete. The official raw resources are preserved locally and checksum-verified;
observation-bearing raw and interim data remain git-ignored. Reusable code, 12 tests,
aggregate-only provenance/QC summaries, the Phase 2 report, and learning documentation
are complete. The decision is to retain the middle core as primary and the segmented
pre-topple toe set as secondary. Implementation commit
`c0d6511400f0503059db70b52c6fc3e236371869` is published in verified draft pull
request [#2](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/2),
and GitHub Actions `quality-checks` run `32353894013` completed successfully. Phase 3
has not started.

### Phase 1 completion baseline

Phase 1 began from verified `main` commit
`432250c33e5160504d9df14b5ef3e72c4090f927`, which matched a freshly fetched
`origin/main` with a clean working tree. Work is isolated on
`phase/1-source-audit`. The official USGS and ScienceBase metadata audit is documented,
and its inventories identify 30 monitoring IDs across displacement, pressure head,
precipitation/snowmelt, and volumetric water content. The decision is to proceed with a
long middle-site set and a co-located toe subset, subject to Phase 2 file and continuity
checks. Repository checks pass, the branch is pushed, and verified draft pull request
[#1](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/1)
targets `main`. No measurement files have been downloaded and Phase 2 has not started.

### Phase 0 completion baseline

The existing Python 3.12 scaffold, local `.venv`, package layout, checks, tests, data
folders, notebook guidance, VS Code settings, and GitHub Actions workflow have been
inspected. No USGS records have been downloaded and no analysis has started.
`./scripts/setup.ps1` reran safely and `./scripts/check.ps1` passed Ruff, two tests, and
environment verification. Git is initialized on `main`; the audited initial commit
`cfefa630520329997d6fdff0ea3fefa15714c4f4` is published to the public
`ricesaurus/geotechnical-monitoring-time-series` repository. The remote commit was
verified through the connected GitHub capability, and its `quality-checks` Actions run
32342816398 completed successfully.

## Phases and dependencies

1. **Phase 0 — project foundation:** environment, repository controls, checks, Git, and
   public GitHub publication. Depends on no later phase.
2. **Phase 1 — Cleveland Corral source and sensor audit:** verify official source URLs,
   metadata, variables, units, datums, time zones, sampling, coverage, and instrument
   history. Depends on Phase 0 acceptance. Do not download data unless Phase 1 explicitly
   authorizes it.
3. **Phase 2 — ingestion and sensor-aware quality control:** preserve raw files, build
   reproducible ingestion, and create transparent quality flags. Depends on the Phase 1
   inventory and selection decisions.
4. **Phase 3 — exploratory structure and dynamics:** characterize coverage, missingness,
   trend, seasonality, stationarity, autocorrelation, and justified lag relationships.
   Depends on Phase 2 analysis-ready, quality-flagged series.
5. **Phase 4 — forecasting, regime analysis, and chronological validation:** compare
   baselines and justified models without future-data leakage; evaluate uncertainty and
   possible changepoints. Depends on Phase 3 findings.
6. **Phase 5 — engineering synthesis and reproducible report:** communicate observed
   results, statistical inference, engineering interpretation, speculation, and limits.
   Depends on validated analyses from prior phases.

Optional spectral analysis may be added only in a later assigned phase if sampling,
record length, and the engineering question support it.

## Phase 2 acceptance criteria

- [x] Phase 1 PR #1 is merged; freshly fetched `main` exactly matched `origin/main` at
  `bc0fc8eeaad584857aa92b390b4d1ab18b83250e` with a clean tree before branching.
- [x] Only the official 15-minute archive, daily archive, and required sensor-description
  table from DOI `10.5066/P1P9DMFX` are preserved in the git-ignored raw layer.
- [x] Source sizes and MD5 values plus locally calculated SHA-256 values are verified and
  recorded without machine-specific paths.
- [x] All 49 CSV members are CRC-checked and inventoried with observed schemas and
  timestamp-grid metadata before full sensor parsing.
- [x] Reusable ingestion preserves original timestamp/value strings, fixed UTC−08:00
  PST interpretation, UTC conversion, official IDs, field positions, and installation
  segments for both 15-minute and daily products.
- [x] Explicit flags cover parse failures, duplicates, ordering, irregular grids, gaps,
  blank/malformed/non-finite/sentinel concerns, metadata ranges, water-year resets,
  negative increments, maintenance, Sly Park estimates, replacements, relocations,
  M1 successors, E5 topple/relocation, and P8/P9 installation changes.
- [x] No observation is deleted, corrected, interpolated, imputed, smoothed, or spliced.
- [x] Local interim Parquet outputs reproduce directly from preserved raw archives and
  remain excluded from Git.
- [x] Aggregate-only archive, coverage/QC, compatibility, segmentation, and
  product-semantics summaries are version controlled and validated.
- [x] Actual coverage and daily-product semantics are inspected; the middle core is
  retained as primary, the pre-topple toe set as secondary, and short successor periods
  are deferred as primary records.
- [x] The Phase 2 report, README, data documentation, learning notes, and active plan are
  updated; `scripts/check.ps1` and raw-manifest verification pass.
- [x] The audited branch is pushed, one verified draft PR is open to `main`, and the
  implementation commit's GitHub Actions result is confirmed successful.
- [x] Phase 3 has not started.

## Completed Phase 2 work

- Implemented fail-closed ScienceBase acquisition, official checksum validation,
  streaming SHA-256, atomic downloads, and local receipts.
- Detected and preserved rain-column schema defects in WY2011, WY2014, and WY2015 using
  source field position and ordinal rather than header-name assumptions.
- Parsed 5,356,490 selected 15-minute long-form rows and 78,108 daily long-form rows into
  local, quality-flagged interim outputs.
- Verified zero timestamp parse failures, within-member duplicates, malformed values,
  non-finite values, and common sentinel candidates; quantified gaps, ordering defects,
  blank cells, range concerns, resets, and documented regimes.
- Confirmed daily medians within 10⁻¹² for all comparable non-rain values and established that
  daily rain primarily follows the maximum cumulative 15-minute field, with 623
  documented mismatches concentrated in four calendar years.
- Quantified actual candidate overlap and revised the P8_C start to its first nonmissing
  date, 2013-05-23, while preserving the earlier metadata installation date.
- Added aggregate-artifact safety validation and local raw-manifest verification that do
  not require network or raw data in ordinary CI.
- Published implementation commit `c0d6511400f0503059db70b52c6fc3e236371869` on
  `phase/2-ingestion-qc`, opened verified draft pull request
  [#2](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/2)
  against `main`, and confirmed GitHub Actions run `32353894013` succeeded.

## Remaining Phase 2 work

None. Stop here; beginning Phase 3 requires a new assignment.

## Phase 1 acceptance criteria

- [x] Official Cleveland Corral project, monitoring, GPS, survey, structures/topography,
  and shear-depth sources are inventoried with evidence URLs.
- [x] Thirty official monitoring IDs are documented: 11 displacement, 16 pressure-head,
  one precipitation/snowmelt, and two volumetric-water-content records.
- [x] Available units, measurement datums, time zone, cadence, coverage, depths,
  instrument changes, and maintenance notes are recorded without filling unknowns.
- [x] A metadata-only compatibility matrix compares temporal overlap, cadence, time
  basis, units/datums, location/depth, continuity, event use, and forecasting use.
- [x] Provisional primary, predictor, contextual, deferred, and unsuitable categories are
  documented, with exact Phase 2 confirmation checks.
- [x] The viability finding is **Proceed**, with limitations distinguished from verified
  metadata.
- [x] Version-controlled metadata inventories pass their dedicated validation tests.
- [x] `./scripts/check.ps1` passes and all generated artifacts and diffs are inspected.
- [x] No measurement observation or archive has been downloaded or committed.
- [x] The audit, learning notes, data documentation, README, and active plan reflect
  Phase 1 findings.
- [x] The feature branch is explicitly staged, committed, pushed, and submitted as one
  verified draft pull request to `main`.
- [x] Phase 2 has not started.

## Completed Phase 1 work

- Verified Phase 0 completion, a clean working tree, and exact equality between freshly
  fetched `main` and `origin/main` at
  `432250c33e5160504d9df14b5ef3e72c4090f927` before branching.
- Inspected the official ScienceBase project and its six child releases, the primary
  monitoring item metadata, the USGS product pages, the Science Data Catalog, and the
  official sensor-description CSV.
- Recorded source provenance, all official sensor IDs, a compatibility matrix, a
  provisional selection, a scope-viability decision, unresolved metadata, and the exact
  Phase 2 objective.
- Added lightweight validation that checks schemas, unique IDs, HTTPS URLs, controlled
  missing values, absence of observation columns, and absence of local paths or
  credential-like content.
- Kept measurement archives, quality control, ingestion, analysis, and modeling out of
  Phase 1.

## Remaining Phase 1 work

None. Stop here; beginning Phase 2 requires a new assignment.

## Phase 0 acceptance criteria

- [x] `./scripts/check.ps1` succeeds, including Ruff, pytest, and environment checks.
- [x] `scripts/setup.ps1` reruns safely and reports native installation failures clearly.
- [x] `AGENTS.md`, `docs/PROJECT_SPEC.md`, `docs/LEARNING_NOTES.md`, and this active plan
  have distinct purposes.
- [x] Documentation identifies the California project and Cleveland Corral primary site,
  treats spectral work as optional, and separates association/prediction from causation.
- [x] Git excludes environments, caches, datasets, credentials, secrets, and temporary or
  machine-specific files while preserving data documentation and placeholders.
- [x] Git is initialized on `main`; the exact staged set is audited and committed.
- [x] The public `ricesaurus/geotechnical-monitoring-time-series` repository exists with
  the requested description, `origin` is correct, and `main` is pushed.
- [x] The remote commit and initial GitHub Actions result are inspected.
- [x] The working tree is clean and Phase 1 has not started.

## Completed Phase 0 work

- Inspected the partially completed scaffold rather than recreating it.
- Preserved the package, tests, workflow, data layers, notebook outline, and curriculum.
- Defined durable repository rules, project scope, and cumulative Phase 0 learning notes.
- Reconciled the README and planning documentation around Cleveland Corral and causal
  limits.
- Initialized `main`, audited the exact staged paths and content for excluded material,
  and committed the Phase 0 foundation.
- Created the requested public GitHub repository, configured `origin`, pushed `main`,
  verified the remote commit, and confirmed the initial Actions run succeeded.
- Kept all data acquisition and substantive analysis out of Phase 0.

## Remaining Phase 0 work

None. Stop here; beginning Phase 1 requires a new assignment.

## Blockers and open decisions

- Git treats this OneDrive workspace as having different filesystem ownership, so Git
  commands use a repository-scoped safe-directory override rather than changing the
  user's global Git configuration.
- Repository creation used a checksum-verified official GitHub CLI 2.97.0 executable in a
  temporary directory because no system installation was available. It is not part of
  the project or repository.
- The toe volumetric-water-content sensor depth is not stated, and daylight-saving
  treatment is not separately documented beyond the release statement that all times
  are Pacific Standard Time.
- The daily rain product differs from the maximum published cumulative 15-minute field
  on 623 dates in 1999–2000, 2007, and 2013; the fixed offsets are not explained by the
  released schemas.
- Cross-station 15-minute logger phases differ, and the successor toe period has no exact
  common high-frequency timestamp across the selected middle/toe set. Alignment remains
  an explicit Phase 3 decision.
- Negative pressure-head and extensometer values are metadata range concerns, not proven
  invalid observations, and require later sensor/engineering interpretation.
- Official GPS pages conflict on whether the one-water-year coverage is 2016–2017 or
  2017–2018; its time zone and full coordinate datum also require metadata/file review.
- Several official landing/catalog publication dates differ; provenance must retain the
  stable DOI, item ID, access date, and observed date discrepancy.
- The need for spectral analysis remains open and data-dependent.

## Next phase (not started)

Phase 3 should use only the Phase 2 quality-flagged, explicitly segmented records to
characterize coverage, missingness patterns, distributions, trend, seasonality,
stationarity, and within-series dependence for the retained middle core and pre-topple
toe subset. Begin cross-series work on verified daily products; evaluate event-focused
15-minute windows only with a declared, sensitivity-tested alignment rule that never
bridges gaps, resets, estimates, replacements, relocations, or successor IDs. Do not
begin forecasting, ARIMA/ARIMAX fitting, changepoint detection, interpolation, or causal
claims.
