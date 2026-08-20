# Cleveland Corral source and sensor audit

**Phase:** 1 — source- and metadata-first audit

**Audit date:** 2026-08-20

**Site:** Cleveland Corral landslide near U.S. Highway 50, El Dorado County,
California

**Scope:** Official metadata only. No measurement archive was downloaded or inspected.

## Decision

**Proceed.** Official USGS metadata establish all four planned monitoring families:
precipitation including rainfall and snowmelt, volumetric water content, groundwater
pressure head, and surface displacement. The primary release states that 15-minute and
daily products use Pacific Standard Time, and official operating dates show a common
toe-focused window from 2006-11-30 through 2017-09-25 as well as a longer middle-site
rain–pressure–displacement window from 2002-10-18 through 2018-09-25.

This is a metadata-based viability finding, not a data-quality conclusion. Phase 2 must
inspect file headers, timestamps, gaps, resets, estimates, replacements, and relocation
boundaries before confirming final series or analysis windows.

## Audit method and evidence boundary

The audit opened official USGS product pages, the official Science Data Catalog, and
the USGS-operated ScienceBase project and item JSON endpoints. The small official
`Cleveland_Corral_Sensor_Descriptions.csv` metadata resource was inspected from a
temporary git-ignored location. The 15-minute, daily, GPS, survey, GIS, and shear-depth
measurement files were not downloaded or opened.

Claims below are either:

- **Verified metadata:** stated by an official source opened during this audit.
- **Preliminary interpretation:** a Phase 1 compatibility or selection judgment based
  only on those metadata.
- **Unknown:** explicitly absent, conflicting, or requiring Phase 2 file inspection.

The version-controlled source inventory is
[`data/provenance/cleveland_corral_source_inventory.csv`](../../data/provenance/cleveland_corral_source_inventory.csv),
the full 30-ID sensor inventory is
[`data/provenance/cleveland_corral_sensor_inventory.csv`](../../data/provenance/cleveland_corral_sensor_inventory.csv),
and the comparison table is
[`data/provenance/cleveland_corral_compatibility.csv`](../../data/provenance/cleveland_corral_compatibility.csv).

## Official source inventory

