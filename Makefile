PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)

.PHONY: all data analysis transition falsification ledger figures tables manuscript submission cross-references oracle-language numerical-qc audit audit-full-source-archive test clean

all: data analysis transition falsification figures tables manuscript submission cross-references oracle-language audit

data:
	$(PYTHON) scripts/fetch_data.py
	$(PYTHON) scripts/fetch_analysis_sources.py
	$(PYTHON) scripts/merge_source_registry.py

analysis: data
	$(PYTHON) scripts/run_analysis.py

transition: analysis
	$(PYTHON) scripts/build_transition_evidence.py

falsification: transition
	$(PYTHON) scripts/build_final_falsification.py

ledger: transition falsification
	$(PYTHON) scripts/build_claim_ledger.py

figures: falsification
	$(PYTHON) scripts/make_figures.py

tables: falsification
	$(PYTHON) scripts/make_tables.py

manuscript: ledger figures tables
	$(PYTHON) scripts/build_manuscript.py

submission: manuscript
	$(PYTHON) scripts/build_submission.py

oracle-language: submission
	$(PYTHON) scripts/audit_oracle_language.py

cross-references: submission
	$(PYTHON) scripts/audit_cross_references.py

numerical-qc: submission cross-references
	$(PYTHON) scripts/run_numerical_qc.py

audit: numerical-qc
	$(PYTHON) scripts/run_integrity_audit.py

audit-full-source-archive: numerical-qc
	LEGACY_STANDARD_AUDIT_REQUIRE_FULL_ARCHIVE=1 $(PYTHON) scripts/run_integrity_audit.py

test:
	$(PYTHON) -m pytest tests -q

clean:
	$(PYTHON) scripts/clean_generated.py
