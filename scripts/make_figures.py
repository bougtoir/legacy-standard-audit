import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from publication_utils import (
    FIGURE_ORDER,
    OUTPUT,
    display,
    fig as figure_label,
    figure_filename,
    interval,
    load_results,
    load_values,
    numeric,
)


FIGURE_DIR = OUTPUT / "figures"
FIGURE_TITLES = dict(FIGURE_ORDER)
BLUE = "#176B87"
TEAL = "#2A9D8F"
GOLD = "#E9C46A"
RED = "#C8553D"
GRAY = "#6B7280"

PRIMARY_AUDIT_ROWS = {
    "BE03": [
        "Occupancy sensing\nand responsive control",
        "Perfect-label on-time proxy",
    ],
    "WK07": [
        "Condition sensing\nand prognostics",
        "Simulated perfect-RUL oracle",
    ],
    "UI01": [
        "Interval metering\nand flexible control",
        "Fixed-price partial equilibrium",
    ],
    "UI09": [
        "Weather data, model,\nand responsive scheduling",
        "Perfect-weather reference crop",
    ],
}
FIXED_AUDIT_ROWS = [
    [
        "TR01",
        "Traffic observation\nand responsive allocation",
        "Directional delay proxy;\ninsufficient",
        "Gate not reached;\nstatic evidence insufficient",
        "Insufficient\nevidence",
    ],
    [
        "NC01",
        "Compatibility and\nnetwork coordination",
        "No quantified comparator;\ninsufficient",
        "Gate not reached;\nstatic evidence insufficient",
        "Insufficient\nevidence",
    ],
    [
        "NC03",
        "Geometric\nself-similarity",
        "Exact repeated-halving null",
        "Not required for\nthe narrow null",
        "No mismatch for\nspecified objective",
    ],
]


def audit_state_rows(
    results: dict[str, dict[str, object]],
    transition: dict[str, object],
) -> list[list[str]]:
    transition_labels = {
        "A": "Level A evidence;\nexplicit model required",
        "B": "Level B;\nnative-unit gate only",
        "C": "Level C;\nno case inference",
        "none": "No transition\nevidence",
    }
    classification_labels = {
        "small_or_uncertain_mismatch": "Small/uncertain\nmismatch",
        "insufficient_evidence": "Insufficient\nevidence",
        "no_mismatch_for_repeated_halving_objective": (
            "No mismatch for\nspecified objective"
        ),
    }
    static_classification_labels = {
        "small_or_uncertain_mismatch": "small or uncertain",
        "insufficient_evidence": "insufficient",
    }
    gate_by_case = {
        str(gate["case_id"]): gate for gate in transition["case_gates"]
    }
    rows = []
    for case_id, (mechanism, static_evidence) in PRIMARY_AUDIT_ROWS.items():
        classification = str(results[case_id]["classification"])
        static_classification = (
            "threshold met"
            if classification.startswith("material_mismatch")
            else static_classification_labels[classification]
        )
        final_state = (
            "Material label\nunder oracle"
            if classification.startswith("material_mismatch")
            else classification_labels[classification]
        )
        level = str(gate_by_case[case_id]["highest_evidence_level"])
        rows.append(
            [
                case_id,
                mechanism,
                f"{static_evidence};\n{static_classification}",
                transition_labels[level],
                final_state,
            ]
        )
    return rows + FIXED_AUDIT_ROWS


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.savefig(
        FIGURE_DIR / name,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def figure_audit_framework() -> None:
    fig, ax = plt.subplots(figsize=(11, 5.7))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (0.3, 3.7, 2.0, 1.1, "Incumbent problem", "Historically defensible;\noptimum may be unidentified"),
        (3.0, 3.7, 2.0, 1.1, "Technology change", "Sensing, computation,\ncommunication, control"),
        (5.7, 3.7, 2.0, 1.1, "Current static audit", "Incumbent versus\nfrictionless comparator"),
        (8.4, 3.7, 2.2, 1.1, "Transition audit", "Switching, safety,\nnetwork and policy costs"),
    ]
    for x, y, width, height, title, subtitle in boxes:
        patch = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.08",
            linewidth=1.4,
            edgecolor=BLUE,
            facecolor="#EAF4F8",
        )
        ax.add_patch(patch)
        ax.text(x + width / 2, y + 0.72, title, ha="center", va="center", weight="bold")
        ax.text(x + width / 2, y + 0.30, subtitle, ha="center", va="center", fontsize=9)
    for start, end in [(2.3, 3.0), (5.0, 5.7), (7.7, 8.4)]:
        ax.annotate(
            "",
            xy=(end, 4.25),
            xytext=(start, 4.25),
            arrowprops={"arrowstyle": "->", "lw": 1.8, "color": GRAY},
        )
    outcomes = [
        (0.8, 1.25, 2.7, "Threshold met under oracle", RED),
        (4.15, 1.25, 2.7, "Small or uncertain mismatch", GOLD),
        (7.5, 1.25, 2.7, "No mismatch / insufficient evidence", TEAL),
    ]
    for x, y, width, text, color in outcomes:
        patch = FancyBboxPatch(
            (x, y),
            width,
            0.8,
            boxstyle="round,pad=0.06",
            linewidth=1.2,
            edgecolor=color,
            facecolor="white",
        )
        ax.add_patch(patch)
        ax.text(x + width / 2, y + 0.4, text, ha="center", va="center", weight="bold")
    ax.text(
        5.5,
        0.45,
        "Redesign additionally requires favorable transition, safety, and regulatory evidence.",
        ha="center",
        va="center",
        fontsize=11,
        weight="bold",
    )
    save_figure(fig, figure_filename("audit_framework"))


