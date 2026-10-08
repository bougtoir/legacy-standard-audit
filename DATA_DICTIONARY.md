# Data dictionary

## Governance tables

### `SOURCE_REGISTRY.csv`

One row per source snapshot or authoritative record. `sha256`,
`file_size_bytes`, and `raw_path` are mandatory for downloaded raw files.
`completeness` distinguishes complete, partial, paginated-complete, and
unavailable retrievals.

### `candidate_registry.csv`

One row per candidate standard. Screening fields describe evidence and
feasibility before confirmatory outcomes are known. `screening_status` is one of
`unreviewed`, `eligible`, `primary-frozen`, `supplementary`, or `excluded`.

### `MANUSCRIPT_VALUES.csv`

Canonical machine-generated values used by manuscript, table, and figure
builders. `estimate`, `lower`, and `upper` are numeric when applicable;
categorical classifications are stored in `estimate` with blank intervals.

### `CLAIM_EVIDENCE_LEDGER.csv`

One row per material manuscript claim. `claim_type` is `historical`,
`descriptive`, `analytical`, `interpretive`, or `policy`. Each claim points to a
verified citation, raw source, or generated analysis output.

## Case data

### BE03 occupancy-responsive lighting

- Source: `SEL-BE03-UCI-DATA`.
- Unit: nominal one-minute office observation.
- `occupied`: binary reference label from the UCI dataset.
- `fixed_on`: weekday observation between the configured start and end hours.
- `adaptive_on`: occupied observation plus the configured post-occupancy hold.
- Two repeated embedded header rows are removed after failed timestamp and
  occupancy parsing; the raw snapshot is unchanged.
- The adaptive result is an oracle upper bound without measured sensor error,
  lamp power, commissioning, or installation cost.

### WK07 condition-informed maintenance

- Source: `SEL-WK07-NASA-DATA`, FD001 only.
- Unit: simulated engine cycle.
- Training lifetime: maximum cycle per training unit.
- Evaluation lifetime: maximum observed test cycle plus the supplied remaining
  useful life.
- Fixed-age policy minimizes normalized renewal cost on training lifetimes.
- Condition-informed comparator replaces the simulated unit a configured
  number of cycles before failure with perfect remaining-life information.

### UI01 interval-aware electricity pricing

- Source: `SEL-UI01-OPSD-DATA`.
- Unit: Germany-Luxembourg hourly load in MW and day-ahead price in EUR/MWh.
- Only complete 24-hour UTC days with both variables are retained.
- Flexible load is bounded symmetrically around each observed hourly load and
  shifted within a day while daily energy is conserved.
- Prices are held fixed, so the result is a partial-equilibrium procurement
  upper bound rather than a customer-response estimate.

### UI09 weather-adaptive irrigation

- Sources: `SEL-UI09-NASA-POWER` and `SEL-UI09-FAO56`.
- Unit: daily weather and weekly millimetres of reference-crop water.
- Reference evapotranspiration follows the FAO-56 Penman-Monteith equations.
- Weekly net requirement is non-negative evapotranspiration minus precipitation.
- The calendar comparator is the median training-period weekly requirement; the
  adaptive comparator exactly meets the evaluation-week requirement.
- Crop coefficients, soil storage, irrigation efficiency, and yield response
  are not modeled.

### TR01 responsive traffic control sensitivity

- Source: `SEL-TR01-NYC-DATA`.
- Unit: hourly directional traffic count.
- The reproducible selection rule chooses the segment with the largest number
  of paired NB/SB or EB/WB count days, breaking ties by segment identifier.
- A training-period fixed directional share is compared with an hourly
  demand-proportional share using a convex saturation-delay proxy.
- The data do not identify a signalized intersection or deployed timing plan.

### NC01 and NC03 controls

- NC01 uses ISO 668 metadata and reports no numeric regret because fleet,
  conversion, coordination, and alternative-design performance data are absent.
- NC03 uses the ISO 216 halving and similarity principles. For positive aspect
  ratio \(r\), repeated-halving invariance requires \(r=2/r\), hence
  \(r=\sqrt{2}\) and zero loss for that narrow objective.
