import csv
import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
CANDIDATES = PROJECT / "candidate_registry.csv"
EVIDENCE = PROJECT / "case_selection_evidence.csv"
PROTOCOL = PROJECT / "case_selection_protocol.md"
SOURCES = PROJECT / "research_inputs" / "selection_sources.csv"
OUTPUT = PROJECT / "frozen_case_set.json"
SIDECAR = PROJECT / "frozen_case_set.sha256"
FREEZE_UTC = "2026-09-24T09:55:00Z"
SCORE_FIELDS = [
    "historical_evidence_score",
    "technology_relevance_score",
    "decision_clarity_score",
    "current_data_score",
    "identifiability_score",
    "counterfactual_feasibility_score",
    "transition_cost_feasibility_score",
    "source_quality_score",
    "comparability_score",
]


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protocol_prespecification_hash():
    prespecified = PROTOCOL.read_text(encoding="utf-8").split("## Frozen set", 1)[0]
    return hashlib.sha256(prespecified.encode("utf-8")).hexdigest()


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


candidate_rows = load_csv(CANDIDATES)
evidence_rows = load_csv(EVIDENCE)
source_rows = load_csv(SOURCES)
candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
evidence_by_id = {row["candidate_id"]: row for row in evidence_rows}
source_ids_by_case = {}
for row in source_rows:
    source_ids_by_case.setdefault(row["case_id"], []).append(row["source_id"])

if len(candidate_by_id) != len(candidate_rows):
    raise ValueError("candidate_registry.csv contains duplicate candidate IDs")
if len({row["candidate_id"] for row in evidence_rows}) != len(evidence_rows):
    raise ValueError("case_selection_evidence.csv contains duplicate candidate IDs")

for candidate in candidate_rows:
    evidence = evidence_by_id.get(candidate["candidate_id"])
    if not evidence:
        continue
    for field in SCORE_FIELDS:
        candidate[field] = evidence[field]
    candidate["total_score"] = str(sum(int(evidence[field]) for field in SCORE_FIELDS))
    candidate["exclusion_flag"] = evidence["exclusion_flag"]
    candidate["verification_status"] = "selection_sources_persisted_and_checked"
    candidate["screening_status"] = f"frozen_{evidence['role']}"
    candidate["screening_reason"] = evidence["selection_rationale"]

with CANDIDATES.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=candidate_rows[0].keys(), lineterminator="\n")
    writer.writeheader()
    writer.writerows(candidate_rows)

frozen_cases = []
for evidence in evidence_rows:
    candidate_id = evidence["candidate_id"]
    if candidate_id not in candidate_by_id:
        raise ValueError(f"Unknown candidate ID: {candidate_id}")
    scores = {field: int(evidence[field]) for field in SCORE_FIELDS}
    if any(score < 0 or score > 3 for score in scores.values()):
        raise ValueError(f"Score outside 0-3 range for {candidate_id}")
    sources = sorted(source_ids_by_case.get(candidate_id, []))
    if not sources:
        raise ValueError(f"No persisted selection source for {candidate_id}")
    frozen_cases.append(
        {
            "candidate_id": candidate_id,
            "candidate_name": candidate_by_id[candidate_id]["candidate_name"],
            "domain": candidate_by_id[candidate_id]["domain"],
            "role": evidence["role"],
            "scores": scores,
            "total_score": sum(scores.values()),
            "exclusion_flag": evidence["exclusion_flag"] or None,
            "selection_rationale": evidence["selection_rationale"],
            "preconfirmatory_limit": evidence["preconfirmatory_limit"],
            "selection_source_ids": sources,
        }
    )

payload = {
    "freeze_version": "1.0",
    "freeze_utc": FREEZE_UTC,
    "selection_rule": (
        "Evidence and design quality only; no confirmatory effect direction, "
        "magnitude, or statistical significance was inspected."
    ),
    "roles": {
        "primary": [row["candidate_id"] for row in frozen_cases if row["role"] == "primary"],
        "supplementary": [
            row["candidate_id"] for row in frozen_cases if row["role"] == "supplementary"
        ],
        "network_control": [
            row["candidate_id"] for row in frozen_cases if row["role"] == "network_control"
        ],
        "null_control": [
            row["candidate_id"] for row in frozen_cases if row["role"] == "null_control"
        ],
    },
    "input_hashes": {
        "candidate_registry.csv": file_hash(CANDIDATES),
        "case_selection_evidence.csv": file_hash(EVIDENCE),
        "case_selection_protocol.md_prespecified_section": protocol_prespecification_hash(),
        "research_inputs/selection_sources.csv": file_hash(SOURCES),
    },
    "source_record_count": len(source_rows),
    "frozen_cases": frozen_cases,
}
rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

if OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") != rendered:
    raise RuntimeError(
        "Frozen case set already exists with different content; record a protocol deviation"
    )
OUTPUT.write_text(rendered, encoding="utf-8")
SIDECAR.write_text(f"{file_hash(OUTPUT)}  {OUTPUT.name}\n", encoding="utf-8")

print(f"Frozen {len(frozen_cases)} cases at {FREEZE_UTC}")
print(f"SHA-256 {file_hash(OUTPUT)}")
