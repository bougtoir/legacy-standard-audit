import csv

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from publication_utils import (
    OUTPUT,
    add_table,
    configured_document,
    display,
    interval,
    load_results,
    load_values,
    tab,
    table_filename,
)


TABLE_DIR = OUTPUT / "tables"


def write_csv(name: str, headers: list[str], rows: list[list[object]]) -> None:
    with (TABLE_DIR / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def tables(values, results):
    table1_headers = ["Audit stage", "Required evidence", "Decision output"]
    table1_rows = [
        [
            "Historical reconstruction",
            "Objective, information set, feasible set, coordination conditions",
            "Historically defensible incumbent problem",
        ],
        [
            "Technology-mediated change",
            "Sensing, computation, communication, automation, adaptive control",
            "Changed parameter or feasible-set claim",
        ],
        [
            "Static audit",
            "Incumbent and contemporary comparator under a common objective",
            "Case-specific static benchmark gap",
        ],
        [
            "Transition audit",
            "Switching, compatibility, safety, regulation, network effects",
            "Transition-adjusted estimate or break-even gate",
        ],
        [
            "Governance",
            "Frozen cases, uncertainty, null controls, falsification",
            "Material, uncertain, null, or insufficient classification",
        ],
    ]
    table2_headers = [
        "Case",
        "Role",
        "Persisted input",
        "Analysis unit",
        "Contemporary comparator",
        "Critical limitation",
    ]
    table2_rows = [
        [
            "BE03",
            "Primary",
            "UCI office occupancy",
            f"{display(values, 'BE03_OBSERVATIONS')} minute-observations",
            f"Perfect-label occupancy comparator, {display(values, 'BE03_HOLD')}-minute hold",
            "No sensor error, power, commissioning, or installation cost",
        ],
        [
            "WK07",
            "Primary",
            "NASA C-MAPSS FD001 simulation",
            f"{display(values, 'WK07_EVALUATION_UNITS')} evaluation units",
            "Perfect remaining-life condition policy",
            "Simulated trajectories; no observed maintenance program",
        ],
        [
            "UI01",
            "Primary",
            "OPSD load and day-ahead prices",
            f"{display(values, 'UI01_COMPLETE_DAYS')} complete days",
            f"{display(values, 'UI01_FLEXIBLE_FRACTION')} bounded load shift",
            "Fixed prices; no tariff assignment or customer response",
        ],
        [
            "UI09",
            "Primary",
            "NASA POWER weather and FAO-56",
            f"{display(values, 'UI09_EVALUATION_WEEKS')} evaluation weeks",
            "Perfect-weather reference-crop requirement",
            "No crop coefficient, soil storage, efficiency, or yield model",
        ],
        [
            "TR01",
            "Supplementary",
            "NYC directional traffic counts",
            f"{display(values, 'TR01_EVALUATION_DAYS')} evaluation days",
            "Demand-proportional directional allocation proxy",
            "No verified intersection or deployed timing plan",
        ],
        [
            "NC01",
            "Network control",
            "ISO container-standard metadata",
            "Not estimable",
            "Break-even identity only",
            "No fleet, conversion, or network-cost data",
        ],
        [
            "NC03",
            "Analytic null",
            "ISO 216 geometric principle",
            "Exact analytic objective",
            r"Positive solution r = √2",
            "Applies only to repeated-halving similarity",
        ],
    ]
    table3_headers = [
        "Case",
        "Pre-specified metric",
        "Estimate",
        "95% interval",
        "Classification",
    ]
    table3_rows = [
        [
            "BE03",
            "Nominal lighting on-time reduction",
            display(values, "BE03_ENERGY_REDUCTION"),
            interval(values, "BE03_ENERGY_REDUCTION"),
            display(values, "BE03_CLASSIFICATION"),
        ],
        [
            "WK07",
            "Static regret, normalized cost/cycle",
            display(values, "WK07_STATIC_REGRET"),
            interval(values, "WK07_STATIC_REGRET"),
            display(values, "WK07_CLASSIFICATION"),
        ],
        [
            "UI01",
            "Fixed-price arithmetic saving, EUR/MWh baseline",
            display(values, "UI01_SAVINGS_PER_MWH"),
            interval(values, "UI01_SAVINGS_PER_MWH"),
            display(values, "UI01_CLASSIFICATION"),
        ],
        [
            "UI09",
            "Normalized objective regret",
            display(values, "UI09_OBJECTIVE_REGRET"),
            interval(values, "UI09_OBJECTIVE_REGRET"),
            display(values, "UI09_CLASSIFICATION"),
        ],
        [
            "TR01",
            "Delay-proxy reduction",
            display(values, "TR01_PROXY_REDUCTION"),
            interval(values, "TR01_PROXY_REDUCTION"),
            display(values, "TR01_CLASSIFICATION"),
        ],
        [
            "NC01",
            "Static/transition regret",
            "Not estimated",
            "Not estimated",
            display(values, "NC01_CLASSIFICATION"),
        ],
        [
            "NC03",
            "Repeated-halving loss",
            display(values, "NC03_SELF_SIMILARITY_LOSS"),
            "Exact analytic result",
            display(values, "NC03_CLASSIFICATION"),
        ],
    ]
    falsification = pd.read_csv(
        OUTPUT / "analysis" / "final_falsification.csv"
    )
    table4_headers = [
        "Test (scope)",
        "Result",
        "Claim weakened?",
        "Interpretation",
    ]
    table4_rows = falsification_rows(falsification)
    return [
        (table_filename("audit_framework"), table1_headers, table1_rows, f"{tab('audit_framework')}. Legacy Standard Audit stages."),
        (table_filename("case_design"), table2_headers, table2_rows, f"{tab('case_design')}. Frozen case design and evidentiary limits."),
        (table_filename("case_results"), table3_headers, table3_rows, f"{tab('case_results')}. Case-specific technical benchmark results."),
        (
            table_filename("falsification"),
            table4_headers,
            table4_rows,
            f"{tab('falsification')}. Cross-case falsification: case and domain removal, "
            "source quality, thresholds, supported model or loss alternatives, and controls. "
            "Counts refer to primary cases meeting the material-mismatch label.",
        ),
    ]


def _short_count(result: str) -> str:
    count, _, rest = result.partition(" of ")
    total = rest.split(" ", 1)[0]
    return f"{count}/{total}"


def falsification_rows(falsification: pd.DataFrame) -> list[list[str]]:
    """Compact the full falsification output without dropping unique tests."""

    def grouped(test: str, label: str, scope_name) -> list[str]:
        subset = falsification[falsification["test"] == test]
        results = "; ".join(
            f"{scope_name(row.scope)} {_short_count(row.result)}"
            for row in subset.itertuples()
        )
        weakened = list(
            dict.fromkeys(
                scope_name(row.scope)
                for row in subset.itertuples()
                if row.claim_weakened != "No"
            )
        )
        verdict = (
            f"Yes—material-count claim ({', '.join(weakened)})" if weakened else "No"
        )
        return [label, results, verdict, subset.iloc[0]["interpretation"]]

    def single(test: str, label: str) -> list[str]:
        row = falsification[falsification["test"] == test].iloc[0]
        return [
            f"{label} ({row['scope']})",
            row["result"],
            row["claim_weakened"],
            row["interpretation"],
        ]

    rows = [
        single("baseline", "Baseline"),
        grouped(
            "leave_one_primary_case_out",
            "Leave one primary case out",
            lambda scope: scope,
        ),
        grouped(
            "leave_one_domain_out",
            "Leave one domain out",
            lambda scope: scope.split(": ", 1)[1].replace(",", "+"),
        ),
        single("remove_WK07_and_UI09", "Remove WK07 and UI09 together"),
        single("exclude_simulated_CMAPSS", "Exclude simulated C-MAPSS"),
    ]
    thresholds = falsification[falsification["test"] == "classification_threshold_sensitivity"]
    rows.append(
        [
            "Classification thresholds (lower, pre-specified, higher)",
            "; ".join(
                f"{row.scope.split(' ', 1)[0]} ({row.scope.split(': ', 1)[1]}) "
                f"{_short_count(row.result)}"
                for row in thresholds.itertuples()
            ),
            "; ".join(
                f"{row.scope.split(' ', 1)[0]}: {row.claim_weakened}"
                for row in thresholds.itertuples()
            ),
            thresholds.iloc[0]["interpretation"],
        ]
    )
    for row in falsification[
        falsification["test"] == "supported_model_or_loss_sensitivity"
    ].itertuples():
        rows.append(
            [f"Model or loss alternatives ({row.scope})", row.result,
             row.claim_weakened, row.interpretation]
        )
    rows.append(single("null_and_network_controls", "Null and network controls"))
    return rows


def build_word_tables(specifications) -> None:
    document = configured_document()
    document.add_heading("Editable tables", 0)
    for _, headers, rows, caption in specifications:
        add_table(document, headers, rows, caption)
    document.save(TABLE_DIR / "Tables_editable.docx")


def build_pptx_tables(specifications) -> None:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    for _, headers, rows, caption in specifications:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        title = slide.shapes.add_textbox(
            Inches(0.4), Inches(0.15), Inches(12.5), Inches(0.6)
        )
        title.text_frame.text = caption
        title.text_frame.paragraphs[0].runs[0].font.size = Pt(20)
        title.text_frame.paragraphs[0].runs[0].font.bold = True
        max_rows = min(len(rows), 13)
        table = slide.shapes.add_table(
            max_rows + 1,
            len(headers),
            Inches(0.25),
            Inches(0.9),
            Inches(12.8),
            Inches(6.2),
        ).table
        for column, header in enumerate(headers):
            cell = table.cell(0, column)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(217, 234, 247)
        for row_index, row in enumerate(rows[:max_rows], start=1):
            for column, value in enumerate(row):
                table.cell(row_index, column).text = str(value)
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.alignment = PP_ALIGN.LEFT
                    for run in paragraph.runs:
                        run.font.size = Pt(7 if len(headers) > 5 else 9)
                        run.font.name = "Arial"
    presentation.save(TABLE_DIR / "Tables_editable.pptx")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    values = load_values()
    results = load_results()
    specifications = tables(values, results)
    for filename, headers, rows, _ in specifications:
        write_csv(filename, headers, rows)
    build_word_tables(specifications)
    build_pptx_tables(specifications)
    print(f"Wrote {len(specifications)} tables and editable DOCX/PPTX")


if __name__ == "__main__":
    main()
