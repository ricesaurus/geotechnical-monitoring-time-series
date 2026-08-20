# Data directory

Measurement data layers are local and are not committed to Git. Small metadata-only
provenance inventories in `provenance/` are version controlled; they contain source and
sensor descriptions, evidence URLs, and preliminary compatibility decisions, never
measurement observations.

The intended primary source is the official USGS Cleveland Corral landslide monitoring
record near U.S. Highway 50 in El Dorado County, California. Phase 0 does not download
or inspect those records.

- `raw/`: immutable files exactly as downloaded
- `interim/`: parsed, standardized, or quality-flagged intermediate files
- `processed/`: analysis-ready tables created entirely by code
- `provenance/`: version-controlled source, sensor, and compatibility metadata

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
