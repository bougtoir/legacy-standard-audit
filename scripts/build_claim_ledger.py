import csv
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


def main() -> None:
    now = json.loads(
        (PROJECT / "analysis_config.json").read_text(encoding="utf-8")
    )["generated_utc"]
    transition = json.loads(
        (
            PROJECT
            / "outputs/analysis/transition_evidence_results.json"
        ).read_text(encoding="utf-8")
    )
    level_a_cases = sorted(
        str(gate["case_id"])
        for gate in transition["case_gates"]
        if gate["highest_evidence_level"] == "A"
    )
    level_b_cases = sorted(
        str(gate["case_id"])
        for gate in transition["case_gates"]
        if gate["highest_evidence_level"] == "B"
    )
    source_counts = transition["source_counts"]
    with (PROJECT / "MANUSCRIPT_VALUES.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        values = {row["value_id"]: row for row in csv.DictReader(handle)}
    strongest_count = int(
        float(values["FALS_REMOVE_BOTH_MATERIAL_COUNT"]["estimate"])
    )
    transition_case_claim = (
        "No primary case has Level A case-compatible transition-cost evidence."
        if not level_a_cases
        else "Level A case-compatible transition evidence is available for "
        + ", ".join(level_a_cases)
        + ", but no transition-adjusted estimate is automatically generated."
    )
    transition_gate_claim = (
        f"{', '.join(level_b_cases)} support threshold analysis only, not "
        "transition-adjusted point estimates."
        if not level_a_cases
        else (
            f"Level B cases {', '.join(level_b_cases)} support threshold "
            f"analysis only; Level A cases {', '.join(level_a_cases)} still "
            "require an explicit audited implementation model before a "
            "transition-adjusted point estimate is reported."
        )
    )
    strongest_claim = (
        "Removing both threshold-meeting oracle cases eliminates all material "
        "primary labels."
        if strongest_count == 0
        else "Removing both threshold-meeting oracle cases leaves "
        f"{strongest_count} material primary "
        + ("label." if strongest_count == 1 else "labels.")
    )
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
            "Only native-unit break-even ceilings are identified; no transition-adjusted superiority is estimated.",
        ],
        [
            "C013",
            "Results—transition evidence",
            transition_case_claim,
            "evidence_gate",
            "TRANSITION-EVIDENCE",
            "outputs/analysis/transition_evidence_results.json; outputs/tables/transition_evidence_matrix.csv",
            "verified",
            now,
            (
                f"{source_counts['B']} sources are Level B and "
                f"{source_counts['C']} sources are Level C."
            ),
        ],
        [
            "C014",
            "Results—transition evidence",
            transition_gate_claim,
            "inference",
            "TRANSITION-GATES",
            "outputs/analysis/transition_evidence_results.json",
            "verified",
            now,
            "Thresholds remain in native benchmark units unless compatible valuation evidence exists.",
        ],
        [
            "C015",
            "Results—UI09",
            "The UI09 break-even quantity is an objective-equivalent threshold, not physical water savings.",
            "limitation",
            "UI09-TRANSITION",
            "outputs/analysis/transition_evidence_results.json",
            "verified",
            now,
            "The objective includes a fivefold shortfall penalty and cannot be monetized without agronomic evidence.",
        ],
        [
            "C016",
            "Methods—transition evidence",
            "The OMB 2026 discount rates are retained as sensitivity references but are not applied to unidentified cash flows.",
            "method",
            "TR-CROSS-OMB-A94",
            "SOURCE_REGISTRY.csv; outputs/analysis/transition_evidence_results.json",
            "verified",
            now,
            "Case-compatible useful lives, horizons, and cash-flow streams are absent.",
        ],
        [
            "C017",
            "Abstract and cross-case synthesis",
            strongest_claim,
            "falsification",
            "JOINT-STRONGEST-CASE",
            "MANUSCRIPT_VALUES.csv:FALS_REMOVE_BOTH_MATERIAL_COUNT; outputs/analysis/final_falsification.csv",
            "verified",
            now,
            (
                "The procedural claim survives, but the empirical material-"
                "mismatch claim does not."
                if strongest_count == 0
                else "The empirical material-mismatch claim survives in the "
                "retained cases, although its count is reduced."
            ),
        ],
        [
            "C018",
            "Framework and limitations",
            "The historical optimum is not identified and no incumbent is assumed to equal it.",
            "historical_claim",
            "HISTORICAL-AUDIT",
            "research_inputs/historical_claim_audit.csv; reports/HISTORICAL_CLAIM_AUDIT.md",
            "verified",
            now,
            "Case language is limited to a historically defensible incumbent problem.",
        ],
        [
            "C019",
            "Limitations",
            (
                f"Transition sources comprise {source_counts['A']} Level A, "
                f"{source_counts['B']} Level B, and "
                f"{source_counts['C']} Level C records."
            ),
            "evidence_gate",
            "TRANSITION-LEVEL-COUNTS",
            "MANUSCRIPT_VALUES.csv:TRANSITION_LEVEL_A_SOURCES; MANUSCRIPT_VALUES.csv:TRANSITION_LEVEL_B_SOURCES; MANUSCRIPT_VALUES.csv:TRANSITION_LEVEL_C_SOURCES",
            "verified",
            now,
            "Level B permits thresholds only; Level C supports no case inference.",
        ],
        [
            "C020",
            "Abstract, results, and limitations",
            "No case identifies a realized causal deployment effect.",
            "inference",
            "CASE-LIMITATIONS",
            "outputs/analysis/case_results.json; reports/ORACLE_LANGUAGE_AUDIT.md",
            "verified",
            now,
            "Oracle, partial-equilibrium, and proxy results remain locally qualified.",
        ],
        [
            "C021",
            "Abstract and methods",
            "The design screened 122 candidates in 12 domains and froze seven cases.",
            "design",
            "DESIGN-COUNTS",
            "MANUSCRIPT_VALUES.csv:DESIGN_CANDIDATES; MANUSCRIPT_VALUES.csv:DESIGN_DOMAINS; MANUSCRIPT_VALUES.csv:DESIGN_FROZEN_CASES",
            "verified",
            now,
            "Counts are generated from the candidate registry and frozen-case file.",
        ],
        [
            "C022",
            "Introduction",
            "The protocol differs from periodic standards review and lifecycle-analysis frameworks by linking capability change to a frozen static benchmark and separate redesign gate.",
            "positioning",
            "FRAMEWORK-ANTECEDENTS",
            "research_inputs/framework_sources.csv; SOURCE_REGISTRY.csv",
            "verified",
            now,
            "Official ISO systematic-review guidance and the exact-DOI NIST FACTS record are persisted.",
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
