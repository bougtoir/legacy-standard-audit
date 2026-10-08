import csv
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ANALYSIS = PROJECT / "outputs" / "analysis"
TABLES = PROJECT / "outputs" / "tables"
ASSESSMENT = PROJECT / "research_inputs" / "transition_evidence_assessment.csv"
EVIDENCE_LEVEL_RANK = {"none": 0, "C": 1, "B": 2, "A": 3}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sum_column(path: Path, column: str) -> float:
    return sum(float(row[column]) for row in read_csv(path))


def apply_evidence_levels(
    gates: list[dict[str, object]],
    assessments: list[dict[str, str]],
) -> list[dict[str, object]]:
    highest_by_case = {str(gate["case_id"]): "none" for gate in gates}
    for assessment in assessments:
        level = assessment["evidence_level"]
        if level not in EVIDENCE_LEVEL_RANK or level == "none":
            raise ValueError(f"Unsupported evidence level: {level}")
        for case_id in assessment["case_id"].split(";"):
            if (
                case_id in highest_by_case
                and EVIDENCE_LEVEL_RANK[level]
                > EVIDENCE_LEVEL_RANK[highest_by_case[case_id]]
            ):
                highest_by_case[case_id] = level

    status_by_level = {
        "A": "level_a_evidence_available",
        "B": "threshold_only",
        "C": "insufficient_evidence",
        "none": "no_transition_evidence",
    }
    for gate in gates:
        level = highest_by_case[str(gate["case_id"])]
        gate["highest_evidence_level"] = level
        gate["transition_status"] = status_by_level[level]
    return gates


def transition_decision(gates: list[dict[str, object]]) -> str:
    level_a_cases = sorted(
        str(gate["case_id"])
        for gate in gates
        if gate["highest_evidence_level"] == "A"
    )
    if not level_a_cases:
        return (
            "No case reaches Level A. Transition analysis is therefore an "
            "evidence gate: it reports the maximum burden consistent with each "
            "frictionless benchmark and identifies the measurements required "
            "before redesign can be recommended."
        )
    return (
        f"Level A evidence is available for {', '.join(level_a_cases)}. "
        "The pipeline does not automatically convert an evidence classification "
        "into a transition-adjusted estimate; case-specific costs, timing, scale, "
        "and uncertainty must be explicitly modeled and audited before redesign "
        "can be recommended."
    )


