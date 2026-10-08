import json
import subprocess
from pathlib import Path

import pandas as pd
from docx.enum.text import WD_ALIGN_PARAGRAPH

from make_tables import tables
from publication_utils import (
    OUTPUT,
    FIGURE_ORDER,
    TABLE_ORDER,
    add_display_math,
    add_figure,
    add_page_number,
    add_rich_text,
    add_table,
    configured_document,
    display,
    interval,
    load_results,
    load_values,
    numeric,
    sentence_number,
    tab,
)
from publication_utils import fig as figure_label
from publication_utils import figure_filename


MANUSCRIPT_DIR = OUTPUT / "manuscript"
FIGURE_DIR = OUTPUT / "figures"
TITLE = (
    "Re-auditing legacy standards after technological change: "
    "a pre-specified protocol for static benchmarks and transition-evidence gates"
)


def add_paragraph(document, text: str, bold_lead: str | None = None) -> None:
    paragraph = document.add_paragraph()
    if bold_lead and text.startswith(bold_lead):
        paragraph.add_run(bold_lead).bold = True
        add_rich_text(paragraph, text[len(bold_lead) :])
    else:
        add_rich_text(paragraph, text)


def figure_path(key: str) -> Path:
    return FIGURE_DIR / figure_filename(key)


def sensitivity_settings(values, case_id: str) -> list[str]:
    return [
        row["notes"].split(": ", 1)[1]
        for value_id, row in values.items()
        if value_id.startswith(f"SENS_{case_id}_")
    ]


def sensitivity_range(values, case_id: str, percent: bool) -> str:
    low = numeric(values, f"FALS_{case_id}_SENS_MIN")
    high = numeric(values, f"FALS_{case_id}_SENS_MAX")
    if percent:
        return f"{low:.1%} to {high:.1%}"
    unit = values[f"FALS_{case_id}_SENS_MIN"]["unit"]
    return f"{low:.3g} to {high:.3g} {unit}"


def join_settings(settings: list[str]) -> str:
    if len(settings) <= 2:
        return " and ".join(settings)
    return ", ".join(settings[:-1]) + f", and {settings[-1]}"


def level_a_case_ids(transition: dict[str, object]) -> list[str]:
    return sorted(
        str(gate["case_id"])
        for gate in transition["case_gates"]
        if gate["highest_evidence_level"] == "A"
    )


def strongest_case_abstract_text(values) -> str:
    count = int(float(values["FALS_REMOVE_BOTH_MATERIAL_COUNT"]["estimate"]))
    if count == 0:
        return (
            "Removing both threshold-meeting oracle cases eliminated material "
            "primary labels."
        )
    noun = "label" if count == 1 else "labels"
    return (
        "Removing both threshold-meeting oracle cases left "
        f"{count} material primary {noun}."
    )


def transition_abstract_text(transition: dict[str, object]) -> str:
    level_a_cases = level_a_case_ids(transition)
    if not level_a_cases:
        return (
            "No case had Level A transition evidence; only native-unit "
            "break-even ceilings are identified."
        )
    return (
        "Level A transition evidence was available for "
        f"{', '.join(level_a_cases)}, but no transition-adjusted estimate is "
        "reported without an explicit, audited implementation model."
    )


def transition_limitations_text(transition: dict[str, object]) -> str:
    level_a_cases = level_a_case_ids(transition)
    if not level_a_cases:
        return (
            "Level B permits threshold analysis only, while Level C supports "
            "no case inference; consequently only native-unit break-even "
            "ceilings—not transition-adjusted point estimates—are reported."
        )
    return (
        "Level B permits threshold analysis only, while Level C supports no "
        "case inference. Level A evidence is available for "
        f"{', '.join(level_a_cases)}, but evidence classification alone does "
        "not generate a transition-adjusted estimate; implementation costs, "
        "timing, scale, and uncertainty must be explicitly modeled."
    )


