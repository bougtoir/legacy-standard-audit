import subprocess

import pandas as pd

from make_tables import tables
from publication_utils import (
    OUTPUT,
    add_figure,
    add_page_number,
    add_table,
    configured_document,
    display,
    load_results,
    load_values,
)


SUPPLEMENT_DIR = OUTPUT / "supplement"


def add_text(document, text: str) -> None:
    document.add_paragraph(text)


def main() -> None:
    SUPPLEMENT_DIR.mkdir(parents=True, exist_ok=True)
    values = load_values()
    results = load_results()
    specifications = tables(values, results)
    document = configured_document()
    add_page_number(document)
    document.add_heading("Supplementary material", 0)
    add_text(
        document,
        "Legacy standards as frozen solutions to obsolete optimization problems: "
        "a framework for technological change and adaptive re-optimization",
    )
    document.add_heading("S1. Pre-specification and frozen selection", level=1)
    add_text(
        document,
        f"The candidate universe contained {display(values, 'DESIGN_CANDIDATES')} "
        f"candidates in {display(values, 'DESIGN_DOMAINS')} domains. "
        f"{display(values, 'DESIGN_FROZEN_CASES')} roles were frozen before confirmatory "
        "estimation. The artifact hash and every input hash are stored in "
        "frozen_case_set.json and frozen_case_set.sha256. Expected effect direction, "
        "magnitude, significance, and narrative usefulness were excluded from scoring.",
    )
    document.add_heading("S2. Source preservation", level=1)
    add_text(
        document,
        "Public analysis inputs were saved under data/raw before use. SOURCE_REGISTRY.csv "
        "records URL, identifier, version or date, UTC access time, retrieval conditions, "
        "local path, file size, SHA-256, terms, completeness, and notes. Existing raw "
        "snapshots are never overwritten. A copyrighted ISO 216 sample is retained "
        "locally for verification but excluded from the public Git repository.",
    )
    registry = pd.read_csv(
        OUTPUT.parent / "SOURCE_REGISTRY.csv"
    )
    case_sources = registry[
        registry["case_id"].isin(["BE03", "WK07", "UI01", "UI09", "TR01", "NC01", "NC03"])
    ][["case_id", "source_id", "title", "identifier", "sha256"]].copy()
    case_sources["sha256"] = case_sources["sha256"].str[:12]
    case_sources.columns = ["Case", "Source ID", "Title", "Identifier", "SHA-256 prefix"]
    add_table(
        document,
        case_sources.columns.tolist(),
        case_sources.fillna("").values.tolist(),
        "Table S2. Registered case-specific evidence and data sources.",
    )
    document.add_heading("S3. Detailed analytical rules", level=1)
    add_text(
        document,
        "BE03. The UCI CSV is parsed row-wise. Two embedded header rows fail timestamp "
        "and occupancy conversion and are removed from the processed analysis table; the "
        "raw file is not altered. Fixed schedules are evaluated at 06:00–20:00, "
        "07:00–19:00, and 08:00–18:00. The adaptive policy is an oracle rolling occupancy "
        "indicator with the configured hold.",
    )
    add_text(
        document,
        "WK07. Training lifetime is the maximum observed cycle for each FD001 training "
        "unit. Evaluation lifetime is maximum observed test cycle plus the supplied "
        "remaining useful life. A renewal cost rate selects fixed replacement age in the "
        "training simulation. The comparator replaces each evaluation unit a configured "
        "number of cycles before failure with perfect information.",
    )
    add_text(
        document,
        "UI01. Germany-Luxembourg hourly load and day-ahead prices are retained only for "
        "complete 24-hour UTC days. Flexible energy is shifted within each day, bounded "
        "symmetrically by the configured fraction of observed hourly load, while daily "
        "energy is conserved. The procedure holds prices fixed and is not a retail-tariff "
        "response model.",
    )
    add_text(
        document,
        "UI09. Daily FAO-56 reference evapotranspiration is calculated from NASA POWER "
        "temperature, humidity, wind, radiation, precipitation, latitude, and elevation. "
        "Shortwave radiation is converted from kWh m−2 day−1 to MJ m−2 day−1 before "
        "the FAO-56 calculation. "
        "Weekly net requirement is non-negative evapotranspiration minus precipitation. "
        "The calendar rule uses the training-period median; sensitivity also uses the "
        "mean and multiple shortfall penalties. Each bootstrap block is wholly contained "
        "within one annual growing season and cannot cross the excluded winter gap.",
    )
    add_text(
        document,
        "TR01. The deterministic segment rule selects the segment with the greatest "
        "number of days having both NB/SB or EB/WB observations, with segment identifier "
        "as the tie-breaker. Training estimates a fixed directional allocation. "
        "Evaluation compares it with hourly demand-proportional allocation using a convex "
        "saturation-delay proxy. This is not a deployed signal model.",
    )
    document.add_heading("S4. Model sensitivity", level=1)
    _, headers, rows, caption = specifications[4]
    add_table(document, headers, rows, caption)
    add_figure(
        document,
        OUTPUT / "figures" / "Figure_S1_model_sensitivity.png",
        "Figure S1. Pre-specified model sensitivity. Each panel uses its own scale.",
    )
    document.add_heading("S5. Cross-case falsification", level=1)
    add_text(
        document,
        "The analyses do not compute a universal effect size. Leave-one-case-out is also "
        "leave-one-domain-out because each primary case represents a distinct domain. A "
        "source-quality sensitivity excludes the simulated C-MAPSS case. The negative "
        "controls retain the exact repeated-halving null and the unquantified container "
        "compatibility case.",
    )
    falsification = pd.read_csv(
        OUTPUT / "analysis" / "cross_case_falsification.csv"
    )
    add_table(
        document,
        falsification.columns.tolist(),
        falsification.fillna("").values.tolist(),
        "Table S3. Full cross-case falsification output.",
    )
    document.add_heading("S6. Reproduction", level=1)
    add_text(
        document,
        "From the project root, create an environment from requirements.lock and run "
        "`make all`, `make test`, and `make audit`. Generated case-level processed files "
        "are written under outputs/analysis. The manuscript, supplement, figures, tables, "
        "and submission archive are regenerated without manual transcription.",
    )
    path = SUPPLEMENT_DIR / "supplement.docx"
    document.save(path)
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(SUPPLEMENT_DIR),
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print("Wrote supplement DOCX and PDF")


if __name__ == "__main__":
    main()
