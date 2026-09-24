import csv
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CANONICAL = PROJECT / "SOURCE_REGISTRY.csv"
INPUTS = [
    CANONICAL,
    PROJECT / "research_inputs" / "prior_art_sources.csv",
    PROJECT / "research_inputs" / "selection_sources.csv",
    PROJECT / "research_inputs" / "analysis_sources.csv",
]


rows = []
fieldnames = None
for path in INPUTS:
    if not path.exists():
        continue
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if fieldnames is None:
            fieldnames = reader.fieldnames
        elif reader.fieldnames != fieldnames:
            raise ValueError(f"Source registry schema mismatch: {path}")
        rows.extend(reader)

unique = {}
order = []
for row in rows:
    source_id = row["source_id"]
    if source_id not in unique:
        order.append(source_id)
    unique[source_id] = row

with CANONICAL.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(unique[source_id] for source_id in order)

print(f"Wrote {len(unique)} unique source records")
