import csv
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests


PROJECT = Path(__file__).resolve().parents[1]
REGISTRY = PROJECT / "research_inputs" / "selection_sources.csv"
ARCHIVE_PATH = (
    PROJECT
    / "data/raw/analysis/legacy_standard_audit_analysis_inputs_v1.zip"
)
ARCHIVE_URL = (
    "https://github.com/bougtoir/legacy-standard-audit/releases/download/"
    "analysis-inputs-v1/legacy_standard_audit_analysis_inputs_v1.zip"
)
ARCHIVE_SHA256 = "f448854e6117b93c495e71b1ba5ec45c557a4d11b2d1a5c590300bc3f2fe7f3a"
REQUIRED_SOURCE_IDS = {
    "SEL-BE03-UCI-DATA",
    "SEL-WK07-NASA-DATA",
    "SEL-UI01-OPSD-DATA",
    "SEL-UI09-NASA-POWER",
    "SEL-TR01-NYC-DATA",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(row: dict[str, str], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "legacy-standard-audit/1.0 (mailto:bougtoir@gmail.com)"}
    with requests.get(row["url"], headers=headers, stream=True, timeout=300) as response:
        response.raise_for_status()
        with destination.open("xb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)


def restore_from_archive(rows: dict[str, dict[str, str]]) -> None:
    missing = [
        source_id
        for source_id, row in rows.items()
        if not (PROJECT / row["raw_path"]).exists()
    ]
    if not missing:
        return
    if not ARCHIVE_PATH.exists():
        download({"url": ARCHIVE_URL}, ARCHIVE_PATH)
    archive_hash = sha256(ARCHIVE_PATH)
    if archive_hash != ARCHIVE_SHA256:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        preserved = ARCHIVE_PATH.with_name(
            f"{ARCHIVE_PATH.stem}_{timestamp}_{archive_hash[:8]}{ARCHIVE_PATH.suffix}"
        )
        ARCHIVE_PATH.rename(preserved)
        raise RuntimeError(
            f"Analysis-input archive checksum mismatch; preserved at {preserved}"
        )
    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        members = set(archive.namelist())
        for source_id in missing:
            row = rows[source_id]
            destination = PROJECT / row["raw_path"]
            member = destination.name
            if member not in members:
                raise RuntimeError(f"{source_id} is absent from {ARCHIVE_PATH.name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, destination.open("xb") as target:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    target.write(chunk)


with REGISTRY.open(newline="", encoding="utf-8") as handle:
    rows = {
        row["source_id"]: row
        for row in csv.DictReader(handle)
        if row["source_id"] in REQUIRED_SOURCE_IDS
    }

missing_records = REQUIRED_SOURCE_IDS - rows.keys()
if missing_records:
    raise RuntimeError(f"Missing source records: {sorted(missing_records)}")

restore_from_archive(rows)

for source_id in sorted(REQUIRED_SOURCE_IDS):
    row = rows[source_id]
    destination = PROJECT / row["raw_path"]
    actual_hash = sha256(destination)
    if actual_hash != row["sha256"]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        preserved = destination.with_name(
            f"{destination.stem}_{timestamp}_{actual_hash[:8]}{destination.suffix}"
        )
        destination.rename(preserved)
        raise RuntimeError(
            f"{source_id} changed upstream; preserved new snapshot at {preserved}"
        )
    if destination.stat().st_size != int(row["file_size_bytes"]):
        raise RuntimeError(f"Size mismatch for {source_id}")
    print(f"{source_id}: verified {destination}")
