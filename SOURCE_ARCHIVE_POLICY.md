# Source archive and fresh-clone policy

The public repository separates numerical reproducibility from preservation of
copyrighted or browser-rendered evidence.

## Fresh-clone build

`make all` retrieves and SHA-256 verifies every raw input used by the numerical
analyses:

- UCI occupancy observations;
- NASA C-MAPSS simulation data;
- Open Power System Data hourly series;
- NASA POWER daily weather data;
- NYC historical traffic counts;
- the publicly downloadable ISO 216 sample used for the narrow geometric null.

These six records are the reproducibility-critical source set. A missing record,
download failure, size mismatch, or checksum mismatch stops the build.

The manuscript's prior-art matrix, selection evidence, requirements summary,
and claim ledger are versioned in Git. Their underlying raw API responses,
government documents, and browser-rendered pages remain registered in
`SOURCE_REGISTRY.csv`, but are not all redistributed. This avoids republishing
copyrighted TFSC and ISO material and avoids placing large evidence archives in
Git.

## Audit modes

- `make audit` validates all locally available snapshots and requires the six
  reproducibility-critical inputs. Missing evidence-only snapshots are reported
  as an explicit archive gap, not silently treated as present.
- `make audit-full-source-archive` requires every registered raw snapshot and is
  intended for the preserved author-side archive used for submission-time
  integrity checks.

The full author-side archive must retain each registered path, file size, and
SHA-256 value. A fresh clone can regenerate the numerical results and
submission package without that copyrighted evidence archive, but cannot claim
to possess or revalidate files that are not legally redistributed.