def prior_art_references() -> list[str]:
    matrix = pd.read_csv(
        Path(__file__).resolve().parents[1] / "TFSC_prior_art_matrix.csv"
    )
    cited_ids = {
        "PA001",
        "PA002",
        "PA003",
        "PA004",
        "PA005",
        "PA006",
        "PA007",
        "PA008",
        "PA009",
        "PA010",
        "PA011",
        "PA012",
        "PA013",
        "PA014",
        "PA015",
        "PA016",
        "PA017",
        "PA018",
        "PA019",
        "PA020",
        "PA021",
        "PA022",
        "PA023",
        "PA024",
        "PA025",
        "PA026",
        "PA027",
        "PA028",
        "PA029",
        "PA030",
        "PA031",
        "PA032",
    }
    references = []
    for row in matrix[matrix["reference_id"].isin(cited_ids)].itertuples():
        authors = str(row.authors).replace(";", ",")
        references.append(
            f"{authors} ({int(row.year)}). {row.title}. {row.container}. "
            f"https://doi.org/{row.doi}"
        )
    institutional = [
        "Food and Agriculture Organization of the United Nations (2025). Crop evapotranspiration: Guidelines for computing crop water requirements, revised edition. FAO Irrigation and Drainage Paper 56 Rev.1.",
        "International Organization for Standardization (n.d.). Systematic Review. ISO/TC 211 good-practice guidance. https://committee.iso.org/sites/tc211/home/resolutions/isotc-211-good-practices/--systematic-review.html",
        "International Organization for Standardization (2007). ISO 216:2007 Writing paper and certain classes of printed matter—Trimmed sizes—A and B series, and indication of machine direction. https://www.iso.org/standard/36631.html",
        "International Organization for Standardization (2020). ISO 668:2020 Series 1 freight containers—Classification, dimensions and ratings. https://www.iso.org/standard/76912.html",
        "National Aeronautics and Space Administration (n.d.). C-MAPSS turbofan engine degradation simulation data. https://data.nasa.gov/docs/legacy/CMAPSSData.zip",
        "National Aeronautics and Space Administration POWER Project (n.d.). Daily agricultural meteorology for Davis, California, 2015–2024. https://power.larc.nasa.gov/",
        "New York City Department of Transportation (n.d.). Traffic Volume Counts (Historical). https://data.cityofnewyork.us/d/btm5-ppia",
        "Open Power System Data (2020). Time series, 60-minute single-index data package, version 2020-10-06. https://data.open-power-system-data.org/time_series/2020-10-06/",
        "Paul W. Witherell, Sudarsan Rachuri, Anantha Narayanan Narayanan, Jae H. Lee (2013). FACTS: A Framework for Analysis, Comparison, and Test of Standards. NISTIR 7935. https://doi.org/10.6028/NIST.IR.7935",
        "UCI Machine Learning Repository (2024). Occupancy Detection [Dataset]. https://doi.org/10.24432/C5X01N",
        "United States Federal Highway Administration (2008). Traffic Signal Timing Manual. FHWA-HOP-08-024.",
    ]
    references.extend(institutional)
    return sorted(references, key=str.casefold)


