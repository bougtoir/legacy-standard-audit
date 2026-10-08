import csv
import json
from collections import defaultdict
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ANALYSIS = PROJECT / "outputs" / "analysis"
OUTPUT_PATH = ANALYSIS / "final_falsification.csv"
VALUES_PATH = PROJECT / "MANUSCRIPT_VALUES.csv"
PRIMARY_CASES = frozenset({"BE03", "WK07", "UI01", "UI09"})
STRONGEST_ORACLE_CASES = frozenset({"WK07", "UI09"})


def classification_count(
    case_results: dict[str, dict[str, object]],
    retained: set[str],
) -> int:
    return sum(
        str(case_results[case_id]["classification"]).startswith(
            "material_mismatch"
        )
        for case_id in retained
    )


def strongest_case_removal_count(
    case_results: dict[str, dict[str, object]],
) -> int:
    return classification_count(
        case_results,
        set(PRIMARY_CASES - STRONGEST_ORACLE_CASES),
    )


def strongest_case_removal_assessment(
    retained_count: int,
    retained_total: int,
    baseline_count: int,
) -> tuple[str, str]:
    if retained_count == 0:
        return (
            "Yes—empirical material-mismatch claim",
            "The procedural and heterogeneous-outcome claims survive; evidence "
            "of material primary mismatch does not.",
        )
    weakened = (
        "Yes—material-count claim"
        if retained_count < baseline_count
        else "No"
    )
    return (
        weakened,
        f"The procedural and heterogeneous-outcome claims survive; "
        f"{retained_count} of {retained_total} retained primary cases still "
        "meet the material-mismatch label.",
    )


def threshold_count(
    case_results: dict[str, dict[str, object]],
    be03_threshold: float,
    wk07_threshold: float,
    ui09_threshold: float,
) -> int:
    be03 = case_results["BE03"]
    wk07 = case_results["WK07"]
    ui09 = case_results["UI09"]
    return sum(
        [
            float(be03["energy_reduction_95_interval"][0]) > be03_threshold
            and int(be03["adaptive_occupied_false_off_minutes"]) == 0,
            float(wk07["static_regret_95_interval"][0]) > 0
            and float(wk07["relative_regret_fraction"]) > wk07_threshold,
            float(ui09["normalized_objective_regret_95_interval"][0])
            > ui09_threshold,
        ]
    )


def append_value_rows(values: list[dict[str, object]]) -> None:
    with VALUES_PATH.open(newline="", encoding="utf-8") as handle:
        existing = list(csv.DictReader(handle))
        fieldnames = list(existing[0])
    replace_ids = {str(value["value_id"]) for value in values}
    retained = [
        row for row in existing if str(row["value_id"]) not in replace_ids
    ]
    with VALUES_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(retained + values)


def value_row(
    generated_utc: str,
    value_id: str,
    metric: str,
    estimate: float,
    unit: str,
    format_spec: str,
    notes: str,
) -> dict[str, object]:
    return {
        "value_id": value_id,
        "case_id": "FALSIFICATION",
        "metric": metric,
        "estimate": estimate,
        "lower": "",
        "upper": "",
        "unit": unit,
        "analysis_output": "outputs/analysis/final_falsification.csv",
        "generated_utc": generated_utc,
        "format_spec": format_spec,
        "notes": notes,
    }


