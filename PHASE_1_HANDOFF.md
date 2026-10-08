# Phase 1 handoff: TFSC requirements

## Completed

- Verified the current official TFSC Guide for Authors, journal page, scope
  page, and Elsevier generative-AI policy on 2026-09-24.
- Saved immutable local raw captures under
  `data/raw/journal_requirements/`; these are excluded from Git because the
  source pages are copyrighted.
- Recorded source URLs, local paths, file sizes, hashes, access conditions,
  completeness, and terms in `SOURCE_REGISTRY.csv`.
- Created `TFSC_SUBMISSION_REQUIREMENTS.md` as the operational specification
  for the submission package.

## Material requirements for later phases

- Double-anonymized review requires separate title-page and anonymized files.
- Abstract limit is 250 words; 1–7 keywords are required.
- Highlights are mandatory: 3–5 bullets, at most 85 characters each.
- A graphical abstract is encouraged, not mandatory.
- Figures are separate files; tables are editable text; all must be cited in
  first-appearance order.
- Research data follow Option C: deposit and cite/link, or explain why sharing
  is impossible. A data statement is mandatory.
- References use author–year citations and an alphabetical reference list.
- Substantive AI assistance requires disclosure before the reference list.
- Human authors must confirm authorship, affiliations, CRediT, funding,
  competing interests, acknowledgements, permissions, publishing model, and
  the final data/code release.

## Access limitation

Direct command-line retrieval of the ScienceDirect guide returned HTTP 403.
The complete rendered guide was therefore captured from the already-running
browser over its local Chrome DevTools endpoint. A separate Jina retrieval
returned a robot-challenge page and is retained only as a documented failed
capture, not as substantive evidence.

## Next phase

Build the verified TFSC prior-art matrix and identify the narrowest defensible
novel contribution before constructing and freezing the empirical case set.
