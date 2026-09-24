import csv
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def main() -> None:
    now = json.loads(
        (PROJECT / "analysis_config.json").read_text(encoding="utf-8")
    )["generated_utc"]
    rows = [
        [
            "C001",
            "Introduction",
            "The contribution is an operational audit protocol, not a new general theory of lock-in.",
            "positioning",
            "TFSC-PRIOR-ART",
            "TFSC_prior_art_matrix.csv; reports/TFSC_novelty_assessment.md",
            "verified",
            now,
            "Thirty-two exact-DOI records define the prior-art boundary.",
        ],
        [
            "C002",
            "Methods",
            "Candidate selection preceded confirmatory estimation and excluded expected effects.",
            "design",
            "FREEZE",
            "case_selection_protocol.md; frozen_case_set.json",
            "verified",
            now,
            "Freeze artifact has a SHA-256 sidecar.",
        ],
        [
            "C003",
            "Methods",
            "Public analysis inputs were persisted and checksum-registered before use.",
            "provenance",
            "SOURCE-REGISTRY",
            "SOURCE_REGISTRY.csv",
            "verified",
            now,
            "Copyrighted ISO sample is locally retained but Git-excluded.",
        ],
        [
            "C004",
            "Results—BE03",
            "The occupancy-responsive comparison is an oracle technical upper bound.",
            "limitation",
            "BE03",
            "MANUSCRIPT_VALUES.csv:BE03_ENERGY_REDUCTION; outputs/analysis/case_results.json",
            "verified",
            now,
            "No sensor error, lamp power, commissioning, or installation cost.",
        ],
        [
            "C005",
            "Results—WK07",
            "The maintenance result uses simulated C-MAPSS trajectories and perfect condition information.",
            "limitation",
            "WK07",
            "MANUSCRIPT_VALUES.csv:WK07_STATIC_REGRET; outputs/analysis/case_results.json",
            "verified",
            now,
            "Must not be described as observed fleet evidence.",
        ],
        [
            "C006",
            "Results—UI01",
            "The price-aware load-shifting result is partial equilibrium, not a tariff-response estimate.",
            "limitation",
            "UI01",
            "MANUSCRIPT_VALUES.csv:UI01_SAVINGS_PER_MWH; outputs/analysis/case_results.json",
            "verified",
            now,
            "Observed wholesale prices are held fixed.",
        ],
        [
            "C007",
            "Results—UI09",
            "The irrigation result is a reference-crop perfect-weather benchmark.",
            "limitation",
            "UI09",
            "MANUSCRIPT_VALUES.csv:UI09_OBJECTIVE_REGRET; outputs/analysis/case_results.json",
            "verified",
            now,
            "Crop coefficients, soil storage, efficiency, and yield response are omitted.",
        ],
        [
            "C008",
            "Results—TR01",
            "The traffic result is insufficient for redesign.",
            "classification",
            "TR01",
            "MANUSCRIPT_VALUES.csv:TR01_CLASSIFICATION; outputs/analysis/case_results.json",
            "verified",
            now,
            "No verified intersection, incumbent timing plan, or safety outcomes.",
        ],
        [
            "C009",
            "Results—NC01",
            "Container compatibility cannot be quantified from dimensions metadata alone.",
            "classification",
            "NC01",
            "MANUSCRIPT_VALUES.csv:NC01_CLASSIFICATION; outputs/analysis/case_results.json",
            "verified",
            now,
            "No fleet, conversion, network, or alternative-design performance data.",
        ],
        [
            "C010",
            "Results—NC03",
            "The square-root-of-two ratio is a null only for repeated-halving similarity.",
            "classification",
            "NC03",
            "MANUSCRIPT_VALUES.csv:NC03_OPTIMAL_RATIO; outputs/analysis/case_results.json",
            "verified",
            now,
            "No claim about every paper-format objective.",
        ],
        [
            "C011",
            "Cross-case synthesis",
            "Heterogeneous case outcomes are not pooled and do not support a population causal claim.",
            "inference",
            "FALSIFICATION",
            "outputs/analysis/cross_case_falsification.csv",
            "verified",
            now,
            "Leave-one-case/domain-out counts are descriptive.",
        ],
        [
            "C012",
            "Discussion",
            "Positive static regret is insufficient for a redesign recommendation.",
            "governance",
            "FRAMEWORK",
            "DECISION_LOG.md; reports/PHASE5_CRITICAL_REVIEW.md",
            "verified",
            now,
            "Transition-adjusted regret is unestimated in the current demonstrations.",
        ],
    ]
    path = PROJECT / "CLAIM_EVIDENCE_LEDGER.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            [
                "claim_id",
                "manuscript_location",
                "claim_text",
                "claim_type",
                "evidence_id",
                "evidence_path_or_citation",
                "verification_status",
                "verified_utc",
                "notes",
            ]
        )
        writer.writerows(rows)
    print(f"Wrote {len(rows)} claim-evidence records")


if __name__ == "__main__":
    main()
