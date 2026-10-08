# Phase R13 Handoff

## Journal-facing package

`outputs/submission/TFSC_submission_package_FINAL.zip` contains only submission-facing files:

- anonymized inline manuscript DOCX and reference PDF;
- non-anonymized title-page template;
- separate main and supplementary figures plus editable figure PPTX;
- editable table DOCX/PPTX;
- supplement DOCX/PDF;
- highlights;
- cover letter DOCX/PDF;
- graphical abstract PNG/editable PPTX;
- data-availability and declaration statements;
- checksum manifest.

## Internal reproducibility package

Internal materials remain in the repository and are excluded from the journal-facing ZIP:

- source registry and frozen protocol;
- code/data instructions and immutable-input metadata;
- `MANUSCRIPT_VALUES.csv` and claim ledger;
- novelty, transition, oracle-language, historical-claim, numerical, integrity, and
  reproducibility audits;
- hostile review and editor rereview;
- final compliance checklist and author-action file.

## Validation

- Canonical `make all` passes.
- Numerical, integrity, reproducibility, oracle-language, and TFSC compliance audits pass.
- The submission archive contains the expected journal-facing files and no internal audit files.
- Author-only placeholders remain visibly blocked by `AUTHOR_ACTION_REQUIRED.md`; they must be
  completed before actual submission.
