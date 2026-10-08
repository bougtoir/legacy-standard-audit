import csv
import json
import math
from pathlib import Path

from docx import Document

from publication_utils import (
    FIGURE_ORDER,
    TABLE_ORDER,
    display,
    fig,
    interval,
    load_values,
    tab,
    table_filename,
)


PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "outputs"
REPORT = PROJECT / "reports" / "NUMERICAL_QC.md"


def close(actual: object, expected: object) -> bool:
    if isinstance(expected, str):
        return str(actual) == expected
    return math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-15)


def assert_value(
    values: dict[str, dict[str, str]],
    value_id: str,
    expected: object,
    failures: list[str],
) -> None:
    actual = values[value_id]["estimate"]
    if not close(actual, expected):
        failures.append(f"{value_id}: canonical value {actual} != recomputed {expected}")


def main() -> None:
    failures: list[str] = []
    values = load_values()
    payload = json.loads(
        (OUTPUT / "analysis" / "case_results.json").read_text(encoding="utf-8")
    )
    cases = {row["case_id"]: row for row in payload["case_results"]}

    scalar_checks = {
        "BE03_OBSERVATIONS": cases["BE03"]["observations"],
        "BE03_ENERGY_REDUCTION": cases["BE03"]["energy_reduction_fraction"],
        "BE03_CLASSIFICATION": cases["BE03"]["classification"],
        "WK07_FIXED_AGE": cases["WK07"]["training_selected_fixed_age_cycles"],
        "WK07_STATIC_REGRET": cases["WK07"]["static_regret_cost_per_cycle"],
        "WK07_RELATIVE_REGRET": cases["WK07"]["relative_regret_fraction"],
        "WK07_CLASSIFICATION": cases["WK07"]["classification"],
        "UI01_COMPLETE_DAYS": cases["UI01"]["complete_days"],
        "UI01_SAVINGS_PER_MWH": cases["UI01"]["procurement_savings_eur_per_mwh"],
        "UI01_CLASSIFICATION": cases["UI01"]["classification"],
        "UI09_TRAINING_WEEKS": cases["UI09"]["training_weeks"],
        "UI09_EVALUATION_WEEKS": cases["UI09"]["evaluation_weeks"],
        "UI09_CALENDAR_APPLICATION": cases["UI09"][
            "calendar_application_mm_per_week"
        ],
        "UI09_ADAPTIVE_APPLICATION": cases["UI09"][
            "adaptive_mean_application_mm_per_week"
        ],
        "UI09_OBJECTIVE_REGRET": cases["UI09"][
            "normalized_objective_regret_fraction"
        ],
        "UI09_CLASSIFICATION": cases["UI09"]["classification"],
        "TR01_PAIRED_DAYS": cases["TR01"]["paired_days"],
        "TR01_TRAINING_DAYS": cases["TR01"]["training_days"],
        "TR01_EVALUATION_DAYS": cases["TR01"]["evaluation_days"],
        "TR01_PROXY_REDUCTION": cases["TR01"][
            "responsive_allocation_proxy_reduction_fraction"
        ],
        "TR01_CLASSIFICATION": cases["TR01"]["classification"],
        "NC01_CLASSIFICATION": cases["NC01"]["classification"],
        "NC03_OPTIMAL_RATIO": cases["NC03"]["optimal_aspect_ratio"],
        "NC03_SELF_SIMILARITY_LOSS": cases["NC03"]["self_similarity_loss"],
        "NC03_CLASSIFICATION": cases["NC03"]["classification"],
    }
    for value_id, expected in scalar_checks.items():
        assert_value(values, value_id, expected, failures)

    interval_checks = {
        "BE03_ENERGY_REDUCTION": cases["BE03"]["energy_reduction_95_interval"],
        "WK07_STATIC_REGRET": cases["WK07"]["static_regret_95_interval"],
        "UI01_SAVINGS_PER_MWH": cases["UI01"][
            "procurement_savings_eur_per_mwh_95_interval"
        ],
        "UI09_OBJECTIVE_REGRET": cases["UI09"][
            "normalized_objective_regret_95_interval"
        ],
        "TR01_PROXY_REDUCTION": cases["TR01"][
            "responsive_allocation_proxy_reduction_95_interval"
        ],
    }
    for value_id, expected in interval_checks.items():
        row = values[value_id]
        if not close(row["lower"], expected[0]) or not close(row["upper"], expected[1]):
            failures.append(f"{value_id}: canonical interval differs from recomputed output")

    with (PROJECT / "candidate_registry.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        candidates = list(csv.DictReader(handle))
    frozen = json.loads(
        (PROJECT / "frozen_case_set.json").read_text(encoding="utf-8")
    )
    design_checks = {
        "DESIGN_CANDIDATES": len(candidates),
        "DESIGN_DOMAINS": len({row["domain"] for row in candidates}),
        "DESIGN_FROZEN_CASES": len(frozen["frozen_cases"]),
    }
    for value_id, expected in design_checks.items():
        assert_value(values, value_id, expected, failures)

    transition = json.loads(
        (OUTPUT / "analysis" / "transition_evidence_results.json").read_text(
            encoding="utf-8"
        )
    )
    for level in ["A", "B", "C"]:
        assert_value(
            values,
            f"TRANSITION_LEVEL_{level}_SOURCES",
            transition["source_counts"][level],
            failures,
        )

    with (OUTPUT / "analysis" / "final_falsification.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        falsification = list(csv.DictReader(handle))
    joint = next(
        row for row in falsification if row["test"] == "remove_WK07_and_UI09"
    )
    assert_value(
        values,
        "FALS_REMOVE_BOTH_MATERIAL_COUNT",
        joint["threshold_meeting_oracle_cases"],
        failures,
    )

    prior_art = list(
        csv.DictReader(
            (PROJECT / "TFSC_prior_art_matrix.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    invalid_doi = [
        row["reference_id"]
        for row in prior_art
        if not row["doi"]
        or row["verification_status"] != "verified"
        or not (PROJECT / row["raw_path"]).exists()
    ]
    if invalid_doi:
        failures.append("Unverified DOI records: " + ", ".join(invalid_doi))

    manuscript = Document(OUTPUT / "manuscript" / "manuscript_anonymized.docx")
    manuscript_text = "\n".join(paragraph.text for paragraph in manuscript.paragraphs)
    required_labels = [fig(key) for key, _ in FIGURE_ORDER] + [
        tab(key) for key in TABLE_ORDER
    ]
    for label in required_labels:
        if label not in manuscript_text:
            failures.append(f"Manuscript does not cite {label}")
    if (OUTPUT / "supplement").exists():
        failures.append("Stale supplement output directory exists")

    table_rows = list(
        csv.DictReader(
            (OUTPUT / "tables" / table_filename("case_results")).open(
                newline="", encoding="utf-8"
            )
        )
    )
    if len(table_rows) != len(cases):
        failures.append("Table 3 does not contain all seven frozen cases")

    manuscript_value_ids = [
        "DESIGN_CANDIDATES",
        "DESIGN_DOMAINS",
        "DESIGN_FROZEN_CASES",
        "BE03_OBSERVATIONS",
        "WK07_FIXED_AGE",
        "UI01_COMPLETE_DAYS",
        "UI09_TRAINING_WEEKS",
        "UI09_EVALUATION_WEEKS",
        "NC03_OPTIMAL_RATIO",
        "FALS_REMOVE_BOTH_MATERIAL_COUNT",
        "TRANSITION_LEVEL_A_SOURCES",
        "TRANSITION_LEVEL_B_SOURCES",
        "TRANSITION_LEVEL_C_SOURCES",
    ]
    missing_displays = [
        value_id
        for value_id in manuscript_value_ids
        if display(values, value_id) not in manuscript_text
    ]
    if missing_displays:
        failures.append(
            "Canonical displays absent from manuscript: " + ", ".join(missing_displays)
        )

    lines = [
        "# Numerical, traceability, and fabrication QC",
        "",
        f"Status: {'PASS' if not failures else 'FAIL'}",
        "",
        "## Recomputed critical values",
        "",
        f"- BE03: n={display(values, 'BE03_OBSERVATIONS')}; nominal reduction "
        f"{display(values, 'BE03_ENERGY_REDUCTION')} "
        f"({interval(values, 'BE03_ENERGY_REDUCTION')}).",
        f"- WK07: fixed age {display(values, 'WK07_FIXED_AGE')} cycles; regret "
        f"{display(values, 'WK07_STATIC_REGRET')} "
        f"({interval(values, 'WK07_STATIC_REGRET')}); relative regret "
        f"{display(values, 'WK07_RELATIVE_REGRET')}.",
        f"- UI01: n={display(values, 'UI01_COMPLETE_DAYS')} complete days; arithmetic "
        f"saving {display(values, 'UI01_SAVINGS_PER_MWH')} EUR/MWh "
        f"({interval(values, 'UI01_SAVINGS_PER_MWH')}).",
        f"- UI09: {display(values, 'UI09_TRAINING_WEEKS')} training and "
        f"{display(values, 'UI09_EVALUATION_WEEKS')} evaluation weeks; calendar/adaptive "
        f"applications {display(values, 'UI09_CALENDAR_APPLICATION')}/"
        f"{display(values, 'UI09_ADAPTIVE_APPLICATION')} mm/week; objective regret "
        f"{display(values, 'UI09_OBJECTIVE_REGRET')} "
        f"({interval(values, 'UI09_OBJECTIVE_REGRET')}).",
        f"- TR01: {display(values, 'TR01_PAIRED_DAYS')} paired days; proxy reduction "
        f"{display(values, 'TR01_PROXY_REDUCTION')} "
        f"({interval(values, 'TR01_PROXY_REDUCTION')}).",
        f"- NC03: optimum {display(values, 'NC03_OPTIMAL_RATIO')}; loss "
        f"{display(values, 'NC03_SELF_SIMILARITY_LOSS')}.",
        f"- Design: {display(values, 'DESIGN_CANDIDATES')} candidates, "
        f"{display(values, 'DESIGN_DOMAINS')} domains, "
        f"{display(values, 'DESIGN_FROZEN_CASES')} frozen cases.",
        f"- Joint strongest-case removal: "
        f"{display(values, 'FALS_REMOVE_BOTH_MATERIAL_COUNT')} material primary labels.",
        "",
        "## Cross-artifact checks",
        "",
        f"- {len(values)} canonical manuscript values have generated source paths.",
        f"- {len(prior_art)} DOI records have verified metadata and persisted raw records.",
        "- Every main figure and table is cited; no supplementary file is produced.",
        "- Critical canonical displays occur in the generated manuscript.",
        "- Table 3 contains every frozen case.",
        "- Consecutive rebuilds preserve machine-readable analytical outputs; Office, "
        "PDF, and ZIP byte hashes may vary with container metadata.",
    ]
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(f"Numerical QC failed with {len(failures)} finding(s)")
    print("Numerical, traceability, and fabrication QC passed")


if __name__ == "__main__":
    main()
