# Project execution plan

**Project:** California Landslide Monitoring Time-Series Analysis  
**Primary intended site:** USGS Cleveland Corral, El Dorado County, California  
**Active phase:** Project complete — all six phases and GitHub delivery accepted

**Last updated:** 2026-08-29

This is the single source of truth for current execution state. The project scope is in
`docs/PROJECT_SPEC.md`; the long-term curriculum is in `docs/LEARNING_ROADMAP.md`.

## Actual current state

Phase 5 began from verified `main` commit
`f0d462b6a6cfb747bfb1c93ca5e01b92a4ea2dd1`, which exactly matched a freshly
fetched `origin/main` with a clean working tree after Phase 4 pull request #4 was
merged. Before branching, all three preserved raw resources passed SHA-256
verification; the full Phase 2 workflow reproduced 5,356,490 selected 15-minute rows
and 78,108 selected daily rows; the full Phase 3 workflow reproduced 97,868 daily
analysis rows, 3,974 event-match rows, 12 aggregate tables, and nine figures; and the
full Phase 4 workflow reproduced 10,746 forecast attempts, 6,123 fitted-parameter
rows, 90 raw changepoint detections, 15 aggregate tables, and nine figures. Every
Phase 2–4 validator passed, regenerated aggregate tables matched the committed Git
objects, and all 18 Phase 3–4 figures were visually inspected. Work is isolated on
`phase/5-engineering-synthesis`. The canonical report, 24-row source-derived claim
matrix, six-row forecast summary, four Phase 5 aggregate tables, seven-figure report,
portfolio documentation, single reproduction route, and both clean-kernel notebooks
now pass local validation. No new scientific analysis, model selection, threshold
optimization, causal claim, or warning-system design was introduced. Implementation
commit `dc56097637b77711df2859f7276d118c586dc870` is published in the single
verified draft pull request
[#5](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/5),
which targets `main` from `phase/5-engineering-synthesis`. GitHub Actions
`quality-checks` run `33240205047` completed successfully. All six phases and the
end-to-end workflow are complete; no next phase remains.

Phase 4 began from verified `main` commit
`e0ce20b02e16f1c95848417fac34e066b86ef7b7`, which exactly matched a freshly fetched
`origin/main` with a clean working tree. The published pull-request head for Phase 3
and the `main` squash commit have identical trees, and `main` identifies the merge as
pull request #3. Before branching, all three preserved raw resources passed SHA-256
verification, the full Phase 2 ingestion reproduced 5,356,490 selected 15-minute rows
and 78,108 selected daily rows, and the complete Phase 3 workflow reproduced its
97,868 daily-analysis rows, 3,974 event-match rows, 12 aggregate tables, and nine
figures. All Phase 2 and Phase 3 output validators passed. Work is isolated on
`phase/4-forecasting-validation`. The frozen Phase 4 forecasting contract is in
`docs/phase4/FORECASTING_CONTRACT.md`; no Phase 4 model comparison had been run when
that contract was frozen. The complete rolling evaluation now accounts for 10,746
scheduled model/horizon rows, 6,123 fitted-parameter rows, and 90 raw changepoint
detections in ignored processed outputs. Fifteen aggregate tables and nine visually
inspected figures pass the Phase 4 validator, and the restart-and-run notebook executes
without analysis errors. The frozen earlier-period selection retained zero change,
AR(1), and AR(2) for the middle horizons and persistence/ARMA(1,1) for the toe horizons;
zero change, tied with the expanding median, nevertheless has the lowest observed MAE
at all six untouched later evaluations. No model was reselected. The remaining Phase 4
implementation is published in verified draft pull request
[#4](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/4), which
targets `main` from `phase/4-forecasting-validation` and is mergeable. Its first remote
check correctly exposed that one committed-artifact test requested ignored local
Parquet products in a clean checkout; the test now validates committed artifacts only,
while `scripts/verify_phase4_outputs.py` continues to require all three local processed
products after a full build. Corrected commit
`372357301e369cb6620a339f514d5da7cc8941b2` is published, and GitHub Actions
`quality-checks` run `33194308505` completed successfully.

Phase 3 began from verified `main` commit
`9950009e83fec4d87ccbf814553f80f2be5968ac`, which matched a freshly fetched
`origin/main` with a clean working tree after Phase 2 pull request
[#2](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/2) was
confirmed merged. Work is isolated on `phase/3-exploratory-dynamics`. Preserved raw
resources pass the committed checksum manifest, and the existing Phase 2 interim
Parquet products are available for reproducible Phase 3 analysis. Implementation,
tests, the complete reproduction workflow, 12 aggregate tables, nine inspected
figures, an executed restart-and-run notebook, the Phase 3 report, and learning
documentation are complete. Implementation commit
`261371eed45013bdcb92dd9ff291b0c3b8dc6b6b` is published in verified draft pull
request [#3](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/3),
and GitHub Actions `quality-checks` run `32363786311` completed successfully.
Forecasting, ARIMA/ARIMAX fitting, changepoint detection, interpolation, and causal
claims remain out of scope; Phase 4 has not started.

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

## Phase 5 acceptance criteria

- [x] Phase 4 pull request #4 is merged; freshly fetched `main` exactly matched
  `origin/main` at `f0d462b6a6cfb747bfb1c93ca5e01b92a4ea2dd1` with a clean tree
  before branching.
- [x] All preserved raw resources pass SHA-256 verification, and full Phase 2, Phase 3,
  and Phase 4 rebuilds reproduce their committed aggregate evidence before synthesis.
- [x] The final report reuses verified Phase 1–4 evidence without new modeling, tuning,
  causal identification, physical-threshold selection, or operational-warning design.
- [x] A programmatically generated claim-and-evidence matrix routes 24 important claims
  to an exact artifact, locator, reproduction command, evidence category, and caveat.
- [x] The canonical Markdown report contains all 15 required sections, six verified
  key forecast rows, and exactly seven curated Phase 3–4 figures. No PDF is committed
  because the project has no stable PDF-production dependency.
- [x] The portfolio README, notebook index, data documentation, learning notes,
  specification, and concise UCLA Statistics 170-style learning map are complete.
- [x] One top-level PowerShell route supports both full official-source reproduction
  and committed-artifact audit without exposing observation-bearing files.
- [x] Both instructional notebooks execute from clean kernels without cell errors, and
  the report, local links, aggregate safety, and numerical claims pass validation.
- [x] Ruff, 34 tests, environment verification, raw checksum verification, all Phase
  2–5 validators, visual review of all 18 source figures, and the tracked-file safety
  audit pass locally.
- [x] The audited branch is pushed, exactly one verified draft pull request (#5) targets
  `main`, and its GitHub Actions `quality-checks` result is confirmed successful.
- [x] No next phase, deployment activity, alarm design, or engineering design decision
  has begun.

## Completed Phase 5 work

- Reproduced all prior scientific phases from preserved official data before using any
  result in the synthesis.
- Built the canonical engineering report and a validator-backed evidence layer that
  distinguishes observed data, statistical inference, engineering interpretation, and
  speculation or unresolved questions.
- Preserved the central negative forecast result: no frozen dynamic or rain-conditioned
  candidate added later long-window MAE skill over zero change under the declared
  design, and no model was reselected after evaluation.
- Curated seven existing figures rather than generating new scientific outputs, and
  verified all report links, table values, counts, claims, and notebook executions.
- Added a reviewer-facing portfolio route, curriculum map, reproduction receipt,
  software receipt, and full/committed reproduction modes.

## Remaining Phase 5 work

None. Stop here. There is no Phase 6 and no automatically authorized follow-on work.

## Phase 4 acceptance criteria

- [x] Phase 3 PR #3 is merged into a freshly fetched `main`; local `main` exactly
  matched `origin/main` at `e0ce20b02e16f1c95848417fac34e066b86ef7b7` with a clean
  tree before branching.
- [x] Raw SHA-256 verification, a full Phase 2 rebuild and verification, and a full
  Phase 3 rebuild and output verification pass before modeling.
- [x] A version-controlled forecasting contract freezes targets, windows, origins,
  candidates, forecast-time feature rules, metrics, intervals, selection, failure
  handling, and changepoint sensitivities before comparisons.
- [x] Transparent baselines and the predeclared ARIMA/ARIMAX candidates are evaluated
  on leakage-free rolling origins at 1-, 2-, and 7-day horizons where defensible.
- [x] Aggregate forecast error, uncertainty, residual dependence, calibration,
  coverage, stability, and coefficient/failure diagnostics are complete and verified.
- [x] Changepoints are analyzed separately inside exact contiguous target runs and
  compared conservatively with metadata and event context.
- [x] Reusable code, synthetic-fixture tests, deterministic build and validator
  scripts, aggregate-only tables, inspected figures, an executed notebook, report,
  README, data documentation, learning notes, and this plan are complete.
- [x] The audited branch is pushed, exactly one verified draft PR targets `main`, and
  the final commit's GitHub Actions result is confirmed successful.
- [x] Phase 5 has not started.

## Completed Phase 4 work

- Froze the target, window, origin, candidate, feature-availability, selection,
  uncertainty, failure, and changepoint contract before running comparisons.
- Evaluated four transparent baselines and the predeclared ARIMA/ARIMAX candidates at
  fixed 14-day expanding origins and 1-, 2-, and 7-day horizons where features were
  knowable.
- Preserved the frozen selection result while documenting that zero change, tied with
  the expanding median, achieved the lowest observed later MAE in all six long-window
  evaluations; all paired uncertainty intervals for nonzero retained models favored
  zero.
- Recorded interval calibration, residual dependence and tails, water-year/season/
  high-movement/early-late errors, parameter paths, coverage, and every numerical or
  contractual forecast failure without silent replacement.
- Restricted changepoint sensitivity to 14 exact eligible runs and grouped 90 raw
  detections into 42 context-labeled candidates; only four groups had support from
  both method families, so no physical boundary was declared.
- Produced and validated 15 aggregate-only tables, nine visually inspected figures,
  three ignored processed Parquet products, an executed instructional notebook, a
  report, learning notes, and reusable synthetic-fixture tests.
- Published the audited branch in verified draft pull request
  [#4](https://github.com/ricesaurus/geotechnical-monitoring-time-series/pull/4)
  against `main`; corrected its clean-checkout test boundary and confirmed GitHub
  Actions `quality-checks` run `33194308505` succeeded.

## Remaining Phase 4 work

None. Stop here; beginning Phase 5 requires a new assignment.

## Phase 3 acceptance criteria

- [x] Phase 2 PR #2 is merged; freshly fetched `main` exactly matched `origin/main` at
  `9950009e83fec4d87ccbf814553f80f2be5968ac` with a clean tree before branching.
- [x] Preserved raw resources pass SHA-256 verification and existing Phase 2 interim
  products are reused without redownload or source modification.
- [x] Explicit level/change/rain masks retain range concerns, require consecutive dates
  and stable regimes, and never cross gaps, water-year resets, offsets, estimates,
  replacements, relocations, or successors.
- [x] Coverage, blank-versus-absent missingness, exact gap lengths, conventional/robust
  distributions, water-year seasonality, and documented regimes are summarized.
- [x] Robust STL is limited to sufficiently long exact-contiguous daily runs, with
  365/366-day sensitivity; no gap filling is used.
- [x] ADF and KPSS are interpreted jointly; ACF/PACF report daily lag units, sample
  sizes, maximum lags, and approximate bands inside individual regimes.
- [x] A seed-170 AR(1), MA(1), and random-walk learning example is clearly labeled
  synthetic and kept separate from USGS observations.
- [x] Daily relationships use exact dates, a positive-predictor-leads convention,
  declared 0–30-day searches, two precipitation definitions, transformed and
  prewhitened sensitivity, and moving-block bootstrap uncertainty.
- [x] Three events are selected by rain only; 15-minute response diagnostics use
  one-to-one no-reuse matching and compare 8- and 15-minute tolerances over declared
  0–48-hour searches.
- [x] Reusable functions, synthetic-fixture tests, a build script, output validation,
  aggregate-only tables, inspected figures, an executed notebook, report, README, data
  documentation, learning notes, and this plan are complete.
- [x] The audited branch is pushed, exactly one verified draft PR targets `main`, and
  the final commit's GitHub Actions result is confirmed successful.
- [x] Phase 4 has not started.

## Completed Phase 3 work

- Built 97,868 ignored daily analysis rows and 3,974 ignored event-match rows from the
  preserved Phase 2 interim layer; raw and interim data were not edited.
- Produced and validated 12 aggregate diagnostic tables and nine curated figures; all
  figures and the notebook were visually or execution inspected.
- Found robust same-day/next-day rain–hydrologic associations and a modest two-day
  long-window toe rain–displacement association, while middle-displacement and shorter
  toe-period findings remain weak or uncertain after dependence adjustment.
- Demonstrated that naive cumulative-level correlations shrink sharply after valid
  changes and prewhitening, and that event-scale lags are not stable across storms.
- Preserved negative displacement changes and range-concern observations while keeping
  their interpretation explicitly unresolved.

## Remaining Phase 3 work

None. Stop here; beginning Phase 4 requires a new assignment.

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
  common high-frequency timestamp across the selected middle/toe set. Phase 3 used
  deterministic one-to-one nearest matching with 8- and 15-minute sensitivity; one
  event/response result was alignment-unstable and event-to-event lag stability was not
  supported.
- Negative pressure-head and extensometer values are metadata range concerns, not proven
  invalid observations, and require later sensor/engineering interpretation.
- Official GPS pages conflict on whether the one-water-year coverage is 2016–2017 or
  2017–2018; its time zone and full coordinate datum also require metadata/file review.
- Several official landing/catalog publication dates differ; provenance must retain the
  stable DOI, item ID, access date, and observed date discrepancy.
- The need for spectral analysis remains open and data-dependent.
- Later chronological evaluation does not support incremental long-window MAE skill
  over zero change for the frozen dynamic models or rain-conditioned candidate. The
  short post-rain-resume check is small, interval estimates are often conservative,
  rare high-movement origins are too few for stable skill claims, and most changepoint
  groups are method-dependent.

## Project completion state

All six planned phases are complete. The end-to-end
workflow now runs from official-source acquisition and immutable checksums through
sensor-aware quality control, exploratory dynamics, frozen chronological forecasting,
and validator-backed engineering synthesis. Phase 5 adds communication and
traceability only; it does not change the scientific analyses.

No next phase remains. Any future causal study, new monitoring campaign, real-time
forecasting system, threshold or alarm design, engineering design analysis, or spectral
extension would be a separately authorized project with a new specification and plan,
not an automatic continuation of this workflow.