def calculate_case_gates(
    case_results: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    be03 = case_results["BE03"]
    be03_fixed = sum_column(ANALYSIS / "BE03_daily_policy.csv", "fixed_on")
    be03_adaptive = sum_column(ANALYSIS / "BE03_daily_policy.csv", "adaptive_on")
    be03_difference = be03_fixed - be03_adaptive
    be03_interval = be03["energy_reduction_95_interval"]

    wk07 = case_results["WK07"]

    ui01 = case_results["UI01"]
    ui01_savings = sum_column(ANALYSIS / "UI01_daily_shift.csv", "savings")
    ui01_shifted = sum_column(ANALYSIS / "UI01_daily_shift.csv", "shifted_mwh")

    ui09 = case_results["UI09"]
    ui09_total_regret = sum_column(
        ANALYSIS / "UI09_weekly_irrigation.csv", "regret"
    )
    ui09_total_calendar_objective = sum_column(
        ANALYSIS / "UI09_weekly_irrigation.csv", "calendar_objective"
    )
    ui09_ratio_interval = ui09["normalized_objective_regret_95_interval"]

    return [
        {
            "case_id": "BE03",
            "gross_static_benefit_value": be03_difference,
            "gross_static_benefit_unit": "nominal illuminated minute-observations",
            "gross_static_benefit_interval": [
                be03_fixed * float(be03_interval[0]),
                be03_fixed * float(be03_interval[1]),
            ],
            "secondary_native_threshold": be03_difference / 60,
            "secondary_native_unit": (
                "kWh avoided per kW of controlled lighting load over the sample"
            ),
            "break_even_rule": (
                "Present value of equipment, installation, commissioning, "
                "maintenance, communication, control, and sensor-error penalties "
                "must not exceed 1766 illuminated minute-observations, equivalent "
                "to 29.4333 kWh per kW of controlled load before valuation."
            ),
            "unidentified_inputs": [
                "controlled lighting power",
                "electricity tariff",
                "sensor false-positive and false-negative rates",
                "room and fixture inventory",
                "installation and commissioning requirements",
                "maintenance and battery replacement",
                "deployment horizon",
            ],
        },
        {
            "case_id": "WK07",
            "gross_static_benefit_value": float(
                wk07["static_regret_cost_per_cycle"]
            ),
            "gross_static_benefit_unit": (
                "preventive-replacement-cost units per operating cycle"
            ),
            "gross_static_benefit_interval": list(
                wk07["static_regret_95_interval"]
            ),
            "secondary_native_threshold": float(wk07["relative_regret_fraction"]),
            "secondary_native_unit": "fraction of fixed-policy cost rate",
            "break_even_rule": (
                "The amortized transition and operating burden must remain below "
                "0.002499 preventive-replacement-cost units per cycle. A one-time "
                "system cost requires an identified fleet scale, exposure horizon, "
                "discount rate, and approved error-cost model."
            ),
            "unidentified_inputs": [
                "sensor and data-system costs",
                "integration and validation costs",
                "false-alarm and missed-failure consequences",
                "training and operating labor",
                "certification and authorization pathway",
                "fleet scale and operating horizon",
                "safety and reliability valuation",
            ],
        },
        {
            "case_id": "UI01",
            "gross_static_benefit_value": float(
                ui01["procurement_savings_eur_per_mwh"]
            ),
            "gross_static_benefit_unit": "EUR per baseline MWh",
            "gross_static_benefit_interval": list(
                ui01["procurement_savings_eur_per_mwh_95_interval"]
            ),
            "secondary_native_threshold": ui01_savings / ui01_shifted,
            "secondary_native_unit": "EUR per shifted MWh",
            "break_even_rule": (
                "Incremental metering, ICT, control, contract, coordination, and "
                "participation burdens must remain below EUR 0.071845 per baseline "
                "MWh, or EUR 14.629 per shifted MWh, under the fixed-price 1% "
                "load-shifting arithmetic."
            ),
            "unidentified_inputs": [
                "meter and participant population",
                "existing versus incremental AMI capability",
                "control and communications costs",
                "retail contract and settlement rules",
                "customer adoption and rebound",
                "market-price and network response",
                "deployment horizon",
            ],
        },
        {
            "case_id": "UI09",
            "gross_static_benefit_value": ui09_total_regret,
            "gross_static_benefit_unit": (
                "millimetre-equivalent objective units over 135 evaluation weeks"
            ),
            "gross_static_benefit_interval": [
                ui09_total_calendar_objective * float(ui09_ratio_interval[0]),
                ui09_total_calendar_objective * float(ui09_ratio_interval[1]),
            ],
            "secondary_native_threshold": ui09_total_regret
            / float(ui09["evaluation_weeks"]),
            "secondary_native_unit": (
                "millimetre-equivalent objective units per evaluation week"
            ),
            "break_even_rule": (
                "Transition burden must remain below 9608.723 objective units "
                "over the evaluation sample. Because the objective embeds a "
                "fivefold shortfall penalty, this quantity is not physical water "
                "savings and cannot be monetized without crop-, soil-, system-, "
                "area-, efficiency-, yield-, and price-specific evidence."
            ),
            "unidentified_inputs": [
                "crop coefficient and growth stage",
                "root-zone soil-water storage",
                "irrigation-system efficiency and uniformity",
                "field area and flow measurement",
                "yield response and shortfall consequences",
                "equipment installation maintenance and telemetry",
                "useful life and local water valuation",
            ],
        },
    ]


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    with (ANALYSIS / "case_results.json").open(encoding="utf-8") as handle:
        case_results_list = json.load(handle)["case_results"]
    case_results = {row["case_id"]: row for row in case_results_list}

    assessments = read_csv(ASSESSMENT)
    gates = apply_evidence_levels(
        calculate_case_gates(case_results),
        assessments,
    )
    gate_by_case = {row["case_id"]: row for row in gates}

    output_rows = []
    for assessment in assessments:
        case_ids = assessment["case_id"].split(";")
        threshold_cases = [
            gate_by_case[case_id] for case_id in case_ids if case_id in gate_by_case
        ]
        row = dict(assessment)
        row["case_thresholds"] = " | ".join(
            (
                f"{gate['case_id']}: {gate['gross_static_benefit_value']:.12g} "
                f"{gate['gross_static_benefit_unit']}"
            )
            for gate in threshold_cases
        )
        output_rows.append(row)

    matrix_path = TABLES / "transition_evidence_matrix.csv"
    fieldnames = list(output_rows[0])
    with matrix_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    result = {
        "evidence_level_definitions": {
            "A": (
                "Case-compatible empirical transition-cost evidence permitting "
                "a justified transition-adjusted estimate."
            ),
            "B": (
                "Credible but insufficiently case-specific evidence permitting "
                "threshold or break-even analysis only."
            ),
            "C": (
                "Weak, duplicate, or non-comparable evidence that cannot support "
                "a transition-cost inference."
            ),
        },
        "source_counts": {
            level: sum(row["evidence_level"] == level for row in assessments)
            for level in ["A", "B", "C"]
        },
        "any_level_a": any(
            gate["highest_evidence_level"] == "A" for gate in gates
        ),
        "decision": transition_decision(gates),
        "discount_reference": {
            "source_id": "TR-CROSS-OMB-A94",
            "nominal_percent_by_maturity_years": {
                "3": 3.4,
                "5": 3.5,
                "7": 3.6,
                "10": 3.7,
                "20": 4.0,
                "30": 4.1,
            },
            "real_percent_by_maturity_years": {
                "3": 1.1,
                "5": 1.3,
                "7": 1.4,
                "10": 1.6,
                "20": 2.0,
                "30": 2.0,
            },
            "application": (
                "Sensitivity reference only; not applied because compatible "
                "cash flows and useful lives are unidentified."
            ),
        },
        "case_gates": gates,
    }
    with (ANALYSIS / "transition_evidence_results.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    values_path = PROJECT / "MANUSCRIPT_VALUES.csv"
    with values_path.open(newline="", encoding="utf-8") as handle:
        existing_values = list(csv.DictReader(handle))
        value_fields = list(existing_values[0])
    value_ids = {
        "TRANSITION_LEVEL_A_SOURCES",
        "TRANSITION_LEVEL_B_SOURCES",
        "TRANSITION_LEVEL_C_SOURCES",
    }
    retained_values = [
        row for row in existing_values if row["value_id"] not in value_ids
    ]
    generated_utc = json.loads(
        (PROJECT / "analysis_config.json").read_text(encoding="utf-8")
    )["generated_utc"]
    added_values = [
        {
            "value_id": f"TRANSITION_LEVEL_{level}_SOURCES",
            "case_id": "TRANSITION",
            "metric": f"level_{level.lower()}_source_count",
            "estimate": result["source_counts"][level],
            "lower": "",
            "upper": "",
            "unit": "sources",
            "analysis_output": "outputs/analysis/transition_evidence_results.json",
            "generated_utc": generated_utc,
            "format_spec": ".0f",
            "notes": result["evidence_level_definitions"][level],
        }
        for level in ["A", "B", "C"]
    ]
    with values_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=value_fields, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(retained_values + added_values)
        handle.write("\n")

    print(f"Wrote {matrix_path.relative_to(PROJECT)}")
    print("Wrote outputs/analysis/transition_evidence_results.json")


if __name__ == "__main__":
    main()
