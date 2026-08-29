# Data directory

Measurement data layers are local and are not committed to Git. Small metadata-only
provenance inventories in `provenance/` are version controlled; they contain source and
sensor descriptions, evidence URLs, and preliminary compatibility decisions, never
measurement observations.

The primary source is the official USGS Cleveland Corral landslide monitoring release
near U.S. Highway 50 in El Dorado County, California, DOI `10.5066/P1P9DMFX`. Phase 2
downloads only the two monitoring archives and the sensor-description table required
to interpret them.

- `raw/`: immutable files exactly as downloaded
- `interim/`: parsed, standardized, or quality-flagged intermediate files
- `processed/`: analysis-ready tables created entirely by code
- `provenance/`: version-controlled source, sensor, and compatibility metadata

Phase 2 local layout:

- `raw/cleveland_corral/`: the verified official ZIPs, official sensor table, and a
  local acquisition receipt;
- `interim/cleveland_corral/`: selected long-form 15-minute and daily Parquet files with
  original strings, fixed-PST timestamps, installation segments, and explicit QC flags;
- `provenance/cleveland_corral_download_manifest.csv`: versioned resource checksums and
  source metadata;
- `provenance/cleveland_corral_archive_inventory.csv`: aggregate archive-member schema
  and timestamp-grid inspection;
- `provenance/cleveland_corral_qc_summary.csv`: aggregate coverage and flag counts;
- `provenance/cleveland_corral_actual_compatibility.csv`: actual candidate overlap;
- `provenance/cleveland_corral_product_semantics.csv`: aggregate daily/15-minute checks.

Reproduce and verify Phase 2 locally with:

```powershell
./.venv/Scripts/python.exe ./scripts/acquire_cleveland_corral.py
./.venv/Scripts/python.exe ./scripts/inspect_cleveland_corral_archives.py
./.venv/Scripts/python.exe ./scripts/build_phase2_interim.py
./.venv/Scripts/python.exe ./scripts/verify_phase2_data.py
```

No raw archive, sensor-description file, parsed row, measurement observation, or
Parquet dataset is committed.

Phase 3 local processed layout:

- `processed/cleveland_corral/phase3_daily_analysis_series.parquet`: explicit daily
  level/change/rain-definition masks and derived values;
- `processed/cleveland_corral/phase3_event_alignment_pairs.parquet`: ignored
  one-to-one event match details used by the aggregate sensitivity diagnostics.

Both files are generated from the Phase 2 interim products and remain git-ignored.
Version-controlled Phase 3 tables under `reports/tables/phase3/` are aggregate
diagnostics only; they contain no timestamped observation rows. Reproduce them with:

```powershell
./.venv/Scripts/python.exe ./scripts/build_phase3_analysis.py
./.venv/Scripts/python.exe ./scripts/verify_phase3_outputs.py
```

Phase 4 local processed layout:

- `processed/cleveland_corral/phase4_rolling_forecasts.parquet`: ignored scheduled
  rolling-origin forecasts, outcomes, eligibility, intervals, and explicit statuses;
- `processed/cleveland_corral/phase4_rolling_parameters.parquet`: ignored fitted
  parameter paths for stability diagnostics;
- `processed/cleveland_corral/phase4_changepoint_detections.parquet`: ignored raw
  run-specific changepoint detections across predeclared sensitivity settings.

These observation- or origin-bearing files remain git-ignored. The 15 version-controlled
tables under `reports/tables/phase4/` contain aggregate configurations, metrics,
diagnostics, uncertainty, selection decisions, and grouped changepoint context only.
Reproduce and verify them with:

```powershell
./.venv/Scripts/python.exe ./scripts/build_phase4_analysis.py
./.venv/Scripts/python.exe ./scripts/verify_phase4_outputs.py
```

Phase 5 adds four version-controlled aggregate tables under
`reports/tables/phase5/`: the claim-and-evidence matrix, six-row forecast decision
summary, software-version receipt, and full-reproduction count receipt. They contain
no timestamps, origins, targets, predictions, parameter paths, or measurement values.
The claim matrix routes final-report statements back to verified Phase 1–4 aggregates;
it is not a new scientific-analysis layer.

The single top-level route reproduces the complete workflow from the official source:

```powershell
./scripts/reproduce.ps1 -Mode Full
```

Clean checkouts without the excluded observation layers can validate all committed
evidence with `./scripts/reproduce.ps1 -Mode Committed`.

Every downloaded dataset must be accompanied by a versioned provenance record that
contains at least:

- source organization and URL
- site and sensor identifiers
- download date
- measurement units and datum
- timestamp time zone and daylight-saving behavior
- nominal sampling interval
- known sensor maintenance, recalibration, or replacement notes
- a file checksum

Never edit a file in `raw/`. If a correction is required, implement it in code and
write a new file to `interim/` or `processed/` with an explicit quality flag.
