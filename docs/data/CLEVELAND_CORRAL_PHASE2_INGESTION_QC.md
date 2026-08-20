# Cleveland Corral Phase 2 ingestion and quality-control report

**Phase:** 2 — ingestion and sensor-aware quality control
**Report date:** 2026-08-20
**Official release:** [USGS DOI 10.5066/P1P9DMFX](https://doi.org/10.5066/P1P9DMFX)
**ScienceBase item:** `65d8f08fd34ec3e1801e3efc`

## Decision

**Proceed to Phase 3 with constraints.** Retain the long middle core as the primary
series set. Retain the toe pre-topple set as a secondary, event-focused set, with
`toe_M1_A`, `toe_E5_C`, and every P8/P9 installation kept as explicit segments. Defer
the short M1_B/P8_D/post-relocation E5 period as a primary analysis window.

Phase 2 found no timestamp parse failures, within-member duplicate timestamps,
malformed values, non-finite values, or common numeric sentinel candidates. It did find
many real gaps and logger-phase changes, two out-of-order source rows, blank sensor
cells, subzero values outside metadata lower bounds, cumulative-series noise and
resets, documented maintenance regimes, and several official schema inconsistencies.
Questionable observations were retained with flags. Nothing was interpolated, imputed,
smoothed, automatically corrected, deleted, or spliced.

This is a data-engineering and QC decision, not a finding about hydrologic response,
landslide mechanism, causation, stationarity, lag structure, or forecast skill.

## Acquired official resources

Only the two primary data archives and the sensor table required to interpret their
installation regimes were downloaded. GPS, campaign survey, GIS, shear-depth, graphics,
and unrelated release files were not acquired.

| Resource | Bytes | USGS MD5 | Verified SHA-256 |
| --- | ---: | --- | --- |
| `Cleveland_Corral_15_Minute_Data.zip` | 6,479,946 | `6bf8a24011063d9118c065e06e081fc4` | `ef77c4efab9229edec5d0433d20654a17a06cfa8ae5eeb9d1bd0f57708171d88` |
| `Cleveland_Corral_Daily_Data.zip` | 100,977 | `dac017f158fa5113a2b75236b565674b` | `7f2534a7453df5a68137e66de06cfb20d17c4ca79fcb5e9da234c739a4b374b7` |
| `Cleveland_Corral_Sensor_Descriptions.csv` | 9,858 | `4f7a3533e2313aa9839ddae11f43e60d` | `c2f3f706f601850b69cbc7244c938c3f51b20963ece16eed505797fca638a728` |

The exact URLs, upload timestamps, item update timestamp, access timestamp, license,
checksums, and relative raw-layer identifiers are in
[`cleveland_corral_download_manifest.csv`](../../data/provenance/cleveland_corral_download_manifest.csv).
Raw resources and the local acquisition receipt are under git-ignored
`data/raw/cleveland_corral/` and are not in Git.

## Reproduction boundary

The complete local workflow is:

```powershell
./.venv/Scripts/python.exe ./scripts/acquire_cleveland_corral.py
./.venv/Scripts/python.exe ./scripts/inspect_cleveland_corral_archives.py
./.venv/Scripts/python.exe ./scripts/build_phase2_interim.py
./.venv/Scripts/python.exe ./scripts/verify_phase2_data.py
./scripts/check.ps1
```

The downloader fails closed: an existing raw file is never overwritten and must match
official size and MD5 before it is accepted. Downloads use a temporary file and become
raw resources only after verification. The parser reads ZIP members without extracting
or modifying them. Local observation-bearing outputs are Parquet files under
git-ignored `data/interim/cleveland_corral/`. Only aggregate counts, coverage dates,
schemas, flags, and provenance are version controlled.

## Archive members and actual schemas

The 15-minute archive contains 44 CSV members: 22 middle, 20 toe, and two upper. The
daily archive contains five CSV members: two middle, two toe, and one upper. Every CSV
has three citation/product-description lines, then a header on line 4.

| Product | Timestamp field | Actual form | Rows in all members | Product meaning |
| --- | --- | --- | ---: | --- |
| 15-minute | `date_time_PST` | un-offset `M/D/YYYY H:MM` string | 1,300,995 | Near-real-time observations on station/logger grids; middle and toe clock phases vary. |
| Daily | `date` | un-offset `M/D/YYYY` string | 15,070 | Rain is a daily maximum; every other selected sensor is a daily median of 15-minute values. |

The exact member-level row counts, columns, byte sizes, CRC32 values, first and last
timestamps, minute phases, gaps, and ordering checks are in
[`cleveland_corral_archive_inventory.csv`](../../data/provenance/cleveland_corral_archive_inventory.csv).
The 15-minute station totals are 705,470 middle rows, 562,107 toe rows, and 33,418
upper rows. The daily station totals are 7,775 middle rows, 6,871 toe rows, and 424
upper rows.

Important source-schema findings are preserved rather than normalized away:

- All 13 selected official sensor IDs occur in both product types.
- WY2011 and WY2014 name the second, cumulative rain field
  `mid_midprecipitation_mm_mid_R` rather than `mid_cumprecipitation_mm_mid_R`.
- WY2015 assigns the exact same `mid_precipitation_mm_mid_R` header to both rain
  fields. Field order and values establish that the first field is the 15-minute amount
  and the second is water-year cumulative. Ingestion therefore retains source-column
  position and per-sensor field ordinal.
- The upper 15-minute filenames are one nominal water year behind their preamble and
  timestamps: `CCupper_WY1998.csv` contains WY1999 and `CCupper_WY1999.csv` contains
  WY2000. These contextual upper records are not selected.
- Both middle daily preambles say “toe station.” The member paths, headers, sensor IDs,
  and values identify them as middle files; the inaccurate preamble is retained in the
  inventory.
- `CCtoe_daily_2001_2017.csv` actually begins 2003-02-21, consistent with its preamble
  but not the filename's first year.

## Timestamp interpretation and grid QC

The release states that all times are Pacific Standard Time and the high-frequency
header explicitly says `date_time_PST`. The files contain no numeric UTC offset or
daylight-saving flag. Ingestion therefore:

1. preserves every original timestamp string;
2. parses it as a naive local clock reading;
3. attaches a fixed UTC−08:00 `PST` offset for all seasons; and
4. converts deterministically to UTC only from that fixed offset.

No daylight-saving transition is silently applied. Daily dates are local PST calendar
summary labels, not instantaneous readings; their stored midnight representation is a
deterministic label for joining daily products.

All 49 members had zero timestamp parse failures and zero duplicate timestamps within a
member. Daily members form complete one-day grids within each file. The 15-minute
members show:

| Station | Gap steps | Missing expected 15-minute intervals | Irregular steps | Phase-changing/off-grid steps |
| --- | ---: | ---: | ---: | ---: |
| Middle | 16,765 | 33,238 | 48,171 | 41,751 |
| Toe | 18,976 | 55,478 | 44,291 | 35,733 |
| Upper | 905 | 7,145 | 919 | 202 |

These are source-grid counts, not inserted rows. An absent interval is not converted to
an observation. The toe files contain two out-of-order source rows: 1997-11-05 16:42
is three minutes earlier than its predecessor in WY1998, and 2011-05-06 10:48 is 28
minutes earlier than its predecessor in WY2011. Selected toe records inherit the second
row's ordering flag; the first lies outside the selected sensor period.

## Missing and special values

Blank CSV fields are the observed missing-value convention. They remain blank in
`value_original`, become missing numeric values only in the parsed field, and receive
`flag_missing_value`. A missing interval and a blank measurement are different:
the former has no source row, while the latter is a source row whose sensor field is
blank. Recorded zero remains a valid observed zero.

Across the selected data there were no malformed nonblank tokens, non-finite tokens,
or common sentinel candidates such as `-999` or `-9999`. Range checks are concerns, not
deletions. All range concerns were below official lower bounds; none exceeded an
official upper limit. Subzero pressure-head and extensometer values are common and may
reflect zero reference, calibration, resolution, noise, or physical interpretation
that requires engineering review. The two negative interval-rain concerns are a value
near floating-point zero on 2010-10-05 and −0.08 mm on 2013-05-15.

## Actual selected-sensor coverage and missingness

The table reports rows only within documented operating segments. Missing percentages
are blank sensor cells on an available station timestamp grid, not absent timestamp
intervals.

| 15-minute series | First nonmissing PST | Last nonmissing PST | Nonmissing | Blank within segment | Blank % |
| --- | --- | --- | ---: | ---: | ---: |
| `mid_R` cumulative | 1997-03-22 14:09 | 2018-09-25 08:55 | 704,980 | 490 | 0.07 |
| `mid_P1` | 1997-10-16 00:11 | 2018-09-24 14:25 | 685,466 | 901 | 0.13 |
| `mid_P2` | 1997-10-16 12:24 | 2018-09-24 14:25 | 685,783 | 584 | 0.09 |
| `mid_E2_B` | 2002-10-18 12:49 | 2018-09-24 17:55 | 521,228 | 15,436 | 2.88 |
| `mid_P5` | 2013-02-05 15:45 | 2018-09-24 13:25 | 157,721 | 37,640 | 19.27 |
| `mid_P6` | 2011-10-26 17:26 | 2018-09-24 13:55 | 235,279 | 318 | 0.14 |
| `toe_M1_A` | 2006-11-02 11:04 | 2017-05-17 15:27 | 343,437 | 176 | 0.05 |
| `toe_M1_B` | 2017-05-17 15:42 | 2017-09-25 13:28 | 12,531 | 62 | 0.49 |
| `toe_P7_B` | 2005-06-15 16:35 | 2017-09-25 13:28 | 402,321 | 721 | 0.18 |
| `toe_E5_C` | 2006-11-30 14:47 | 2017-09-25 13:28 | 347,828 | 5,499 | 1.56 |
| `toe_P8_C` | 2013-05-23 19:09 | 2017-03-02 17:57 | 124,364 | 10,247 | 7.61 |
| `toe_P8_D` | 2017-03-09 15:57 | 2017-09-25 13:28 | 18,281 | 914 | 4.76 |
| `toe_P9_D` | 2013-02-05 17:53 | 2017-09-25 13:28 | 153,730 | 747 | 0.48 |

`toe_P8_C` is the clearest metadata-versus-data revision: metadata starts it on
2013-02-06, but its first nonmissing 15-minute value is 2013-05-23. Daily coverage
begins on the same calendar date. Complete segment-level coverage and all flag counts
are in
[`cleveland_corral_qc_summary.csv`](../../data/provenance/cleveland_corral_qc_summary.csv).

## Cumulative resets, maintenance, and regimes

Rain and extensometer observations are source cumulative series. Flags are calculated
without replacing them by increments. The 15-minute cumulative rain channel has 21
observed negative October water-year resets and one additional −0.08 mm decrease after
a gap on 2013-05-15. The daily rain channel has 19 observed October resets and three
unexplained downward adjustments: 1999-10-30, 2007-01-01, and 2013-09-12.

Extensometer measurement noise produces many small negative changes: 71,981
unexplained negative increments for `mid_E2_B` and 73,036 for `toe_E5_C` at 15-minute
cadence. These counts are QC concerns, not evidence of upslope landslide movement and
not grounds for deletion. Later analysis must decide how to derive displacement
increments without crossing resets, gaps, or instrument regimes.

The official sensor-description dates drive the following explicit regimes:

- seven `mid_E2_B` instrument/cable segments;
- two `mid_P1` sensor/depth segments;
- three `mid_P5` amplifier/sensor segments;
- four `mid_R` fire/failure/metadata regimes;
- pre-topple, topple-to-relocation, and post-relocation `toe_E5_C` regimes;
- distinct official IDs for `toe_M1_A` and `toe_M1_B`;
- distinct relocated/depth-specific IDs for `toe_P8_C`, `toe_P8_D`, and `toe_P9_D`.

Files contain no row-level maintenance marker. Phase 2 adds metadata-derived flags for
575 15-minute rows per rain field and six daily rows in the documented 2016-01-22
through 2016-01-27 Sly Park estimate interval. It similarly flags 3,827 15-minute and
40 daily `toe_E5_C` rows from the 2017-03-16 topple through the 2017-04-25 relocation.
The removed topple event cannot be recovered from the release.

## Daily-product relationship

For every selected non-rain sensor, every comparable daily value matches the median
recalculated from available 15-minute values within an absolute numeric tolerance of
10⁻¹²: 40,160 matches and zero mismatches across the 12 non-rain IDs.

At the same 10⁻¹² tolerance, daily rain matches the daily maximum of the cumulative
15-minute field on 6,961 of 7,584 comparable dates. It matches the daily maximum of the
interval-rain field on only 210 dates. The remaining 623 cumulative-field mismatches
occur only in calendar years 1999, 2000, 2007, and 2013 and have a maximum absolute
difference of 1.528 mm. They follow fixed-offset downward adjustments in the daily
product, including the three non-October decreases listed above. Phase 2 therefore
confirms the documented “daily maximum” semantics but does not claim the daily rain
table can be reproduced exactly from the published 15-minute archive on every date.

The comparison counts are in
[`cleveland_corral_product_semantics.csv`](../../data/provenance/cleveland_corral_product_semantics.csv).

## Candidate compatibility and recommendation

| Candidate | Product | Actual common window (fixed PST) | Exact common nonmissing timestamps | Recommendation |
| --- | --- | --- | ---: | --- |
| Middle core: `mid_R`, `mid_P1`, `mid_P2`, `mid_E2_B` | 15-minute | 2002-10-18 12:49 to 2018-09-24 14:25 | 519,695 | **Retain as primary.** Segment E2 and P1; do not cross resets or gaps. |
| Middle core | daily | 2002-10-18 to 2018-09-24 | 5,616 | **Retain for initial cross-series structure.** |
| Toe core pre-topple: `mid_R`, `toe_M1_A`, `toe_P7_B`, `toe_E5_C` | 15-minute | 2006-11-30 14:47 to 2017-03-15 23:53 | 7,774 | **Retain as secondary.** Cross-station clock phases sharply reduce exact joins. |
| Toe core pre-topple | daily | 2006-11-30 to 2017-03-15 | 3,603 | **Preferred initial toe comparison.** |
| Later middle deep: `mid_R`, `mid_P5`, `mid_P6`, `mid_E2_B` | 15-minute | 2013-02-05 15:45 to 2018-09-24 13:25 | 152,972 | **Retain as secondary.** P5 is 19.27% blank within its regimes. |
| Later toe deep pre-topple: `mid_R`, `toe_M1_A`, `toe_P8_C`, `toe_P9_D`, `toe_E5_C` | daily | 2013-05-23 to 2017-03-01 | 1,297 | **Retain as event-focused secondary.** |
| M1_B/P8_D/post-relocation E5 successor period | 15-minute | 2017-05-17 to 2017-09-25 | 0 | **Defer as primary.** Separate short regimes and middle/toe clock phases prevent an exact high-frequency join. |
| M1_B/P8_D/post-relocation E5 successor period | daily | 2017-05-17 to 2017-09-25 | 131 | **Context only.** Too short and change-heavy for a primary record. |

The full candidate table, including logger minute phases and selection constraints, is
[`cleveland_corral_actual_compatibility.csv`](../../data/provenance/cleveland_corral_actual_compatibility.csv).

## Remaining limitations

- The VWC installation depth remains unknown. The released values are compatible with
  neither an unambiguous fraction-versus-percent interpretation nor a documented
  soil-specific calibration, so Phase 3 must keep the official unitless scale.
- No source row flags Sly Park estimates, maintenance, replacements, or relocation;
  those QC fields are date-based inferences from official metadata.
- The daily rain offsets in 1999–2000, 2007, and 2013 are unexplained by the released
  schemas.
- Fixed PST is verified by the release statement and field name, but no separate file
  field documents daylight-saving treatment. The project intentionally applies none.
- Cross-station 15-minute logger phases vary. Any tolerance join or resampling is a
  declared later transformation, not part of Phase 2.
- Negative pressure-head and extensometer values require sensor/engineering judgment;
  a metadata range flag alone does not prove that a reading is invalid.
- Released `toe_E5_C` data omit the topple artifact, so the event cannot be reconstructed.

## Exact recommended Phase 3 objective

Using only the Phase 2 quality-flagged, explicitly segmented records, characterize
coverage, missingness patterns, distributions, trend, seasonality, stationarity, and
within-series dependence for the retained middle core and pre-topple toe subset. Begin
cross-series work on the verified daily products; then evaluate event-focused
15-minute windows only with a declared, sensitivity-tested alignment rule that never
bridges gaps, water-year resets, estimates, replacements, relocations, or successor
IDs. Phase 3 may use descriptive plots, decomposition, ACF/PACF, and carefully qualified
lag exploration, but must not begin forecasting, ARIMA/ARIMAX fitting, changepoint
detection, interpolation, or causal claims.
