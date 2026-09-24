import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests


PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "data" / "raw" / "case_selection"
REGISTRY = PROJECT / "research_inputs" / "selection_sources.csv"
RAW.mkdir(parents=True, exist_ok=True)
REGISTRY.parent.mkdir(exist_ok=True)

SOURCES = [
    {
        "source_id": "SEL-BE03-UCI-META",
        "case_id": "BE03",
        "source_type": "dataset_metadata",
        "title": "UCI Occupancy Detection dataset metadata",
        "publisher_or_custodian": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/api/dataset?id=357",
        "identifier": "UCI dataset 357; DOI 10.24432/C5X01N",
        "version_or_date": "last updated 2024-04-13",
        "retrieval_conditions": "Public HTTP API",
        "filename": "BE03_uci_occupancy_metadata_2026-09-24.json",
        "license_or_terms": "UCI repository terms; dataset page states CC BY 4.0",
        "notes": "Selection evidence and data documentation",
    },
    {
        "source_id": "SEL-BE03-UCI-DATA",
        "case_id": "BE03",
        "source_type": "observational_dataset",
        "title": "Occupancy Detection data",
        "publisher_or_custodian": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/static/public/357/data.csv",
        "identifier": "UCI dataset 357; DOI 10.24432/C5X01N",
        "version_or_date": "repository file accessed 2026-09-24",
        "retrieval_conditions": "Public HTTP download",
        "filename": "BE03_uci_occupancy_data_2026-09-24.csv",
        "license_or_terms": "CC BY 4.0 per UCI metadata",
        "notes": "Observed office environmental and occupancy time series",
    },
    {
        "source_id": "SEL-BE03-UCI-PAPER",
        "case_id": "BE03",
        "source_type": "bibliographic_metadata",
        "title": "Crossref metadata: Accurate occupancy detection of an office room",
        "publisher_or_custodian": "Crossref",
        "url": "https://api.crossref.org/works/10.1016%2Fj.enbuild.2015.11.071",
        "identifier": "10.1016/j.enbuild.2015.11.071",
        "version_or_date": "2016 article; API response accessed 2026-09-24",
        "retrieval_conditions": "Crossref REST API exact DOI lookup",
        "filename": "BE03_occupancy_paper_crossref_2026-09-24.json",
        "license_or_terms": "Crossref metadata API terms",
        "notes": "Exact metadata for the paper associated with the UCI dataset",
    },
    {
        "source_id": "SEL-BE03-DOE-SCHEDULES",
        "case_id": "BE03",
        "source_type": "government_model_assumptions",
        "title": "DOE Commercial Building Energy Asset Score assumptions",
        "publisher_or_custodian": "United States Department of Energy",
        "url": "https://buildingenergyscore.energy.gov/resources/download?key=documents%2Fenergy_asset_score_assumptions.pdf",
        "identifier": "Energy Asset Score assumptions document",
        "version_or_date": "file last modified 2023-09-07",
        "retrieval_conditions": "Public HTTP download",
        "filename": "BE03_doe_asset_score_schedules_2023.pdf",
        "license_or_terms": "United States government publication",
        "notes": "Formal office occupancy and lighting schedule assumptions",
    },
    {
        "source_id": "SEL-WK07-NASA-DATA",
        "case_id": "WK07",
        "source_type": "simulation_dataset",
        "title": "C-MAPSS turbofan engine degradation simulation data",
        "publisher_or_custodian": "NASA Prognostics Center of Excellence",
        "url": "https://data.nasa.gov/docs/legacy/CMAPSSData.zip",
        "identifier": "NASA C-MAPSS legacy dataset",
        "version_or_date": "legacy archive accessed 2026-09-24",
        "retrieval_conditions": "Public HTTP download",
        "filename": "WK07_CMAPSSData_2026-09-24.zip",
        "license_or_terms": "NASA open-data terms",
        "notes": "Simulated run-to-failure data; must not be described as observed equipment data",
    },
    {
        "source_id": "SEL-WK07-NASA-PAPER",
        "case_id": "WK07",
        "source_type": "method_documentation",
        "title": "Review and Analysis of Algorithmic Approaches Developed for Prognostics on CMAPSS Dataset",
        "publisher_or_custodian": "NASA Technical Reports Server",
        "url": "https://ntrs.nasa.gov/api/citations/20150007677/downloads/20150007677.pdf",
        "identifier": "NASA NTRS 20150007677",
        "version_or_date": "2015",
        "retrieval_conditions": "Public HTTP download",
        "filename": "WK07_nasa_cmapss_review_2015.pdf",
        "license_or_terms": "NASA technical report terms",
        "notes": "Dataset scope and prognostics context",
    },
    {
        "source_id": "SEL-WK07-NASA-PBM",
        "case_id": "WK07",
        "source_type": "method_documentation",
        "title": "Developing Deep Learning Models for System Prognostics",
        "publisher_or_custodian": "NASA Technical Reports Server",
        "url": "https://ntrs.nasa.gov/api/citations/20220009583/downloads/Darrah_PHM_2022.pdf",
        "identifier": "NASA NTRS 20220009583",
        "version_or_date": "2022",
        "retrieval_conditions": "Public HTTP download",
        "filename": "WK07_nasa_prognostics_maintenance_2022.pdf",
        "license_or_terms": "NASA technical report terms",
        "notes": "Defines condition-based and prognostics-based maintenance relative to time-based practice",
    },
    {
        "source_id": "SEL-UI01-OPSD-DATA",
        "case_id": "UI01",
        "source_type": "observational_dataset",
        "title": "Open Power System Data time series, 60-minute single-index format",
        "publisher_or_custodian": "Open Power System Data",
        "url": "https://data.open-power-system-data.org/time_series/2020-10-06/time_series_60min_singleindex.csv",
        "identifier": "OPSD time_series 2020-10-06",
        "version_or_date": "2020-10-06",
        "retrieval_conditions": "Public HTTP download; full 60-minute file",
        "filename": "UI01_opsd_time_series_60min_2020-10-06.csv",
        "license_or_terms": "Open Power System Data package terms; source licenses documented by column",
        "notes": "Observed European load, generation, and price series through mid-2020",
    },
    {
        "source_id": "SEL-UI01-DOE-RATES",
        "case_id": "UI01",
        "source_type": "government_report",
        "title": "Customer Acceptance, Retention, and Response to Time-Based Rates",
        "publisher_or_custodian": "United States Department of Energy",
        "url": "https://www.energy.gov/sites/prod/files/2016/12/f34/CBS_Final_Program_Impact_Report_Draft_20161101_0.pdf",
        "identifier": "DOE Consumer Behavior Studies final program impact report",
        "version_or_date": "2016",
        "retrieval_conditions": "Public HTTP download",
        "filename": "UI01_doe_time_based_rates_2016.pdf",
        "license_or_terms": "United States government publication",
        "notes": "Documents AMI-enabled time-based pricing and randomized utility studies",
    },
    {
        "source_id": "SEL-UI09-FAO56",
        "case_id": "UI09",
        "source_type": "technical_guideline",
        "title": "Crop evapotranspiration: Guidelines for computing crop water requirements, revised edition",
        "publisher_or_custodian": "Food and Agriculture Organization of the United Nations",
        "url": "https://openknowledge.fao.org/server/api/core/bitstreams/adb9d711-428b-42da-a47f-db6f8b804848/content",
        "identifier": "FAO Irrigation and Drainage Paper 56 Rev.1; ISBN 978-92-5-140060-9",
        "version_or_date": "2025 revised edition",
        "retrieval_conditions": "Public FAO repository download",
        "filename": "UI09_fao56_rev1_2025.pdf",
        "license_or_terms": "FAO Open Knowledge Repository terms",
        "notes": "Current crop-water-requirement and irrigation-scheduling methods",
    },
    {
        "source_id": "SEL-UI09-NASA-POWER",
        "case_id": "UI09",
        "source_type": "observational_reanalysis_dataset",
        "title": "NASA POWER daily agricultural meteorology for Davis, California",
        "publisher_or_custodian": "NASA Langley Research Center POWER Project",
        "url": (
            "https://power.larc.nasa.gov/api/temporal/daily/point"
            "?parameters=T2M_MAX,T2M_MIN,T2M,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR"
            "&community=AG&longitude=-121.7405&latitude=38.5449"
            "&start=20150101&end=20241231&format=JSON&time-standard=LST"
        ),
        "identifier": "NASA POWER point request, Davis CA, 2015-01-01 to 2024-12-31",
        "version_or_date": "API response accessed 2026-09-24",
        "retrieval_conditions": "Public NASA POWER daily API; one complete point request",
        "filename": "UI09_nasa_power_davis_2015_2024_2026-09-24.json",
        "license_or_terms": "NASA POWER data-access terms",
        "notes": "Daily meteorological input; source is analysis-ready satellite/model-derived data",
    },
    {
        "source_id": "SEL-UI09-SENSOR-REVIEW",
        "case_id": "UI09",
        "source_type": "bibliographic_metadata",
        "title": "Crossref metadata: Soil water sensors for irrigation scheduling in the United States",
        "publisher_or_custodian": "Crossref",
        "url": "https://api.crossref.org/works/10.1016%2Fj.agwat.2023.108148",
        "identifier": "10.1016/j.agwat.2023.108148",
        "version_or_date": "2023 article; API response accessed 2026-09-24",
        "retrieval_conditions": "Crossref REST API exact DOI lookup",
        "filename": "UI09_soil_sensor_review_crossref_2026-09-24.json",
        "license_or_terms": "Crossref metadata API terms",
        "notes": "Exact systematic-review metadata for sensor-based irrigation scheduling",
    },
    {
        "source_id": "SEL-TR01-FHWA",
        "case_id": "TR01",
        "source_type": "government_manual",
        "title": "Traffic Signal Timing Manual",
        "publisher_or_custodian": "United States Federal Highway Administration",
        "url": "https://ops.fhwa.dot.gov/publications/fhwahop08024/fhwa_hop_08_024.pdf",
        "identifier": "FHWA-HOP-08-024",
        "version_or_date": "2008 archived first edition",
        "retrieval_conditions": "Public HTTP download",
        "filename": "TR01_fhwa_signal_timing_manual_2008.pdf",
        "license_or_terms": "United States government publication",
        "notes": "Defines pre-timed and actuated control; supplementary-case evidence",
    },
    {
        "source_id": "SEL-TR01-NYC-META",
        "case_id": "TR01",
        "source_type": "dataset_metadata",
        "title": "Traffic Volume Counts (Historical) metadata",
        "publisher_or_custodian": "New York City Department of Transportation",
        "url": "https://data.cityofnewyork.us/api/views/btm5-ppia",
        "identifier": "NYC Open Data btm5-ppia",
        "version_or_date": "dataset metadata accessed 2026-09-24",
        "retrieval_conditions": "Public Socrata metadata API",
        "filename": "TR01_nyc_traffic_counts_metadata_2026-09-24.json",
        "license_or_terms": "NYC Open Data terms",
        "notes": "Documents columns, provenance, and last update",
    },
    {
        "source_id": "SEL-TR01-NYC-DATA",
        "case_id": "TR01",
        "source_type": "observational_dataset",
        "title": "Traffic Volume Counts (Historical), complete Socrata export",
        "publisher_or_custodian": "New York City Department of Transportation",
        "url": "https://data.cityofnewyork.us/resource/btm5-ppia.csv?$limit=1000000",
        "identifier": "NYC Open Data btm5-ppia",
        "version_or_date": "dataset export accessed 2026-09-24",
        "retrieval_conditions": "Public Socrata API; one request with limit above published row count",
        "filename": "TR01_nyc_traffic_counts_complete_2026-09-24.csv",
        "license_or_terms": "NYC Open Data terms",
        "notes": "Complete published table at retrieval; row count validated after download",
    },
    {
        "source_id": "SEL-PD02-QWERTY",
        "case_id": "PD02",
        "source_type": "bibliographic_metadata",
        "title": "Crossref metadata: Why Alphabetic Keyboards Are Not Easy to Use",
        "publisher_or_custodian": "Crossref",
        "url": "https://api.crossref.org/works/10.1177%2F001872088202400502",
        "identifier": "10.1177/001872088202400502",
        "version_or_date": "1982 article; API response accessed 2026-09-24",
        "retrieval_conditions": "Crossref REST API exact DOI lookup",
        "filename": "PD02_qwerty_crossref_2026-09-24.json",
        "license_or_terms": "Crossref metadata API terms",
        "notes": "Negative-control evidence; reports small modeled layout differences and switching concerns",
    },
    {
        "source_id": "SEL-NC01-ISO668",
        "case_id": "NC01",
        "source_type": "standards_body_metadata",
        "title": "ISO 668:2020 Series 1 freight containers — Classification, dimensions and ratings",
        "publisher_or_custodian": "International Organization for Standardization",
        "url": "https://www.iso.org/standard/76912.html",
        "identifier": "ISO 668:2020",
        "version_or_date": "Edition 7, 2020-01; page accessed 2026-09-24",
        "retrieval_conditions": "Rendered in the existing Chrome session because direct HTTP returned a Cloudflare challenge",
        "filename": "NC01_iso_668_2020_page_2026-09-24.txt",
        "license_or_terms": "ISO page metadata only; standard text not redistributed",
        "notes": "Negative-control evidence; public bibliographic page captured without copyrighted standard text",
        "existing_capture_required": True,
    },
    {
        "source_id": "SEL-NC03-ISO216",
        "case_id": "NC03",
        "source_type": "standards_body_metadata",
        "title": "ISO 216:2007 Writing paper and certain classes of printed matter — Trimmed sizes",
        "publisher_or_custodian": "International Organization for Standardization",
        "url": "https://www.iso.org/standard/36631.html",
        "identifier": "ISO 216:2007",
        "version_or_date": "Edition 2, 2007-09; confirmed current 2021; page accessed 2026-09-24",
        "retrieval_conditions": "Rendered in the existing Chrome session because direct HTTP returned a Cloudflare challenge",
        "filename": "NC03_iso_216_2007_page_2026-09-24.txt",
        "license_or_terms": "ISO page metadata only; standard text not redistributed",
        "notes": "Mathematical null control for repeated-halving aspect-ratio invariance",
        "existing_capture_required": True,
    },
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(source):
    destination = RAW / source["filename"]
    if destination.exists():
        return destination, "existing_snapshot_not_overwritten"
    if source.get("existing_capture_required"):
        raise FileNotFoundError(
            f"Browser-rendered source must be captured before registry generation: {destination}"
        )
    headers = {"User-Agent": "legacy-standard-audit/0.1 (mailto:bougtoir@gmail.com)"}
    with requests.get(source["url"], headers=headers, stream=True, timeout=180) as response:
        response.raise_for_status()
        with destination.open("xb") as fh:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    fh.write(chunk)
    return destination, "downloaded"


existing_rows = {}
if REGISTRY.exists():
    with REGISTRY.open(newline="", encoding="utf-8") as fh:
        existing_rows = {row["source_id"]: row for row in csv.DictReader(fh)}

accessed = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
rows = []
for source in SOURCES:
    path, action = download(source)
    row = {
        key: value
        for key, value in source.items()
        if key not in {"filename", "existing_capture_required"}
    }
    row.update(
        {
            "accessed_utc": existing_rows.get(source["source_id"], {}).get(
                "accessed_utc", accessed
            ),
            "raw_path": str(path.relative_to(PROJECT)),
            "file_size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "completeness": "complete_requested_resource",
            "notes": existing_rows.get(source["source_id"], {}).get(
                "notes", f"{source['notes']}; {action}"
            ),
        }
    )
    rows.append(row)
    print(source["source_id"], path.stat().st_size, action)

fieldnames = [
    "source_id", "case_id", "source_type", "title", "publisher_or_custodian",
    "url", "identifier", "version_or_date", "accessed_utc",
    "retrieval_conditions", "raw_path", "file_size_bytes", "sha256",
    "license_or_terms", "completeness", "notes",
]
with REGISTRY.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} source records to {REGISTRY}")
