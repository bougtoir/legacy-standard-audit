# Phase 5 handoff: case analyses and falsification

## Completed

- Added deterministic analysis configuration and reusable numerical methods.
- Verified the five analysis datasets against the registered sizes and
  SHA-256 checksums before use.
- Removed the two embedded UCI header rows in preprocessing without modifying
  the raw snapshot.
- Implemented all seven frozen roles without replacement:
  - BE03: fixed office schedule versus an oracle occupancy-responsive policy;
  - WK07: fixed-age versus perfect-information condition maintenance;
  - UI01: observed load procurement versus bounded price-aware intraday load
    shifting at fixed wholesale prices;
  - UI09: calendar versus perfect-weather weekly irrigation;
  - TR01: supplementary directional-allocation sensitivity;
  - NC01: unquantified high-network-cost control;
  - NC03: repeated-halving analytic null.
- Generated `MANUSCRIPT_VALUES.csv` from the analysis output.
- Added case-specific model sensitivity, leave-one-case/domain-out,
  source-quality, and negative-control checks.
- Used circular block bootstrap intervals for temporally ordered daily and
  weekly cases, while retaining the simulated engine as the WK07 sampling unit.
- Confirmed deterministic regeneration of all analysis outputs and canonical
  manuscript values.

## Confirmatory classifications

| Case | Frozen role | Classification |
|---|---|---|
| BE03 | Primary | Small or uncertain mismatch |
| WK07 | Primary | Material mismatch under an oracle benchmark |
| UI01 | Primary | Small or uncertain mismatch |
| UI09 | Primary | Material mismatch under an oracle benchmark |
| TR01 | Supplementary | Insufficient evidence |
| NC01 | Network control | Insufficient evidence |
| NC03 | Analytic null | No mismatch for the repeated-halving objective |

These labels are generated from the frozen analyses. They do not imply realized
causal effects or practical redesign recommendations.

## Integrity limits

- Oracle policies are technical upper bounds, not deployment estimates.
- C-MAPSS remains simulated evidence.
- Observed electricity prices are not re-equilibrated after shifting load.
- The irrigation analysis omits crop, soil, efficiency, and yield-response
  parameters.
- The traffic analysis lacks verified geometry, timing plans, pedestrian
  constraints, saturation flows, queues, and safety outcomes.
- NC01 remains unquantified rather than receiving invented network-cost inputs.
- Cross-case magnitudes are not pooled because their objectives and units are
  incomparable.

## Verification

```bash
python3 scripts/fetch_data.py
python3 scripts/fetch_analysis_sources.py
python3 scripts/merge_source_registry.py
python3 scripts/run_analysis.py
python3 -m pytest tests/test_analysis_methods.py -q
```

The unit tests pass, Python sources compile, and a second analysis run reproduces
the same SHA-256 hashes for all generated analysis files and
`MANUSCRIPT_VALUES.csv`.

## Next phase

Phase 6 manuscript, submission-asset, and audit work is documented in
`PHASE_6_HANDOFF.md`.
