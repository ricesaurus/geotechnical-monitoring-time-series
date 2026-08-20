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
