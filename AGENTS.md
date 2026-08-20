# Repository working rules

- Read `docs/PROJECT_SPEC.md` and the active execution plan before changing the project.
- Work only within the assigned phase, and stop before automatically entering the next
  phase.
- Preserve raw data exactly as obtained; corrections and transformations belong in code
  and derived data layers.
- Never fabricate measurements, numerical results, metadata, citations, or engineering
  findings.
- Use chronological validation for time-series work and prevent future-data leakage in
  preprocessing, feature construction, model selection, and evaluation.
- Put reusable logic in `src/geotech_ts/` and add or update tests for it.
- Inspect generated tables, figures, notebooks, and reports before treating them as
  deliverables.
- Update the specification, active plan, README, or learning notes when project state or
  durable decisions change.
- Clearly distinguish observed data, statistical inference, engineering interpretation,
  and speculation. Correlation or predictive skill alone does not establish causation.
