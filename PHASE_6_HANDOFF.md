# Phase 6 handoff: manuscript and TFSC submission package

## Completed

- Generated a single-column anonymized Word manuscript and PDF.
- Generated a separate editable title page with explicit author placeholders.
- Generated separate high-resolution figures and editable English PPTX source.
- Generated editable CSV, DOCX, and PPTX tables.
- Generated supplementary DOCX and PDF material.
- Generated five TFSC highlights, a data-availability statement, declarations,
  a cover letter, and a 1328 × 531 graphical abstract with editable PPTX source.
- Generated a checksummed TFSC submission ZIP.
- Populated the claim-evidence ledger from the frozen analysis and canonical
  manuscript values.
- Added explicit operational classification thresholds to the analysis
  configuration and manuscript.
- Completed editor, adversarial reviewer, integrity, reproducibility, and TFSC
  compliance audits.

## Verification

```bash
make all
make test
ruff check scripts tests
git diff --check
```

Observed results:

- all 58 registered source snapshots passed size and SHA-256 validation;
- all 74 canonical manuscript values had unique identifiers and extant source
  outputs;
- all 12 claim-ledger records were verified;
- the abstract contained 181 words;
- seven keywords were present;
- five highlights were each below 85 characters;
- the graphical abstract was exactly 1328 × 531 pixels;
- all six unit tests passed;
- deterministic analysis regeneration reproduced the same hashes for the case
  results, summaries, falsification outputs, sensitivity outputs, and
  `MANUSCRIPT_VALUES.csv`.

## Scientific disposition

The package does not claim that legacy standards are generally obsolete.
Historical optima remain incomplete for several demonstrations, transition-
adjusted regret is not numerically estimated, oracle comparators are not
deployable interventions, and the purposive heterogeneous cases do not support
population inference. These constraints are stated in the abstract, methods,
discussion, limitations, conclusion, editor audit, and claim-evidence ledger.

## Submission-time actions

- Supply author names, order, affiliations, and corresponding-author details.
- Complete the cover-letter date and signature.
- Confirm funding, competing interests, and author contributions.
- Replace the provisional repository statement with a stable public archive URL
  or DOI.
- Perform the submitting authors' final source, number, and interpretation
  verification.
