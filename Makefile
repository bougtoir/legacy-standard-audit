PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: all data analysis ledger figures tables manuscript supplement submission audit audit-full-source-archive test clean

all: data analysis figures tables manuscript supplement submission audit

data:
	$(PYTHON) scripts/fetch_data.py
	$(PYTHON) scripts/fetch_analysis_sources.py
	$(PYTHON) scripts/merge_source_registry.py

analysis: data
	$(PYTHON) scripts/run_analysis.py

ledger: analysis
	$(PYTHON) scripts/build_claim_ledger.py

figures: analysis
	$(PYTHON) scripts/make_figures.py

tables: analysis
	$(PYTHON) scripts/make_tables.py

manuscript: ledger figures tables
	$(PYTHON) scripts/build_manuscript.py

supplement: figures tables
	$(PYTHON) scripts/build_supplement.py

submission: manuscript supplement
	$(PYTHON) scripts/build_submission.py

audit: submission
	$(PYTHON) scripts/run_integrity_audit.py

audit-full-source-archive: submission
	LEGACY_STANDARD_AUDIT_REQUIRE_FULL_ARCHIVE=1 $(PYTHON) scripts/run_integrity_audit.py

test:
	$(PYTHON) -m pytest tests -q

clean:
	$(PYTHON) scripts/clean_generated.py
