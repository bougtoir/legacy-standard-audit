# Phase 0 handoff

## Completed

- Created the project structure and one-command Makefile contract.
- Established canonical source, candidate, claim, and manuscript-value records.
- Defined data and integrity rules.
- Pre-specified the case-selection logic without selecting on outcomes.
- Recorded initial methodological decisions.

## Files changed

See the project root governance files, `README.md`, `Makefile`, and
`requirements.lock`.

## Reproduction commands

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
make all
make test
make audit
```

Pipeline scripts are intentionally incomplete at this handoff and will be
implemented after requirements, prior-art, candidate, and case-selection work.

## Unresolved issues

- Current TFSC requirements have not yet been verified.
- Candidate universe and frozen case set do not yet exist.
- No empirical conclusion is available.

## Next phase

Verify official TFSC requirements from current Elsevier/TFSC sources and record
URLs, access dates, implications, submission files, and human-only declarations.

## Integrity warning

This scaffold is not evidence and is not submission-ready. No empirical value
or historical rationale has yet been established.
