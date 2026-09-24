import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests


PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "data" / "raw" / "analysis"
REGISTRY = PROJECT / "research_inputs" / "analysis_sources.csv"
RAW.mkdir(parents=True, exist_ok=True)
REGISTRY.parent.mkdir(exist_ok=True)

SOURCES = [
    {
        "source_id": "AN-NC03-ISO216-SAMPLE",
        "case_id": "NC03",
        "source_type": "standard_sample",
        "title": "ISO 216:2007 sample pages including the halving and similarity principles",
        "publisher_or_custodian": "iTeh Standards sample mirror",
        "url": "https://cdn.standards.iteh.ai/samples/36631/c0883203ea25445c9992bb09343620c5/ISO-216-2007.pdf",
        "identifier": "ISO 216:2007 sample 36631",
        "version_or_date": "2007 standard sample; accessed 2026-09-24",
        "retrieval_conditions": "Public HTTP download of sample pages",
        "filename": "NC03_iso_216_2007_sample_2026-09-24.pdf",
        "license_or_terms": "Copyrighted standard sample retained locally for verification; do not redistribute",
        "notes": "Supports the analytic null-control objective; raw file excluded from Git",
    }
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


existing_rows: dict[str, dict[str, str]] = {}
if REGISTRY.exists():
    with REGISTRY.open(newline="", encoding="utf-8") as handle:
        existing_rows = {row["source_id"]: row for row in csv.DictReader(handle)}

accessed = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
rows = []
for source in SOURCES:
    destination = RAW / source["filename"]
    action = "existing_snapshot_not_overwritten"
    if not destination.exists():
        headers = {"User-Agent": "legacy-standard-audit/1.0 (mailto:bougtoir@gmail.com)"}
        with requests.get(
            source["url"], headers=headers, stream=True, timeout=180
        ) as response:
            response.raise_for_status()
            with destination.open("xb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        action = "downloaded"
    row = {
        key: value for key, value in source.items() if key != "filename"
    }
    row.update(
        {
            "accessed_utc": existing_rows.get(source["source_id"], {}).get(
                "accessed_utc", accessed
            ),
            "raw_path": str(destination.relative_to(PROJECT)),
            "file_size_bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "completeness": "complete_public_sample",
            "notes": existing_rows.get(source["source_id"], {}).get(
                "notes", f"{source['notes']}; {action}"
            ),
        }
    )
    rows.append(row)

fieldnames = [
    "source_id", "case_id", "source_type", "title", "publisher_or_custodian",
    "url", "identifier", "version_or_date", "accessed_utc",
    "retrieval_conditions", "raw_path", "file_size_bytes", "sha256",
    "license_or_terms", "completeness", "notes",
]
with REGISTRY.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} analysis source records")