def main() -> None:
    payload = json.loads(
        (ANALYSIS / "case_results.json").read_text(encoding="utf-8")
    )
    case_results = {
        str(row["case_id"]): row for row in payload["case_results"]
    }
    primary = set(PRIMARY_CASES)
    frozen = json.loads(
        (PROJECT / "frozen_case_set.json").read_text(encoding="utf-8")
    )
    domains: dict[str, set[str]] = defaultdict(set)
    for row in frozen["frozen_cases"]:
        case_id = str(row["candidate_id"])
        if case_id in primary:
            domains[str(row["domain"])].add(case_id)

    rows = []

    def add(
        test: str,
        scope: str,
        retained: set[str],
        result: str,
        weakened: str,
        interpretation: str,
        threshold_count_override: int | None = None,
    ) -> None:
        rows.append(
            {
                "test": test,
                "scope": scope,
                "primary_cases_retained": len(retained),
                "threshold_meeting_oracle_cases": classification_count(
                    case_results, retained
                )
                if threshold_count_override is None
                else threshold_count_override,
                "result": result,
                "claim_weakened": weakened,
                "interpretation": interpretation,
            }
        )

    baseline_count = classification_count(case_results, primary)
    add(
        "baseline",
        "all primary cases",
        primary,
        (
            f"{baseline_count} of {len(primary)} primary cases meet the "
            "oracle-threshold label"
        ),
        "No",
        "Descriptive classification count only; no pooled magnitude or population rate.",
    )
    for case_id in ["BE03", "WK07", "UI01", "UI09"]:
        retained = primary - {case_id}
        count = classification_count(case_results, retained)
        add(
            "leave_one_primary_case_out",
            case_id,
            retained,
            f"{count} of {len(retained)} retained primary cases meet the label",
            "Yes—material-count claim"
            if case_id in {"WK07", "UI09"}
            else "No",
            "The procedural claim survives; the number of material oracle labels depends on the strongest cases.",
        )
    for domain in ["built_environment", "work", "utilities_infrastructure"]:
        omitted = domains[domain]
        retained = primary - omitted
        count = classification_count(case_results, retained)
        add(
            "leave_one_domain_out",
            f"{domain}: {','.join(sorted(omitted))}",
            retained,
            f"{count} of {len(retained)} retained primary cases meet the label",
            "Yes—material-count claim" if count < 2 else "No",
            "UI01 and UI09 share utilities/infrastructure; domain deletion is not identical to every case deletion.",
        )
    without_wk07 = primary - {"WK07"}
    without_wk07_count = classification_count(case_results, without_wk07)
    add(
        "remove_WK07",
        "simulated C-MAPSS case",
        without_wk07,
        (
            f"{without_wk07_count} of {len(without_wk07)} retained primary "
            "cases meets the label"
        ),
        "Yes—material-count claim",
        "Only the perfect-weather UI09 comparison remains material.",
    )
    without_ui09 = primary - {"UI09"}
    without_ui09_count = classification_count(case_results, without_ui09)
    add(
        "remove_UI09",
        "perfect-weather irrigation case",
        without_ui09,
        (
            f"{without_ui09_count} of {len(without_ui09)} retained primary "
            "cases meets the label"
        ),
        "Yes—material-count claim",
        "Only the simulated perfect-RUL WK07 comparison remains material.",
    )
    without_strongest = primary - set(STRONGEST_ORACLE_CASES)
    without_strongest_count = strongest_case_removal_count(case_results)
    strongest_weakened, strongest_interpretation = (
        strongest_case_removal_assessment(
            without_strongest_count,
            len(without_strongest),
            baseline_count,
        )
    )
    add(
        "remove_WK07_and_UI09",
        "both strongest oracle cases",
        without_strongest,
        (
            f"{without_strongest_count} of {len(without_strongest)} retained "
            "primary cases meets the label"
        ),
        strongest_weakened,
        strongest_interpretation,
    )
    add(
        "exclude_simulated_CMAPSS",
        "source-quality sensitivity",
        without_wk07,
        (
            f"{without_wk07_count} of {len(without_wk07)} retained primary "
            "cases meets the label"
        ),
        "Yes—material-count claim",
        "Material mismatch is not supported by more than one primary case after excluding simulation.",
    )
    add(
        "null_and_network_controls",
        "NC03 and NC01",
        primary,
        "NC03 is an exact narrow null; NC01 remains unquantified",
        "No—procedural claim strengthened",
        "The frozen design does not force every incumbent into a redesign narrative.",
    )

    low_count = threshold_count(case_results, 0.10, 0.025, 0.025)
    current_count = threshold_count(case_results, 0.20, 0.05, 0.05)
    high_count = threshold_count(case_results, 0.30, 0.10, 0.10)
    for label, thresholds, count in [
        ("lower exploratory thresholds", "BE03 10%; WK07 2.5%; UI09 2.5%", low_count),
        ("pre-specified thresholds", "BE03 20%; WK07 5%; UI09 5%", current_count),
        ("higher exploratory thresholds", "BE03 30%; WK07 10%; UI09 10%", high_count),
    ]:
        add(
            "classification_threshold_sensitivity",
            f"{label}: {thresholds}",
            primary,
            f"{count} of 4 primary cases meet the threshold rules",
            "Yes—classification count" if count != current_count else "No",
            "Threshold variation is exploratory; it does not alter the frozen reported classifications.",
            count,
        )

    with (ANALYSIS / "model_sensitivity.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        sensitivity = list(csv.DictReader(handle))
    sensitivity_by_case: dict[str, list[float]] = defaultdict(list)
    for row in sensitivity:
        sensitivity_by_case[str(row["case_id"])].append(
            float(row["estimate"])
        )
    supported_interpretations = {
        "BE03": (
            "Schedule alternatives",
            "Yes—case magnitude and threshold status",
            "Nominal on-time reduction varies strongly with the assumed fixed schedule.",
        ),
        "WK07": (
            "Failure-cost and warning-lead alternatives",
            "No—sign; yes—magnitude",
            "Static regret remains positive across supported settings but remains a simulated perfect-information comparison.",
        ),
        "UI01": (
            "Flexible-load fractions",
            "No—interpretation",
            "Arithmetic savings scale with assumed flexibility; customer response and equilibrium remain unidentified.",
        ),
        "UI09": (
            "Median/mean calendar rule and shortfall penalties",
            "No—sign; yes—magnitude",
            "The objective gap remains positive but depends strongly on the normative loss function.",
        ),
    }
    for case_id in ["BE03", "WK07", "UI01", "UI09"]:
        values = sensitivity_by_case[case_id]
        scope, weakened, interpretation = supported_interpretations[case_id]
        add(
            "supported_model_or_loss_sensitivity",
            f"{case_id}: {scope}",
            primary,
            f"range {min(values):.6g} to {max(values):.6g} {next(row['unit'] for row in sensitivity if row['case_id'] == case_id)}",
            weakened,
            interpretation,
        )

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    config = json.loads(
        (PROJECT / "analysis_config.json").read_text(encoding="utf-8")
    )
    generated_utc = str(config["generated_utc"])
    values = [
        value_row(
            generated_utc,
            "FALS_REMOVE_BOTH_MATERIAL_COUNT",
            "material_oracle_count_without_WK07_UI09",
            without_strongest_count,
            "cases",
            ".0f",
            "Both strongest oracle cases removed",
        ),
        value_row(
            generated_utc,
            "FALS_THRESHOLD_LOW_COUNT",
            "material_count_lower_exploratory_thresholds",
            low_count,
            "cases",
            ".0f",
            "BE03 10%; WK07 2.5%; UI09 2.5%",
        ),
        value_row(
            generated_utc,
            "FALS_THRESHOLD_CURRENT_COUNT",
            "material_count_prespecified_thresholds",
            current_count,
            "cases",
            ".0f",
            "BE03 20%; WK07 5%; UI09 5%",
        ),
        value_row(
            generated_utc,
            "FALS_THRESHOLD_HIGH_COUNT",
            "material_count_higher_exploratory_thresholds",
            high_count,
            "cases",
            ".0f",
            "BE03 30%; WK07 10%; UI09 10%",
        ),
    ]
    for case_id in ["BE03", "WK07", "UI01", "UI09"]:
        case_values = sensitivity_by_case[case_id]
        values.extend(
            [
                value_row(
                    generated_utc,
                    f"FALS_{case_id}_SENS_MIN",
                    "supported_sensitivity_minimum",
                    min(case_values),
                    next(
                        row["unit"]
                        for row in sensitivity
                        if row["case_id"] == case_id
                    ),
                    ".6g",
                    supported_interpretations[case_id][0],
                ),
                value_row(
                    generated_utc,
                    f"FALS_{case_id}_SENS_MAX",
                    "supported_sensitivity_maximum",
                    max(case_values),
                    next(
                        row["unit"]
                        for row in sensitivity
                        if row["case_id"] == case_id
                    ),
                    ".6g",
                    supported_interpretations[case_id][0],
                ),
            ]
        )
    append_value_rows(values)
    print(f"Wrote {len(rows)} final falsification checks")


if __name__ == "__main__":
    main()
