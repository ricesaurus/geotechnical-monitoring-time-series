# Project execution plan

**Project:** California Landslide Monitoring Time-Series Analysis  
**Primary intended site:** USGS Cleveland Corral, El Dorado County, California  
**Active phase:** Phase 0 — project foundation  
**Last updated:** 2026-08-20

This is the single source of truth for current execution state. The project scope is in
`docs/PROJECT_SPEC.md`; the long-term curriculum is in `docs/LEARNING_ROADMAP.md`.

## Actual current state

The existing Python 3.12 scaffold, local `.venv`, package layout, checks, tests, data
folders, notebook guidance, VS Code settings, and GitHub Actions workflow have been
inspected. No USGS records have been downloaded and no analysis has started. Phase 0
documentation and local validation are complete. Git is initialized on `main`; the
staged-file audit, initial commit, and publication remain to be completed and verified.

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

## Phase 0 acceptance criteria

- [x] `./scripts/check.ps1` succeeds, including Ruff, pytest, and environment checks.
- [x] `scripts/setup.ps1` reruns safely and reports native installation failures clearly.
- [x] `AGENTS.md`, `docs/PROJECT_SPEC.md`, `docs/LEARNING_NOTES.md`, and this active plan
  have distinct purposes.
- [x] Documentation identifies the California project and Cleveland Corral primary site,
  treats spectral work as optional, and separates association/prediction from causation.
- [x] Git excludes environments, caches, datasets, credentials, secrets, and temporary or
  machine-specific files while preserving data documentation and placeholders.
- [ ] Git is initialized on `main`; the exact staged set is audited and committed.
- [ ] The public `ricesaurus/geotechnical-monitoring-time-series` repository exists with
  the requested description, `origin` is correct, and `main` is pushed.
- [ ] The remote commit and initial GitHub Actions result are inspected.
- [ ] The working tree is clean and Phase 1 has not started.

## Completed Phase 0 work

- Inspected the partially completed scaffold rather than recreating it.
- Preserved the package, tests, workflow, data layers, notebook outline, and curriculum.
- Defined durable repository rules, project scope, and cumulative Phase 0 learning notes.
- Reconciled the README and planning documentation around Cleveland Corral and causal
  limits.
- Kept all data acquisition and substantive analysis out of Phase 0.

## Remaining Phase 0 work

- Inspect the exact staged files and create the initial commit.
- Create and verify the public GitHub repository, push `main`, and inspect Actions.
- Update this plan with the verified final state and stop before Phase 1.

## Blockers and open decisions

- Git treats this OneDrive workspace as having different filesystem ownership, so Git
  commands use a repository-scoped safe-directory override rather than changing the
  user's global Git configuration.
- GitHub CLI is not installed. Use the connected GitHub capability where possible; install
  and authenticate the CLI only if repository creation or pushing requires it.
- Phase 1 must decide which official Cleveland Corral records and sensor series are
  compatible. Phase 0 makes no sensor selection or data-availability claim.
- The need for spectral analysis remains open and data-dependent.

## Next phase (not started)

The Phase 1 worker should perform a source- and metadata-first audit of official USGS
Cleveland Corral records, documenting provenance and candidate sensor compatibility
before authorizing downloads or analysis.