| Stable source ID | Official source | Audit use |
| --- | --- | --- |
| `usgs_cc_project_65a821ec` | [ScienceBase Cleveland Corral project](https://www.sciencebase.gov/catalog/item/65a821ecd34ebad3f34c9a4b) | Site context and authoritative child-release index. |
| `usgs_cc_monitoring_p1p9dmfx` | [USGS monitoring-data release](https://www.usgs.gov/data/landslide-monitoring-data-cleveland-corral-landslide-near-us-highway-50-el-dorado-county), [DOI](https://doi.org/10.5066/P1P9DMFX) | Primary monitoring source and product description. |
| `usgs_cc_sensor_descriptions_csv` | [ScienceBase release item](https://www.sciencebase.gov/catalog/item/65d8f08fd34ec3e1801e3efc) | Official sensor IDs, variables, dates, units, depths, models, ranges, and change notes. |
| `usgs_sdc_cc_monitoring_65d8f08f` | [USGS Science Data Catalog record](https://data.usgs.gov/datacatalog/data/USGS%3A65d8f08fd34ec3e1801e3efc) | Catalog citation, temporal extent, contacts, license, and repository link. |
| `usgs_cc_gps_p91g78vn` | [USGS 10-minute GPS release](https://www.usgs.gov/data/10-minute-gps-monitoring-data-cleveland-corral-landslide-near-us-highway-50-el-dorado-county), [DOI](https://doi.org/10.5066/P91G78VN) | Independent high-frequency toe-displacement candidate. |
| `usgs_cc_survey_p9x62ev3` | [USGS survey-monument release](https://www.usgs.gov/data/survey-monument-positions-cleveland-corral-landslide-near-us-highway-50-el-dorado-county), [DOI](https://doi.org/10.5066/P9X62EV3) | Long-term campaign displacement context. |
| `usgs_cc_structures_p14l6wgv` | [USGS structures and topography release](https://www.usgs.gov/data/landslide-structures-kinematic-elements-and-topography-cleveland-corral-landslide-near-us), [DOI](https://doi.org/10.5066/P14L6WGV) | Sensor/monument spatial and kinematic context. |
| `usgs_cc_depth_p149nurw` | [USGS landslide-depth release](https://www.usgs.gov/data/landslide-depth-measurements-cleveland-corral-landslide-near-us-highway-50-el-dorado-county), [DOI](https://doi.org/10.5066/P149NURW) | Episodic shear-depth context. |

### Primary release contents

The [primary USGS release](https://www.usgs.gov/data/landslide-monitoring-data-cleveland-corral-landslide-near-us-highway-50-el-dorado-county)
states that monitoring ran between 1997 and 2018 and supplies:

1. a sensor-location graphic;
2. pre-1999 sensor coordinates;
3. 2011 and 2017 sensor coordinates;
4. sensor operating timelines;
5. 15-minute monitoring files;
6. daily files using rainfall maxima and medians of 15-minute values for other sensors;
7. sensor descriptions; and
8. piezometer construction diagrams.

The release states that files are organized by water year beginning October 1 and all
times are Pacific Standard Time. It does not separately describe daylight-saving
treatment. The release landing page displays 2024-12-19, while the inspected current
ScienceBase JSON and Science Data Catalog metadata display publication date 2025-12-15.
The DOI and item identifier agree, so this is recorded as a metadata-date discrepancy,
not resolved by inference.

The official rights statement is CC0 1.0 Universal on USGS product pages; the Science
Data Catalog also marks the records public and points to the United States public-domain
label.

## Sensor and variable inventory

### Metadata common to primary monitoring records

The official sensor descriptions and [release page](https://www.usgs.gov/data/landslide-monitoring-data-cleveland-corral-landslide-near-us-highway-50-el-dorado-county)
establish these interpretation rules:

- **Sampling:** 15-minute records and daily summaries are supplied. Actual timestamp
  regularity and gaps require Phase 2 file inspection.
- **Time zone:** Pacific Standard Time. Daylight-saving treatment is not separately
  stated and must not be guessed.
- **Piezometers:** values are pressure head in centimetres, expressed as equivalent
  water depth above each sensor diaphragm. Sensors are vented to the atmosphere.
- **Extensometers:** values are downslope surface displacement in centimetres from a
  linear position transducer and cable. Values reset to zero on October 1 and are
  cumulative within each water year.
- **Rain gauge:** the tipping-spoon gauge records rainfall and snowmelt. One tip is
  0.254 mm. Values reset to zero on October 1 and are cumulative within each water year.
- **Volumetric water content:** the two EC-5 records are described as unitless with a
  stated 0–100 percent range and use a Decagon 5 V calibration formula. Sensor depth and
  soil-specific calibration information are not stated.

The inspected official construction diagram shows that `mid_P1` and `mid_P2` occupy the
same augered hole at different depths, `toe_P7_A` and `toe_P7_B` were installed at
different times, and the driven steel-pipe piezometers use installation-specific
lengths. The official location graphic independently confirms that the middle rain
gauge, E2 response, and middle piezometers occupy one local cluster, while E5, M1, P7,
P8, and P9 occupy the toe area. These figures establish spatial context only; they do
not establish identical subsurface conditions.

### Displacement records

| Sensor ID | Site | Official operating dates | Key verified metadata |
| --- | --- | --- | --- |
| `upp_E6` | upper | 1998-11-19 to 2000-01-16 | Upslope extensometer; 0–1016 cm range. |
| `upp_E7` | upper | 1998-11-19 to 1999-07-18 | Downslope extensometer; 0–1270 cm range. |
| `mid_E1` | middle | 1997-12-12 to 2002-07-26 | Upslope extensometer. |
| `mid_E2_A` | middle | 1997-03-31 to 2002-07-26 | Downslope extensometer; site destroyed by the St. Pauli fire. |
| `mid_E2_B` | middle | 2002-10-18 to 2018-09-25 | Longest stated continuous identifier; repeated instrument swaps and a broken cable. |
| `toe_E3` | toe | 1997-04-04 to 2001-06-21 | Downslope extensometer. |
| `toe_E4_A` | toe | 1997-04-04 to 1998-02-04 | West extensometer; broken instrument. |
| `toe_E4_B` | toe | 1998-04-01 to 2001-06-21 | Replacement west extensometer. |
| `toe_E5_A` | toe | 2002-12-30 to 2005-03-28 | First E5 installation. |
| `toe_E5_B` | toe | 2005-03-28 to 2006-11-02 | New post after shallow failure. |
| `toe_E5_C` | toe | 2006-11-30 to 2017-09-25 | Post toppled 2017-03-16; topple event removed; post relocated 2017-04-25. |

The exact instrument changes, ranges, and unresolved file questions for every ID are in
the sensor inventory. E-series suffixes are treated as distinct records; Phase 1 does
not assume that predecessor and successor installations can be spliced.

### Pore-water-pressure records

| Sensor ID | Site and installation | Diaphragm depth | Official operating dates | Key verified metadata |
| --- | --- | ---: | --- | --- |
| `mid_P1` | middle shallow open PVC tube | 1.79 m then 1.82 m | 1997-10-16 to 2018-09-25 | First sensor may have sunk up to 0.04 m; changed 2006-05-04. |
| `mid_P2` | middle deep open PVC tube | 3.69 m | 1997-10-16 to 2018-09-25 | Sensor may have sunk up to 0.04 m. |
| `mid_P3` | middle direct-burial transducer | 2.40 m | 1997-06-26 to 2001-01-10 | No open tube. |
| `mid_P4` | middle deep driven steel pipe | 4.77 m | 2004-04-07 to 2011-10-25 | Eight sensor/amplifier replacements are listed. |
| `mid_P5` | middle upslope deep driven pipe | 4.47 m | 2013-02-05 to 2018-09-25 | Amplifier changed in 2014; sensor serial changed in 2016. |
| `mid_P6` | middle downslope deep driven pipe | 4.47 m | 2011-10-26 to 2018-09-25 | Sand-filled tip; no replacement stated. |
| `toe_P7_A` | toe shallow open PVC tube | 0.94 m | 2004-11-19 to 2005-06-15 | Initial location. |
| `toe_P7_B` | toe shallow open PVC tube | 1.03 m | 2005-06-15 to 2017-09-25 | New location after shallow failure. |
| `toe_P8_A` | toe east driven pipe | 3.00 m | 2011-03-11 to 2011-09-28 | Sand-filled tip. |
| `toe_P8_B` | toe east driven pipe | 2.41 m | 2011-10-25 to 2013-02-06 | Same location; jacked shallower. |
| `toe_P8_C` | toe east driven pipe | 2.36 m | 2013-02-06 to 2017-03-02 | New bead-tip location 1.8 m west. |
| `toe_P8_D` | toe east driven pipe | 1.62 m | 2017-03-09 to 2017-09-25 | New location and sensor. |
| `toe_P9_A` | toe west driven pipe | 2.14 m | 2011-03-11 to 2011-10-25 | Sand-filled tip. |
| `toe_P9_B` | toe west driven pipe | 3.03 m | 2011-10-25 to 2012-12-11 | Same location; driven deeper. |
| `toe_P9_C` | toe west driven pipe | 2.94 m | 2012-12-11 to 2013-02-05 | Bead-filled tip at same location. |
| `toe_P9_D` | toe west driven pipe | 4.45 m | 2013-02-05 to 2017-09-25 | New bead-tip location 1.1 m east. |

These are local pressure-head records, not elevations tied to an external vertical datum.
Changing depth, tip, sensor, or location can change physical interpretation even when
units remain centimetres.

### Precipitation and soil moisture

| Sensor ID | Site | Variable and unit | Official operating dates | Key verified metadata |
| --- | --- | --- | --- | --- |
| `mid_R` | middle | precipitation including rain and snowmelt; mm | 1997-03-22 to 2018-09-25 | Fire gap 2002-07-26 to 2002-10-18; mechanical failure 2016-01-22 to 2016-01-27; that interval used an estimate from Sly Park gauge. |
| `toe_M1_A` | toe | volumetric water content; unitless | 2006-11-01 to 2017-05-17 | EC-5 using Decagon 5 V calibration; depth not stated. |
| `toe_M1_B` | toe | volumetric water content; unitless | 2017-05-17 to 2017-09-25 | Replacement/successor; continuity with M1_A is unknown. |

The release describes the precipitation channel as rainfall and snowmelt together; it
does not provide a separate snowfall or snow-water-equivalent sensor in the inspected
metadata.

## Candidate compatibility assessment

The detailed matrix is
[`cleveland_corral_compatibility.csv`](../../data/provenance/cleveland_corral_compatibility.csv).
This summary is preliminary interpretation.

| Candidate set | Metadata-only assessment | Main concern |
| --- | --- | --- |
| Middle core: `mid_R`, `mid_P1`, `mid_P2`, `mid_E2_B` | Strongest long-duration combination; same site, stated 15-minute cadence and PST, common 2002-10-18 to 2018-09-25 window. | E2 replacements/cable break, P1 change, possible P1/P2 sinking, rain gaps and one estimated interval. |
| Toe core: `mid_R`, `toe_M1_A/B`, `toe_P7_B`, `toe_E5_C` | Best metadata-only representation of the proposed hydrologic sequence; common 2006-11-30 to 2017-09-25 window. | Rain gauge is at middle site; VWC depth is unknown; M1 replacement and E5 post topple/relocation require segments. |
| Later middle deep: `mid_R`, `mid_P5`, `mid_P6`, `mid_E2_B` | Useful paired deep-pressure comparison from 2013 to 2018. | P5 amplifier/sensor changes and shorter window. |
| Later toe deep: `mid_R`, `toe_M1_A/B`, `toe_P8_C/D`, `toe_P9_D`, `toe_E5_C` | Spatially rich event subset from 2013 to 2017. | P8/P9 relocations and depth changes overlap M1 and E5 changes. |
| 10-minute GPS | Potential independent toe-motion context. | Coverage dates conflict between official pages; time zone and full datum are unresolved; each solution uses the preceding one-hour window. |
| Campaign monument positions | Good long-term spatial context. | About annual and usually collected when dormant; unsuitable for within-event lag or high-frequency forecasting. |
| Copper-pipe shear depths | Useful physical context for possible shear depths. | Episodic measurements only bracket shear timing; unsuitable as a high-frequency response. |

### Resampling implications

The primary release's 15-minute products appear frequency-compatible without initial
cross-frequency resampling, but Phase 2 must still verify timestamp grids. Rain and
extensometer values are water-year cumulative, so event increments would be a later,
code-based transformation that respects resets and gaps. Daily files are not equivalent
raw samples: rainfall uses daily maxima and other channels use daily medians of the
15-minute data.

The GPS candidate would require aggregation from approximately 10-minute solutions and
care because each solution summarizes the previous hour. Campaign survey and shear-depth
records should not be interpolated to 15-minute cadence.

## Provisional candidate-series recommendation

### Recommended primary response series

- `mid_E2_B` for the long middle-site response record, with separate regimes for each
  documented replacement or cable failure.
- `toe_E5_C` for the co-located toe subset, provisionally limited to the pre-topple
  segment ending 2017-03-16 until Phase 2 establishes how the removed topple event and
  2017-04-25 relocation are represented.

### Recommended hydrologic predictor series

- `mid_R` as the only documented on-site precipitation/snowmelt channel.
- `mid_P1` and `mid_P2` as long shallow/deep middle-site pressure-head records.
- `toe_M1_A` as the main soil-moisture record, with `toe_M1_B` held separate until
  continuity and calibration are verified.
- `toe_P7_B` as the long shallow toe pressure-head record.
- `mid_P5` and `mid_P6` for a later deep middle-site comparison.
- `toe_P8_C` and `toe_P9_D` for a later deep toe comparison; `toe_P8_D` remains a
  separate successor segment.

### Useful contextual series

- The approximately 10-minute toe GPS record, after coverage, time-zone, datum, and
  processing-window questions are resolved.
- Campaign monument positions for long-term movement and spatial context.
- Structures, kinematic elements, topography, and shear-depth releases for sensor and
  landslide interpretation.

### Uncertain or deferred series

- Short early extensometers `upp_E6`, `upp_E7`, `mid_E1`, `mid_E2_A`, `toe_E3`,
  `toe_E4_A`, and `toe_E4_B`.
- E5 predecessors `toe_E5_A` and `toe_E5_B`, which should not be spliced into `toe_E5_C`
  without evidence.
- Short or change-heavy pressure records `mid_P3`, `mid_P4`, `toe_P7_A`, all P8/P9
  predecessors, and short successors `toe_P8_D` and `toe_M1_B`.

### Unsuitable as primary high-frequency series

- Campaign monument positions: about annual and commonly collected while the slide was
  dormant.
- Copper-pipe shear-depth measurements: episodic and only bracket movement time.
- The one-water-year GPS release: not a primary long-horizon forecasting target unless
  Phase 2 resolves the official coverage conflict and finds a specific event-analysis
  role.

These labels address compatibility with this project's planned event and forecasting
questions; they are not judgments that the official records are poor quality.

## Unresolved metadata and blockers for final selection

Phase 2 must resolve the following before confirming the series set:

1. Exact archive member names, schemas, timestamp fields, and whether every listed
   sensor occurs in both 15-minute and daily products.
2. Actual sampling regularity, duplicates, gaps, sentinel values, flags, and outage
   intervals.
3. How fixed PST is encoded and whether timestamps remain on standard time throughout
   the year; no daylight-saving rule is separately stated.
4. Exact representation of October 1 cumulative resets and whether records contain
   negative or discontinuous values around maintenance.
5. Which rain values were estimated from Sly Park and how estimates are flagged.
6. Continuity across `mid_E2_B`, `mid_P1`, `mid_P5`, `toe_M1_A/B`, and all relocated
   P8/P9 installations.
7. VWC installation depth, calibration output scale, plausible range, and any
   soil-specific calibration information.
8. Representation of the `toe_E5_C` topple removal and relocation.
9. GPS coverage date conflict: the USGS product page says 2016-10-01 to 2017-09-30,
   while the current Science Data Catalog says 2017-10-01 to 2018-09-30.
10. GPS timestamp zone, UTM datum, coordinate fields, quality fields, and the
    consequences of its trailing one-hour processing window.
11. Whether the release-date discrepancies reflect revisions that require recording a
    version or last-modified date in provenance.

None of these metadata issues requires returning to the project planner before Phase 2,
but all constrain final selection and analysis claims.

## Exact recommended Phase 2 objective

Download only the official DOI-versioned primary monitoring archives selected above,
preserve each raw file unchanged with checksum and access metadata, inspect schemas and
timestamps before parsing, and build sensor-aware ingestion plus quality flags that:

- retain each official sensor ID and installation segment;
- identify PST encoding, water-year resets, gaps, duplicates, sentinels, estimates,
  replacements, and relocations;
- initially ingest the middle core and toe core without interpolation;
- compare 15-minute and daily product semantics without treating daily summaries as raw
  observations; and
- use chronological validation boundaries in every later derived step.

Phase 2 should confirm or revise the provisional series selection only after those
checks. It should not begin modeling or substantive time-series analysis.

## Phase 1 limitations

- No monitoring observation was inspected, so continuity, event counts, missingness,
  plausible ranges, and usable sample sizes remain unknown.
- Operating dates describe metadata coverage, not guaranteed complete observations.
- Spatial relevance is based on site labels and stated depths, not a quantitative
  geotechnical model.
- Compatibility and recommendations are preliminary interpretations. They do not prove
  hydrologic response, causation, or predictive skill.
