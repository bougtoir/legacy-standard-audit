# Legacy Standard Audit

Reproducible research pipeline for evaluating whether persistent standards are
best understood as frozen solutions to optimization problems whose technological
constraints have changed.

The project is designed for a *Technological Forecasting and Social Change*
submission. It does not presume that old standards are inefficient. Each case
must distinguish frictionless static regret from transition-adjusted welfare,
retain null findings, and trace every empirical value to public source data.

## Reproduce

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
make all
make test
make audit
```

`make all` retrieves or validates permitted public inputs, rebuilds processed
data, analyses, figures, tables, manuscript files, and the submission package.
No manuscript result should require manual transcription.

A fresh clone requires and checksum-validates the six raw inputs used by the
numerical analyses. Evidence-only snapshots that cannot be redistributed are
governed by `SOURCE_ARCHIVE_POLICY.md`. Authors with the preserved local archive
can run `make audit-full-source-archive` to require all registered snapshots.

## Canonical records

- `SOURCE_REGISTRY.csv`: source provenance and immutable raw-file checksums.
- `SOURCE_ARCHIVE_POLICY.md`: fresh-clone and full-archive verification rules.
- `candidate_registry.csv`: full candidate universe and screening fields.
- `case_selection_protocol.md`: pre-specified selection and frozen cases.
- `MANUSCRIPT_VALUES.csv`: canonical generated numerical and categorical values.
- `CLAIM_EVIDENCE_LEDGER.csv`: claims linked to sources or generated outputs.
- `DECISION_LOG.md`: methodological decisions, deviations, and rationale.

## Integrity constraints

1. Raw public data are stored under `data/raw/`; new snapshots never overwrite
   prior snapshots.
2. Historical dates and rationales require primary or authoritative records.
3. Positive static regret is not sufficient evidence for practical redesign.
4. Synthetic data, if used for method illustration, are explicitly labelled and
   never represented as observations.
5. The case-selection protocol is frozen before confirmatory analyses.
6. Values in prose, tables, and figures are generated from
   `MANUSCRIPT_VALUES.csv`.

## Status

Phases 0–6 are complete. The 122-case universe and seven-case preconfirmatory
freeze are documented in `PHASE_3_HANDOFF.md`, `PHASE_4_HANDOFF.md`, and
`frozen_case_set.json`; generated case classifications and sensitivity tests are
documented in `PHASE_5_HANDOFF.md`. The manuscript, supplement, separate and
editable figures and tables, graphical abstract, cover letter, audit reports,
and TFSC submission archive are documented in `PHASE_6_HANDOFF.md` and generated
under `outputs/`.

The package is scientifically and mechanically audited. Submission still
requires author names, affiliations, corresponding-author details, funding and
competing-interest confirmation, and a stable public archival URL or DOI.