def add_title_and_abstract(document, values, transition) -> None:
    title = document.add_heading(TITLE, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_paragraph(
        document,
        "Abstract",
        bold_lead="Abstract",
    )
    abstract = (
        "Technological capability can expand feasible sensing, prediction, computation, "
        "communication, and control, but a static technical advantage does not establish "
        "that a persistent standard is inefficient or should be redesigned. We present a "
        "pre-specified, reproducible Legacy Standard Audit separating a historically "
        "defensible incumbent problem—without assuming historical optimality—a current "
        "case-specific frictionless benchmark, and a transition-evidence gate. We screened "
        f"{display(values, 'DESIGN_CANDIDATES')} candidates in "
        f"{display(values, 'DESIGN_DOMAINS')} domains and froze "
        f"{display(values, 'DESIGN_FROZEN_CASES')} heterogeneous cases before confirmatory "
        "estimation, preserving null and insufficient-evidence outcomes. Simulated "
        "perfect-remaining-life maintenance and a perfect-weather reference-crop comparison "
        "met pre-specified material-mismatch thresholds. Perfect-label lighting and bounded "
        "fixed-price load shifting remained small or uncertain; a traffic delay proxy and "
        "container compatibility were insufficient, while repeated-halving geometry returned "
        "the narrow analytic null. Objectives and units differ, so results are not pooled "
        "and do not estimate a population rate. "
        f"{strongest_case_abstract_text(values)} "
        f"{transition_abstract_text(transition)} Documented capability change can "
        "therefore trigger re-audit, whereas redesign requires case-compatible implementation, "
        "safety, network, and regulatory evidence."
    )
    add_paragraph(document, abstract)
    add_paragraph(
        document,
        "Keywords: standards; path dependence; technological change; adaptive control; "
        "switching costs; reproducibility; technology governance",
    )


def add_introduction(document, values) -> None:
    document.add_heading("1. Introduction", level=1)
    add_paragraph(
        document,
        "Standards coordinate expectations, reduce interface uncertainty, and permit "
        "complementary investment. Those same benefits can make an incumbent persistent "
        "after the problem environment changes. Research on dominant designs and "
        "technological trajectories explains how technologies stabilize and later face "
        "discontinuities (Utterback and Abernathy, 1975; Dosi, 1982; Abernathy and Clark, "
        "1985; Tushman and Anderson, 1986; Henderson and Clark, 1990). Research on "
        "increasing returns, compatibility, and infrastructure lock-in explains why "
        "persistence can remain privately or socially rational (Farrell and Saloner, "
        "1985; Arthur, 1989; Liebowitz and Margolis, 1995; Pierson, 2000; Unruh, 2000). "
        "The analytical error is "
        "therefore not persistence itself, but inferring either efficiency or "
        "inefficiency from persistence without reconstructing the decision problem.",
    )
    add_paragraph(
        document,
        "Digital technologies sharpen this problem. Cheap sensing, computation, "
        "communication, and adaptive control can relax information constraints that once "
        "favored fixed schedules, fixed intervals, or static allocations. Digital "
        "innovation also changes architectures and organizing logics rather than merely "
        "improving a component (Yoo et al., 2010; Nambisan et al., 2017). Yet "
        "real-time information does not erase compatibility, investment, safety, "
        "regulation, or collective-action costs. Standards scholarship accordingly "
        "shows that dominance depends on installed bases, participation, governance, and "
        "the interaction between standardization and innovation (Allen and Sriram, 2000; "
        "Suarez, 2004; Wiegmann et al., 2017; van de Kaa et al., 2018; Blind et al., "
        "2022, 2023).",
    )
    add_paragraph(
        document,
        "This article contributes a pre-specified measurement and governance protocol. "
        "It does not offer a new general theory of lock-in. Instead, it operationalizes "
        "a question that spans standards economics, technological transitions, and "
        "adaptive systems: when a technology changes the feasible information or control "
        "set, how should an incumbent standard be re-audited without selecting only "
        "striking examples or forcing a redesign conclusion? The protocol estimates "
        "case-specific static benchmark gaps and applies a separate transition-evidence "
        "gate, preserves null and "
        "insufficient-evidence cases, and forbids pooling outcomes with incomparable "
        "objectives.",
    )
    add_paragraph(
        document,
        "The protocol is not a claim to have invented standards review. ISO systematic "
        "review already supports confirmation, revision or amendment, and withdrawal, "
        "while the NIST FACTS framework analyzes standards across lifecycle, stakeholder, "
        "implementation, comparison, and testing perspectives (International Organization "
        "for Standardization, n.d.; Witherell et al., 2013). The narrower distinction here "
        "is an empirical evidence sequence linking a documented capability change to a "
        "case-specific static benchmark and then to a separate redesign gate.",
    )
    add_paragraph(
        document,
        "We make three bounded contributions. First, the protocol freezes case selection, "
        "comparators, thresholds, raw-input provenance, and null retention before "
        "confirmatory estimation. Second, it separates static benchmark evidence from a "
        "graded transition-evidence gate, preventing technical improvement from becoming "
        "an automatic redesign recommendation. Third, the heterogeneous frozen cases test "
        "whether the common audit architecture remains usable across non-common objectives "
        "without pooling magnitudes or claiming population prevalence. The cases are "
        "present-day audit demonstrations, not reconstructions of historical optima.",
    )


def add_theory(document) -> None:
    document.add_heading("2. Theory and audit propositions", level=1)
    add_paragraph(
        document,
        "Path dependence can arise through increasing returns and coordination, but "
        "historical persistence alone does not establish market failure. Critical work "
        "on escape from lock-in and technological trajectories emphasizes that incumbent "
        "systems may be difficult to displace even when alternatives improve (Cowan and "
        "Hultén, 1996; Dolfsma and Leydesdorff, 2009; Heinrich, 2014). Sociological and "
        "organizational accounts add that standards are enacted through practices and "
        "institutions rather than imposed as purely technical rules (Orlikowski, 1992; "
        "Timmermans and Epstein, 2010). Exploration and exploitation create a related "
        "governance tension: reassessment has option value, but continual change can "
        "destroy coordination value (March, 1991).",
    )
    add_paragraph(
        document,
        "Transition research frames system change as a co-evolution of technology, "
        "institutions, infrastructure, and user practices (Geels, 2002, 2004, 2005). "
        "Governance experiments can reveal transition conditions, but their success is "
        "contextual (Bos and Brown, 2012). Standards participation and policy further "
        "shape whose objectives and constraints enter a redesign process (Choung et al., "
        "2012; Blind and von Laer, 2022). Consumer switching research likewise shows that "
        "comparative technical value is only one component of adoption (Kamolsook et al., "
        "2019).",
    )
    add_paragraph(
        document,
        "The framework yields five falsifiable expectations. First, where source evidence "
        "supports information scarcity as a plausible generating constraint, fixed rules "
        "should show larger static mismatch when reliable real-time control becomes "
        "feasible. Second, a responsive comparator should rank "
        "better under the specified objective only when information and control gains exceed error and "
        "implementation costs. Third, non-technological changes such as demand, prices, "
        "demography, and regulation may explain apparent mismatch and must be modeled or "
        "named. Fourth, network and switching costs can rationally preserve an incumbent "
        "despite a positive frictionless benchmark gap. Fifth, some inherited standards "
        "should remain aligned with their specified objective and appear as null controls.",
    )


def add_framework(document, table_specs) -> None:
    document.add_heading("3. The Legacy Standard Audit", level=1)
    add_paragraph(
        document,
        "Let the incumbent be $x_{inc}$. The historical optimum $x_{h}^{*}$ minimizes loss "
        "under the historical feasible set and parameters; the current frictionless optimum "
        "$x_{c}^{*}$ minimizes current loss without switching costs; and the "
        "transition-adjusted optimum $x_{T}^{*}$ adds switching, compatibility, and "
        f"coordination costs. {figure_label('audit_framework')} shows the resulting "
        "decision sequence.",
    )
    add_paragraph(
        document,
        "Here $x_{h}^{*}$ is a conceptual benchmark, not an empirical assumption that "
        "$x_{inc} = x_{h}^{*}$. If the historical objective, feasible set, or chronology cannot be "
        "verified, the audit records only a historically defensible incumbent problem "
        "and classifies the historical optimum as unidentified.",
    )
    add_display_math(document, r"x_{h}^{*} = \argmin_{x ∈ X_{h}} L_{h}(x; θ_{h})")
    add_display_math(document, r"x_{c}^{*} = \argmin_{x ∈ X_{c}} L_{c}(x; θ_{c})")
    add_display_math(
        document,
        r"x_{T}^{*} = \argmin_{x ∈ X_{c}} [L_{c}(x; θ_{c}) + C_{switch}(x_{inc}, x)]",
    )
    add_display_math(
        document,
        r"R_{static} = L_{c}(x_{inc}; θ_{c}) − L_{c}(x_{c}^{*}; θ_{c})",
    )
    add_figure(
        document,
        figure_path("audit_framework"),
        f"{figure_label('audit_framework')}. Legacy Standard Audit. Technological change can trigger reassessment; "
        "a redesign recommendation requires case-compatible transition evidence.",
    )
    add_paragraph(
        document,
        f"{tab('audit_framework')} defines the five audit stages. A case can show a positive static benchmark "
        "gap and still retain the incumbent if discounted gains do not exceed conversion, "
        "coordination, stranded-asset, safety, or regulatory costs. Conversely, a null "
        "case is informative because it demonstrates that persistence need not indicate "
        "technological inertia.",
    )
    _, headers, rows, caption = table_specs[0]
    add_table(document, headers, rows, caption)


def add_methods(document, values, results, table_specs) -> None:
    config = json.loads((OUTPUT.parent / "analysis_config.json").read_text(encoding="utf-8"))
    document.add_heading("4. Data and pre-specified methods", level=1)
    add_paragraph(
        document,
        "Candidate selection preceded confirmatory estimation. The registry covered the "
        "built environment, transport, automotive interfaces, work, education, "
        "healthcare, packaging, paper and digital legacies, utilities, household and "
        "demographic systems, information-scarcity systems, and null controls. Screening "
        "used historical evidence, technology relevance, decision clarity, public-data "
        "availability, identifiability, counterfactual feasibility, transition-cost "
        "feasibility, source quality, and comparability. The frozen roles "
        "were four primary cases, one supplementary case, one network control, and one "
        "analytic null control. The candidate universe, scoring protocol, case roles, "
        "comparators, thresholds, and analysis configuration were fixed before "
        "confirmatory outputs were estimated; no case was replaced after its result was known.",
    )
    add_paragraph(
        document,
        f"The candidate universe contained {display(values, 'DESIGN_CANDIDATES')} "
        f"candidates in {display(values, 'DESIGN_DOMAINS')} domains, and "
        f"{display(values, 'DESIGN_FROZEN_CASES')} cases were frozen before confirmatory "
        "estimation. Scoring excluded expected effect direction, magnitude, statistical "
        "significance, and narrative usefulness. The frozen case set is stored as a "
        "machine-readable artifact with its own hash and the hash of every input it "
        "references, so later changes to roles or sources are detectable.",
    )
    add_paragraph(
        document,
        "Every public input was saved as a local raw snapshot and registered with its "
        "URL, identifier, version, access time, retrieval conditions, file size, SHA-256 "
        "hash, terms, and completeness. Raw inputs were not overwritten. Analysis "
        "configuration, random seed, and bootstrap settings were fixed in a machine-"
        "readable configuration. Temporal uncertainty used circular block resampling, "
        "except that UI09 drew non-circular blocks wholly contained within annual growing "
        "seasons; the C-MAPSS engine was the independent simulation unit. A copyrighted "
        "ISO 216 sample is retained locally for verification and excluded from the public "
        "repository.",
    )
    add_paragraph(
        document,
        "Classifications were operational decision labels rather than significance tests. "
        "BE03 required the lower uncertainty bound to exceed "
        f"{display(values, 'THRESHOLD_BE03')} with no labeled occupied false-off events; "
        "WK07 required a positive lower regret bound and relative regret above "
        f"{display(values, 'THRESHOLD_WK07')}; UI09 required the lower normalized-regret "
        f"bound to exceed {display(values, 'THRESHOLD_UI09')}. UI01 remained uncertain "
        "because response and equilibrium were not identified, while TR01 and NC01 "
        "required incumbent and transition evidence unavailable in the registered sources. "
        "The thresholds organize the frozen audit and are not universal welfare criteria.",
    )
    add_paragraph(
        document,
        "Case-specific analytical rules were fixed as follows; their sources are listed "
        "at the end of this subsection.",
    )
    schedule = config["BE03"]
    add_paragraph(
        document,
        "BE03 parses the UCI occupancy file row-wise; "
        f"{results['BE03']['invalid_repeated_header_rows_removed']} embedded repeated header "
        "rows fail timestamp and occupancy conversion and are removed from the processed "
        "table without altering the raw file. The incumbent is a weekday "
        f"{schedule['schedule_start_hour']:02d}:00–{schedule['schedule_end_hour']:02d}:00 "
        "nominal lighting schedule, and the schedule sensitivity settings are "
        f"{join_settings([s.replace('-', '–') for s in sensitivity_settings(values, 'BE03')])}. "
        "The comparator uses perfect retained occupancy labels with a "
        f"{display(values, 'BE03_HOLD')}-minute rolling hold and is not a deployed sensor policy.",
    )
    add_paragraph(
        document,
        "WK07 uses NASA C-MAPSS FD001 simulated run-to-failure trajectories. Training "
        "lifetime is the maximum observed cycle of each training engine; evaluation "
        "lifetime is the maximum observed test cycle plus the supplied remaining useful "
        "life. A renewal cost rate with preventive cost "
        f"{config['WK07']['preventive_cost']} and failure-cost ratio "
        f"{config['WK07']['failure_cost_ratio']} selects the fixed replacement age on the "
        "training simulation. The comparator replaces each evaluation engine "
        f"{config['WK07']['condition_lead_cycles']} cycles before failure with perfect "
        "remaining-life information.",
    )
    add_paragraph(
        document,
        "UI01 retains Germany-Luxembourg hourly load and day-ahead prices only for complete "
        "24-hour UTC days. Within each day, a bounded fraction of observed hourly load "
        f"({config['UI01']['primary_flexible_fraction']:.0%}, applied as a symmetric "
        "hourly bound) is shifted toward lower observed prices while daily energy is "
        "conserved. Prices are held fixed; the procedure is neither a retail-tariff "
        "response model nor a market re-equilibration.",
    )
    add_paragraph(
        document,
        "UI09 calculates daily FAO-56 reference evapotranspiration from NASA POWER "
        "temperature, humidity, wind, radiation, precipitation, latitude, and elevation, "
        "after converting shortwave radiation from kWh m^{−2} day^{−1} to MJ m^{−2} "
        "day^{−1}. Weekly net requirement is non-negative evapotranspiration minus "
        f"precipitation within the {config['UI09']['growing_season_start']} to "
        f"{config['UI09']['growing_season_end']} (month-day) growing season. The calendar "
        f"rule is the training-period ({config['UI09']['training_years'][0]}–"
        f"{config['UI09']['training_years'][-1]}) median weekly requirement, evaluated "
        f"in {config['UI09']['evaluation_years'][0]}–{config['UI09']['evaluation_years'][-1]} "
        "against perfect-weather weekly requirements with a shortfall penalty of "
        f"{config['UI09']['shortfall_penalty']}. Bootstrap blocks are wholly contained "
        "within one growing season and never cross the excluded winter gap.",
    )
    add_paragraph(
        document,
        "TR01 selects, by a deterministic rule, the traffic-count segment with the most "
        "days observed in both directions of one axis, using the segment identifier as "
        "the tie-breaker. Training estimates a fixed directional allocation, and "
        "evaluation compares it with hourly demand-proportional allocation using a convex "
        "saturation-delay proxy; this is not a deployed signal model. NC01 and NC03 "
        "test, respectively, an unquantified compatibility case and an exact geometric null.",
    )
    add_paragraph(
        document,
        "Source attribution "
        "is UCI Machine Learning Repository (2024) for BE03, National Aeronautics and "
        "Space Administration (n.d.) for WK07, Open Power System Data (2020) for UI01, "
        "Food and Agriculture Organization of the United Nations (2025) and National "
        "Aeronautics and Space Administration POWER Project (n.d.) for UI09, United "
        "States Federal Highway Administration (2008) and New York City Department of "
        "Transportation (n.d.) for TR01, and International Organization for "
        "Standardization (2007, 2020) for the controls.",
    )
    add_paragraph(
        document,
        f"{tab('case_design')} lists the analysis unit, comparator, and primary threat to interpretation "
        "for each frozen case. These limitations are part of the result rather than "
        "post-estimation caveats.",
    )
    _, headers, rows, caption = table_specs[1]
    add_table(document, headers, rows, caption)


def add_results(document, values, table_specs) -> None:
    document.add_heading("5. Results", level=1)
    add_paragraph(
        document,
        f"BE03 retained {display(values, 'BE03_OBSERVATIONS')} valid minute-observations "
        "after removing embedded repeated header rows. The perfect-label occupancy comparator "
        f"reduced nominal on-time by {display(values, 'BE03_ENERGY_REDUCTION')} "
        f"(95% block interval {interval(values, 'BE03_ENERGY_REDUCTION')}) while both "
        "policies had zero occupied false-off observations under the retained labels. "
        "The result was classified as small or uncertain because schedule choice strongly "
        "changed the estimate and deployment costs and sensor errors were unavailable.",
    )
    add_paragraph(
        document,
        f"WK07 selected a fixed replacement age of {display(values, 'WK07_FIXED_AGE')} "
        "cycles on the training simulation. In the evaluation simulation, the fixed "
        f"policy cost rate was {display(values, 'WK07_FIXED_RATE')} and the perfect-remaining-life "
        f"condition rate was {display(values, 'WK07_CONDITION_RATE')}, yielding static "
        f"regret {display(values, 'WK07_STATIC_REGRET')} normalized cost per cycle "
        f"(95% interval {interval(values, 'WK07_STATIC_REGRET')}) and relative regret "
        f"{display(values, 'WK07_RELATIVE_REGRET')}. This simulated oracle comparison met "
        "the pre-specified material-mismatch threshold; it is not observed fleet savings.",
    )
    add_paragraph(
        document,
        f"UI01 retained {display(values, 'UI01_COMPLETE_DAYS')} complete days. With "
        f"{display(values, 'UI01_FLEXIBLE_FRACTION')} of each hourly load available for "
        "bounded intraday reallocation, the fixed-price arithmetic saving was "
        f"EUR {display(values, 'UI01_SAVINGS_PER_MWH')} per MWh of baseline load "
        f"(95% block interval {interval(values, 'UI01_SAVINGS_PER_MWH')}), equal to "
        f"{display(values, 'UI01_COST_REDUCTION')} of baseline procurement cost. The "
        "small estimate, fixed-price assumption, and absence of customer response support "
        "a small-or-uncertain classification.",
    )
    add_paragraph(
        document,
        f"UI09 used {display(values, 'UI09_TRAINING_WEEKS')} training and "
        f"{display(values, 'UI09_EVALUATION_WEEKS')} evaluation weeks. The calendar "
        f"application was {display(values, 'UI09_CALENDAR_APPLICATION')} mm/week, compared "
        f"with a perfect-weather reference-crop mean of "
        f"{display(values, 'UI09_ADAPTIVE_APPLICATION')} mm/week. "
        f"Normalized objective regret was {display(values, 'UI09_OBJECTIVE_REGRET')} "
        f"(95% block interval {interval(values, 'UI09_OBJECTIVE_REGRET')}). The result "
        "met the pre-specified material-mismatch threshold across loss-weight checks, but "
        "it is a reference-crop, perfect-weather oracle with omitted agronomic constraints; "
        "the objective gap is not physical water savings.",
    )
    add_paragraph(
        document,
        f"TR01 retained {display(values, 'TR01_EVALUATION_DAYS')} evaluation days and "
        f"produced a {display(values, 'TR01_PROXY_REDUCTION')} reduction in a directional "
        f"delay proxy (95% block interval {interval(values, 'TR01_PROXY_REDUCTION')}). "
        "Because the data do not establish an intersection, incumbent timing plan, "
        "pedestrian constraints, queues, saturation flows, or safety outcomes, the case "
        "remained insufficient evidence. NC01 also remained unquantified. NC03 returned "
        f"the exact positive repeated-halving ratio {display(values, 'NC03_OPTIMAL_RATIO')} "
        "with numerically zero loss for that narrow objective.",
    )
    add_paragraph(
        document,
        f"{figure_label('primary_case_benchmarks')} reports primary-case benchmarks on "
        "separate scales to prevent false comparability. "
        f"{tab('case_results')} reports the corresponding classifications.",
    )
    add_figure(
        document,
        figure_path("primary_case_benchmarks"),
        f"{figure_label('primary_case_benchmarks')}. Frozen primary-case technical benchmarks. Each panel uses a "
        "case-specific objective and scale; estimates are not pooled.",
    )
    _, headers, rows, caption = table_specs[2]
    add_table(document, headers, rows, caption)
    add_paragraph(
        document,
        f"{figure_label('model_sensitivity')} reports every pre-specified model or loss "
        "alternative for the four primary cases. Under the alternative fixed schedules, "
        f"the BE03 point estimate ranged from {sensitivity_range(values, 'BE03', True)}, "
        f"spanning the {display(values, 'THRESHOLD_BE03')} material threshold, so the "
        "position of the BE03 point estimate relative to that threshold depends on which "
        f"fixed schedule is treated as the incumbent. WK07 regret ranged from {sensitivity_range(values, 'WK07', False)} "
        "across failure-cost ratios and warning leads, remaining positive in every setting. "
        f"UI01 savings ranged from {sensitivity_range(values, 'UI01', False)} and scaled "
        "with the assumed flexible-load fraction. UI09 normalized regret ranged from "
        f"{sensitivity_range(values, 'UI09', True)} across median or mean calendar rules "
        f"and shortfall penalties, above the {display(values, 'THRESHOLD_UI09')} threshold "
        "in every setting. The alternatives change magnitudes, not the sign of the WK07 "
        "and UI09 gaps; the full parameter grid is released with the code.",
    )
    add_figure(
        document,
        figure_path("model_sensitivity"),
        f"{figure_label('model_sensitivity')}. Pre-specified model sensitivity for the "
        "primary cases. Diamonds mark the pre-specified setting; dashed lines mark "
        "material thresholds where the threshold is defined on the plotted scale. Each "
        "panel uses its own case-specific unit; points are point estimates and are not pooled.",
    )


def add_synthesis(document, values, table_specs) -> None:
    document.add_heading("6. Cross-case synthesis and falsification", level=1)
    add_paragraph(
        document,
        f"{sentence_number(int(numeric(values, 'CROSS_MATERIAL_ORACLE_CASES')))} of "
        f"{display(values, 'CROSS_PRIMARY_CASES')} primary cases met the "
        "pre-specified material-mismatch label under oracle comparison, while the remaining "
        "primary cases were small or uncertain. That count is descriptive; no universal or "
        "pooled effect size was computed. Removing either "
        "threshold-meeting case "
        "reduced the count to one; excluding simulated C-MAPSS evidence also left one. "
        f"Removing both threshold-meeting oracle cases reduced the count to "
        f"{display(values, 'FALS_REMOVE_BOTH_MATERIAL_COUNT')}. The cross-case result "
        "therefore does not establish a stable population rate of mismatch.",
    )
    add_paragraph(
        document,
        "Heterogeneity is a design feature for testing protocol portability, not a basis "
        "for estimating a common effect. Each case retains its own objective function, "
        "denominator, comparator, and native unit. The common architecture consists only "
        "of the technology mechanism, static-evidence state, transition-evidence gate, "
        "and final audit classification. Cross-case synthesis therefore compares audit "
        "states and evidence completeness rather than magnitudes.",
    )
    add_paragraph(
        document,
        f"Exploratory lower classification thresholds increased the primary-case count "
        f"from {display(values, 'FALS_THRESHOLD_CURRENT_COUNT')} to "
        f"{display(values, 'FALS_THRESHOLD_LOW_COUNT')}; the higher explored thresholds "
        f"left it at {display(values, 'FALS_THRESHOLD_HIGH_COUNT')}. As "
        f"{figure_label('model_sensitivity')} showed, supported model and loss alternatives "
        "preserved positive WK07 and UI09 gaps but changed their magnitudes, while BE03 "
        "crossed classification-relevant ranges under alternative fixed schedules. "
        f"{tab('falsification')} collects case removal, domain removal (UI01 and UI09 "
        "share the utilities and infrastructure domain), source-quality, threshold, "
        "model, and control checks in one place. These checks weaken any result-frequency claim but not the "
        "procedural conclusion that evidence state and comparator quality must be audited "
        "case by case.",
    )
    add_paragraph(
        document,
        f"{figure_label('case_classifications')} demonstrates why frozen null and insufficient-evidence cases matter. "
        "The outcomes span all intended categories rather than converging on a redesign "
        "narrative. The strongest evidence is conditional: inexpensive information and "
        "control can create a measurable static benchmark gap under a specified objective, "
        "but redesign recommendations remain unidentified without implementation, "
        "network, safety, and coordination costs. Real-time foresight can improve "
        "preparedness in dynamic networks (Weber et al., 2015), but it cannot substitute "
        "for case-specific institutional evidence.",
    )
    add_figure(
        document,
        figure_path("case_classifications"),
        f"{figure_label('case_classifications')}. Audit-state matrix for all pre-specified frozen cases. Common columns "
        "show technology mechanism and evidence gates; static effect units remain case "
        "specific and are not pooled.",
    )
    _, headers, rows, caption = table_specs[3]
    add_table(document, headers, rows, caption, widths=[1.55, 1.6, 1.15, 2.2])


def add_discussion(document, values) -> None:
    document.add_heading("7. Discussion", level=1)
    add_paragraph(
        document,
        "The central audit lesson is that a documented capability change is a reason to "
        "reassess an incumbent, not evidence that replacement is desirable. Static, "
        "transition, and institutional evidence answer different questions and must not "
        "be collapsed into a single claim of technological improvement.",
    )
    add_paragraph(
        document,
        "The methodological contribution is procedural. A standard should be audited as part "
        "of a decision problem, not as an old object. The procedure begins by stating "
        "a historically defensible incumbent problem and the limits of its reconstruction, "
        "identifies which constraints a "
        "technology plausibly changed, estimates a current technical counterfactual, and "
        "then asks whether transition costs reverse the ranking. This ordering prevents "
        "two symmetric errors: celebrating persistence as evidence of efficiency and "
        "treating a positive static benchmark gap as sufficient evidence for redesign.",
    )
    add_paragraph(
        document,
        "The cases illustrate three technology mechanisms. Occupancy detection and "
        "weather data reduce the cost of sensing current state. Prognostics and interval "
        "metering reduce the cost of computing and communicating condition-dependent "
        "actions. Responsive control changes the feasible frequency of adjustment. Yet "
        "the same cases show why technological capability is not welfare evidence. "
        "Sensor errors, response costs, market equilibrium, crop biology, safety, and "
        "installed-base compatibility can dominate a frictionless gain.",
    )
    add_paragraph(
        document,
        "The empirical demonstration is deliberately heterogeneous. "
        f"{sentence_number(int(numeric(values, 'CROSS_MATERIAL_ORACLE_CASES')))} material labels "
        "depend on perfect-information comparators and are sensitive in magnitude to "
        "retained models or loss functions. "
        f"{strongest_case_abstract_text(values)} "
        "Small, null, and insufficient outcomes are equally consequential "
        "because they show that the protocol does not force a positive redesign narrative.",
    )
    add_paragraph(
        document,
        "For technology governance, the implication is to institutionalize periodic "
        "audits rather than automatic sunset rules. The audit trigger should be a "
        "measurable change in information, control, production, or coordination "
        "conditions. The output should be a transparent classification with an explicit "
        "evidence gap. Regulators and standards bodies can then commission the missing "
        "transition evidence before altering a coordinated system. Multi-mode "
        "standardization and participation research suggests that this process should "
        "include affected implementers and complementors rather than treat the technical "
        "counterfactual as dispositive (Wiegmann et al., 2017; Blind and von Laer, 2022).",
    )
    add_paragraph(
        document,
        "Existing research already explains lock-in, standards battles, transition "
        "governance, digital innovation, and switching behavior. The narrower added value "
        "is the reproducible integration of frozen selection, case-specific benchmarks, "
        "graded transition evidence, controls, and explicit insufficient-evidence states.",
    )


def add_limitations_conclusion(document, values, transition) -> None:
    document.add_heading("8. Limitations", level=1)
    add_paragraph(
        document,
        "First, the analyses do not fully reconstruct the historical optimum for every "
        "case, and they do not assume that any incumbent equals $x_{h}^{*}$. They are frozen "
        "demonstrations of the current-audit stages. Second, four "
        "comparators are oracle or proxy bounds; none identifies a realized causal "
        "deployment effect. Third, the transition audit found "
        f"{display(values, 'TRANSITION_LEVEL_A_SOURCES')} Level A, "
        f"{display(values, 'TRANSITION_LEVEL_B_SOURCES')} Level B, and "
        f"{display(values, 'TRANSITION_LEVEL_C_SOURCES')} Level C sources. "
        f"{transition_limitations_text(transition)} Fourth, the "
        "case set is purposive and heterogeneous, so neither the frequency nor magnitude "
        "of mismatch generalizes to legacy standards as a population. Fifth, uncertainty "
        "intervals quantify sampling variation under the retained model but do not "
        "capture all structural uncertainty. Sixth, the largest normalized result, UI09, "
        "depends on a normative shortfall penalty and omits crop and soil processes.",
    )
    add_paragraph(
        document,
        "Future work should prospectively apply the audit to a second frozen set, acquire "
        "case-specific switching and implementation costs, and validate technical "
        "comparators against deployed controls. A particularly valuable extension would "
        "estimate one full transition-adjusted case from incumbent reconstruction through "
        "realized implementation.",
    )
    document.add_heading("9. Conclusion", level=1)
    add_paragraph(
        document,
        "Technological change can make a fixed standard reassessable without making it "
        "obsolete. The Legacy Standard Audit converts that distinction into a "
        "pre-specified workflow: state a historically defensible incumbent problem, "
        "identify the changed technology constraint, estimate static regret, incorporate transition costs, and "
        "retain null or insufficient-evidence outcomes. In the frozen demonstrations, "
        f"{display(values, 'CROSS_MATERIAL_ORACLE_CASES')} oracle technical comparisons "
        "met pre-specified material-mismatch thresholds, "
        "others were small, one analytic "
        "standard remained exactly aligned with its narrow objective, and a high-network "
        "compatibility case could not be quantified. The defensible conclusion is not "
        "that inherited standards should be replaced. It is that standards governance "
        "should make re-audit reproducible, conditional, and explicit about the evidence "
        "still required for change.",
    )


def add_end_matter(document) -> None:
    document.add_heading("Data and code availability", level=1)
    add_paragraph(
        document,
        "All analysis code, frozen selection records, source registry, checksums, and "
        "generated values are provided in the accompanying repository. Public raw data "
        "are retrieved from registered sources and retained as immutable local snapshots. "
        "Copyrighted ISO sample material is not redistributed; its provenance and local "
        "checksum are recorded. The source registry records each source's URL, "
        "identifier, version, access time, file size, SHA-256 hash, terms, and "
        "completeness; the complete model-sensitivity grid and the unabridged "
        "falsification output are released as machine-readable files. After installing "
        "the pinned dependencies, the command make all regenerates analyses, figures, "
        "tables, manuscript files, and audits, and make test and make audit rerun the "
        "regression tests and integrity checks. The article is self-contained; no "
        "additional file is required to interpret it.",
    )
    document.add_heading(
        "Declaration of generative AI and AI-assisted technologies in the manuscript "
        "preparation process",
        level=1,
    )
    add_paragraph(
        document,
        "During the preparation of this work, the authors used Devin, an AI "
        "software-engineering assistant built by Cognition AI, to support code generation, "
        "document assembly, and consistency checks. After using this tool, the authors "
        "reviewed and edited the content as needed and take full responsibility for the "
        "content of the published article. The AI system is not an author.",
    )
    document.add_heading("Declarations", level=1)
    add_paragraph(
        document,
        "Funding: [AUTHOR ACTION REQUIRED: confirm the funding statement before submission.]",
    )
    add_paragraph(
        document,
        "Competing interests: [AUTHOR ACTION REQUIRED: complete Elsevier's declarations "
        "tool and insert the confirmed statement before submission.]",
    )
    add_paragraph(document, "Ethics: The study uses public secondary data and simulations; no human participants were recruited.")
    document.add_heading("References", level=1)
    for reference in prior_art_references():
        add_paragraph(document, reference)


def build_title_page() -> None:
    document = configured_document()
    title = document.add_heading(TITLE, 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    document.add_paragraph()
    add_paragraph(document, "Article type: Full-length research article")
    add_paragraph(document, "Authors: [To be supplied by the submitting author]")
    add_paragraph(document, "Affiliations: [To be supplied]")
    add_paragraph(document, "Corresponding author: [Name, postal address, and email to be supplied]")
    add_paragraph(document, f"Tables: {len(TABLE_ORDER)}")
    add_paragraph(document, f"Figures: {len(FIGURE_ORDER)}")
    add_paragraph(document, "Acknowledgements: [To be supplied or confirmed as none]")
    add_paragraph(document, "Funding: [To be supplied or confirmed as none]")
    add_paragraph(document, "Competing interests: [To be supplied from Elsevier's declarations tool]")
    add_paragraph(document, "CRediT author statement: [To be supplied]")
    add_paragraph(document, "Author biographies (maximum 100 words each): [To be supplied]")
    add_paragraph(
        document,
        "Author details are intentionally not inferred from repository or account metadata.",
    )
    document.save(MANUSCRIPT_DIR / "title_page.docx")


def convert_to_pdf(path: Path) -> None:
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(path.parent),
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    MANUSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    values = load_values()
    results = load_results()
    transition = json.loads(
        (OUTPUT / "analysis" / "transition_evidence_results.json").read_text(
            encoding="utf-8"
        )
    )
    table_specs = tables(values, results)
    document = configured_document()
    add_page_number(document)
    add_title_and_abstract(document, values, transition)
    add_introduction(document, values)
    add_theory(document)
    add_framework(document, table_specs)
    add_methods(document, values, results, table_specs)
    add_results(document, values, table_specs)
    add_synthesis(document, values, table_specs)
    add_discussion(document, values)
    add_limitations_conclusion(document, values, transition)
    add_end_matter(document)
    manuscript_path = MANUSCRIPT_DIR / "manuscript_anonymized.docx"
    document.save(manuscript_path)
    build_title_page()
    convert_to_pdf(manuscript_path)
    print("Wrote anonymized manuscript, title page, and manuscript PDF")


if __name__ == "__main__":
    main()
