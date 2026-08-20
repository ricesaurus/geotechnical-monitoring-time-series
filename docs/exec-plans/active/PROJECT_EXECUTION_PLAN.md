# Project execution plan

**Project:** California Landslide Monitoring Time-Series Analysis  
**Primary intended site:** USGS Cleveland Corral, El Dorado County, California  
**Active phase:** Phase 1 — Cleveland Corral source and sensor audit in progress

**Last updated:** 2026-08-20

This is the single source of truth for current execution state. The project scope is in
`docs/PROJECT_SPEC.md`; the long-term curriculum is in `docs/LEARNING_ROADMAP.md`.

## Actual current state

Phase 1 began from verified `main` commit
`432250c33e5160504d9df14b5ef3e72c4090f927`, which matched a freshly fetched
`origin/main` with a clean working tree. Work is isolated on
`phase/1-source-audit`. The official USGS and ScienceBase metadata audit is documented,
and its inventories identify 30 monitoring IDs across displacement, pressure head,
precipitation/snowmelt, and volumetric water content. The preliminary decision is to
proceed with a long middle-site set and a co-located toe subset. No measurement files
have been downloaded and Phase 2 has not started. Repository checks pass; GitHub
delivery remain before Phase 1 can be marked complete.

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
- [ ] The feature branch is explicitly staged, committed, pushed, and submitted as one
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
- Phase 2 must inspect exact archive members, schemas, timestamps, gaps, water-year
  resets, the Sly Park estimate, and maintenance/relocation boundaries before finalizing
  a series set.
- The toe volumetric-water-content sensor depth is not stated, and daylight-saving
  treatment is not separately documented beyond the release statement that all times
  are Pacific Standard Time.
- Official GPS pages conflict on whether the one-water-year coverage is 2016–2017 or
  2017–2018; its time zone and full coordinate datum also require metadata/file review.
- Several official landing/catalog publication dates differ; provenance must retain the
  stable DOI, item ID, access date, and observed date discrepancy.
- The need for spectral analysis remains open and data-dependent.

## Next phase (not started)

Phase 2 should download only the official DOI-versioned primary monitoring archives,
preserve raw files unchanged with checksums and access metadata, inspect schemas and
timestamps before parsing, and build sensor-aware ingestion and quality flags for the
recommended middle and toe sets. It must preserve official sensor and installation
segments, identify PST encoding, resets, gaps, duplicates, sentinels, estimates,
replacements, and relocations, avoid interpolation, and stop before substantive
time-series analysis or modeling.