def figure_primary_benchmarks(values: dict[str, dict[str, str]]) -> None:
    panels = [
        ("BE03", "Nominal on-time reduction", "BE03_ENERGY_REDUCTION", "Fraction"),
        ("WK07", "Static regret", "WK07_STATIC_REGRET", "Normalized cost/cycle"),
        ("UI01", "Fixed-price arithmetic saving", "UI01_SAVINGS_PER_MWH", "EUR/MWh baseline"),
        ("UI09", "Objective regret", "UI09_OBJECTIVE_REGRET", "Fraction"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    for ax, (case_id, title, value_id, unit) in zip(axes.ravel(), panels):
        row = values[value_id]
        estimate = float(row["estimate"])
        lower = float(row["lower"])
        upper = float(row["upper"])
        margin = max((upper - lower) * 1.3, abs(estimate) * 0.18)
        ax.errorbar(
            estimate,
            0,
            xerr=np.array([[estimate - lower], [upper - estimate]]),
            fmt="o",
            color=BLUE,
            ecolor=BLUE,
            capsize=5,
            markersize=8,
        )
        ax.axvline(0, color="#A0A0A0", lw=1)
        ax.set_xlim(min(0, lower - margin), upper + margin)
        ax.set_yticks([])
        ax.set_xlabel(unit)
        ax.set_title(f"{case_id}: {title}", loc="left", weight="bold")
        ax.text(
            0.02,
            0.82,
            f"{display(values, value_id)} (95% block/bootstrap interval "
            f"{interval(values, value_id)})",
            transform=ax.transAxes,
            fontsize=9,
        )
        ax.spines[["top", "right", "left"]].set_visible(False)
    fig.suptitle(
        "Frozen primary-case technical benchmarks (case-specific scales)",
        weight="bold",
        fontsize=13,
    )
    fig.text(
        0.5,
        0.01,
        "Panels are not a pooled effect size; comparators are oracle or partial-equilibrium bounds.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    save_figure(fig, figure_filename("primary_case_benchmarks"))


def figure_case_classifications(rows: list[list[str]]) -> None:
    columns = [
        "Case",
        "Technology mechanism",
        "Static evidence",
        "Transition evidence",
        "Final audit state",
    ]
    fig, ax = plt.subplots(figsize=(13.5, 7.0))
    ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=columns,
        cellLoc="left",
        colLoc="left",
        colWidths=[0.07, 0.22, 0.29, 0.23, 0.19],
        bbox=[0, 0.05, 1, 0.86],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    for (row, column), cell in table.get_celld().items():
        cell.set_edgecolor("#CBD5E1")
        if row == 0:
            cell.set_facecolor("#DCEEF5")
            cell.set_text_props(weight="bold")
        elif column == 3:
            evidence = rows[row - 1][3]
            if "Level A" in evidence:
                cell.set_facecolor("#DCFCE7")
            elif "Level B" in evidence:
                cell.set_facecolor("#FFF7D6")
        elif column == 4:
            cell.set_facecolor("#F3F4F6")
    ax.set_title(
        "Frozen-case audit-state matrix: common gates, non-common effect units",
        weight="bold",
        fontsize=13,
        pad=12,
    )
    fig.text(
        0.5,
        0.015,
        "Heterogeneity tests protocol portability; it does not identify a pooled magnitude or population rate.",
        ha="center",
        fontsize=9,
    )
    save_figure(fig, figure_filename("case_classifications"))


def sensitivity_rows(values: dict[str, dict[str, str]], case_id: str):
    rows = [
        row
        for value_id, row in values.items()
        if value_id.startswith(f"SENS_{case_id}_")
    ]
    return rows


SENSITIVITY_PANELS = {
    "BE03": ("BE03_ENERGY_REDUCTION", "THRESHOLD_BE03", "Fixed schedule"),
    "WK07": ("WK07_STATIC_REGRET", None, "Failure-cost ratio; warning lead (cycles)"),
    "UI01": ("UI01_SAVINGS_PER_MWH", None, "Flexible-load fraction"),
    "UI09": ("UI09_OBJECTIVE_REGRET", "THRESHOLD_UI09", "Calendar rule; shortfall penalty"),
}


def figure_sensitivity(values: dict[str, dict[str, str]]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.4))
    for ax, (case_id, (primary_id, threshold_id, axis_label)) in zip(
        axes.ravel(), SENSITIVITY_PANELS.items()
    ):
        rows = sensitivity_rows(values, case_id)
        labels = [
            row["notes"].split(": ", 1)[1].replace("cost=", "").replace(";lead=", "; ")
            .replace(";penalty=", "; ")
            for row in rows
        ]
        estimates = np.array([float(row["estimate"]) for row in rows])
        primary = numeric(values, primary_id)
        is_primary = np.isclose(estimates, primary, rtol=1e-12, atol=0)
        positions = np.arange(len(rows))
        ax.scatter(positions[~is_primary], estimates[~is_primary], color=BLUE, s=42, zorder=3,
                   label="Alternative setting")
        ax.scatter(positions[is_primary], estimates[is_primary], color=RED, marker="D", s=58,
                   zorder=4, label="Pre-specified setting")
        if threshold_id:
            threshold = numeric(values, threshold_id)
            ax.axhline(threshold, color=GRAY, ls="--", lw=1.2,
                       label=f"Material threshold ({display(values, threshold_id)})")
        ax.set_xticks(positions, labels, rotation=45 if len(rows) > 6 else 0,
                      ha="right" if len(rows) > 6 else "center", fontsize=9)
        ax.set_xlabel(axis_label, fontsize=10)
        ax.set_title(case_id, loc="left", weight="bold")
        ax.set_ylabel(rows[0]["unit"] if rows else "", fontsize=10)
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.25)
        ax.legend(fontsize=8, loc="best", frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Pre-specified model sensitivity by case (case-specific scales)",
                 weight="bold", fontsize=13)
    fig.text(0.5, 0.01, "Points are point estimates; settings are not pooled across cases.",
             ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    save_figure(fig, figure_filename("model_sensitivity"))


def add_text_box(slide, x, y, width, height, text, fill, font_size=16, bold=False):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x),
        Inches(y),
        Inches(width),
        Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(*fill)
    shape.line.color.rgb = RGBColor(23, 107, 135)
    frame = shape.text_frame
    frame.clear()
    paragraph = frame.paragraphs[0]
    paragraph.alignment = PP_ALIGN.CENTER
    run = paragraph.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    return shape


def build_editable_pptx(
    values: dict[str, dict[str, str]],
    results: dict[str, dict[str, object]],
    audit_rows: list[list[str]],
) -> None:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    title_layout = presentation.slide_layouts[6]

    slide = presentation.slides.add_slide(title_layout)
    add_text_box(slide, 0.5, 0.25, 12.3, 0.65, f"{figure_label('audit_framework')}. {FIGURE_TITLES['audit_framework']}", (255, 255, 255), 24, True)
    labels = [
        "Incumbent problem\nHistorically defensible • optimum may be unidentified",
        "Technology change\nSensing • computation • control",
        "Static audit\nIncumbent vs frictionless comparator",
        "Transition audit\nSwitching • network • safety costs",
    ]
    for index, label in enumerate(labels):
        add_text_box(slide, 0.4 + index * 3.2, 2.0, 2.7, 1.3, label, (234, 244, 248), 14, True)
        if index < 3:
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW,
                Inches(3.0 + index * 3.2),
                Inches(2.45),
                Inches(0.6),
                Inches(0.35),
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = RGBColor(107, 114, 128)
            arrow.line.fill.background()
    add_text_box(
        slide,
        2.7,
        5.25,
        8.0,
        0.8,
        "Recommend change only with case-compatible transition evidence",
        (255, 255, 255),
        18,
        True,
    )

    slide = presentation.slides.add_slide(title_layout)
    add_text_box(slide, 0.5, 0.25, 12.3, 0.65, f"{figure_label('primary_case_benchmarks')}. {FIGURE_TITLES['primary_case_benchmarks']}", (255, 255, 255), 24, True)
    benchmark_ids = [
        ("BE03", "BE03_ENERGY_REDUCTION"),
        ("WK07", "WK07_STATIC_REGRET"),
        ("UI01", "UI01_SAVINGS_PER_MWH"),
        ("UI09", "UI09_OBJECTIVE_REGRET"),
    ]
    for index, (case_id, value_id) in enumerate(benchmark_ids):
        x = 0.7 + (index % 2) * 6.2
        y = 1.3 + (index // 2) * 2.8
        add_text_box(slide, x, y, 5.5, 0.55, case_id, (234, 244, 248), 18, True)
        add_text_box(
            slide,
            x,
            y + 0.75,
            5.5,
            1.15,
            f"Estimate: {display(values, value_id)}\n95% interval: {interval(values, value_id)}\n{values[value_id]['unit']}",
            (255, 255, 255),
            15,
        )

    slide = presentation.slides.add_slide(title_layout)
    add_text_box(slide, 0.4, 0.18, 12.5, 0.55, f"{figure_label('case_classifications')}. {FIGURE_TITLES['case_classifications']}", (255, 255, 255), 22, True)
    column_specs = [
        (0.35, 0.75, "Case"),
        (1.1, 2.35, "Technology mechanism"),
        (3.5, 3.4, "Static evidence"),
        (6.95, 2.8, "Transition evidence"),
        (9.8, 3.15, "Final audit state"),
    ]
    for x, width, label in column_specs:
        add_text_box(slide, x, 0.82, width, 0.48, label, (220, 238, 245), 10, True)
    for row_index, row_values in enumerate(audit_rows):
        y = 1.38 + row_index * 0.82
        for (x, width, _), text in zip(column_specs, row_values):
            add_text_box(
                slide,
                x,
                y,
                width,
                0.72,
                text,
                (
                    (220, 252, 231)
                    if "Level A" in text
                    else (255, 247, 214)
                    if "Level B" in text
                    else (255, 255, 255)
                ),
                8,
                x == 0.35,
            )

    slide = presentation.slides.add_slide(title_layout)
    add_text_box(slide, 0.5, 0.25, 12.3, 0.65, f"{figure_label('model_sensitivity')}. {FIGURE_TITLES['model_sensitivity']}", (255, 255, 255), 24, True)
    for index, case_id in enumerate(["BE03", "WK07", "UI01", "UI09"]):
        rows = sensitivity_rows(values, case_id)
        text = "\n".join(
            f"{row['notes'].split(': ', 1)[1]}: {float(row['estimate']):.4g}"
            for row in rows
        )
        x = 0.7 + (index % 2) * 6.2
        y = 1.15 + (index // 2) * 3.0
        add_text_box(slide, x, y, 5.5, 0.55, case_id, (234, 244, 248), 17, True)
        add_text_box(slide, x, y + 0.65, 5.5, 2.0, text, (255, 255, 255), 10)

    slide_ids = presentation.slides._sldIdLst
    sensitivity_slide = list(slide_ids)[-1]
    slide_ids.remove(sensitivity_slide)
    slide_ids.insert(
        [key for key, _ in FIGURE_ORDER].index("model_sensitivity"), sensitivity_slide
    )
    presentation.save(FIGURE_DIR / "Figures_editable.pptx")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.titlecolor": "#1F2937",
            "axes.labelcolor": "#374151",
            "text.color": "#1F2937",
        }
    )
    values = load_values()
    results = load_results()
    transition = json.loads(
        (OUTPUT / "analysis" / "transition_evidence_results.json").read_text(
            encoding="utf-8"
        )
    )
    rows = audit_state_rows(results, transition)
    figure_audit_framework()
    figure_primary_benchmarks(values)
    figure_case_classifications(rows)
    figure_sensitivity(values)
    build_editable_pptx(values, results, rows)
    print("Wrote 4 figures and editable PPTX")


if __name__ == "__main__":
    main()
