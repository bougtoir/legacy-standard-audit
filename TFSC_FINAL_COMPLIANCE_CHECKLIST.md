# TFSC final compliance checklist

Official TFSC guidance and Elsevier's generative-AI policy were rechecked on
2026-09-24 against persisted raw snapshots in `data/raw/journal_requirements/`.

| Requirement | Status | Final check |
|---|---|---|
| Article type and scope | PASS | Full-length research article with technology-governance focus; select the Technology Governance and Public Policy bureau at submission. |
| Title | PASS | Concise, informative, no unexplained abbreviation, and identical across manuscript, title page, and cover letter. |
| Abstract | PASS | 169 words before the final rebuild; maximum 250. Rechecked automatically. |
| Keywords | PASS | Seven English keywords; permitted range is 1–7. |
| Manuscript word limit | PASS | The current guide states no full-article word limit. |
| Highlights | PASS | Five bullets; each is at most 85 characters; separate editable text file. |
| Graphical abstract | PASS | Optional; supplied separately at 1328×531 pixels with an editable PPTX. |
| Main figures | PASS | Four figures supplied separately as high-resolution PNGs; numbering follows first in-text citation (machine-checked by `scripts/audit_cross_references.py`). |
| Tables | PASS | Four main tables cited in first-citation order; editable DOCX/PPTX tables are supplied. |
| References | PASS | Author–year citations and alphabetical reference list; real-source and DOI checks are automated. |
| Numbered sections and equations | PASS | Main sections are numbered; equations are editable Word (OMML) equations. |
| Double-anonymized review | PASS | Anonymized manuscript and non-anonymized title page are separate; the manuscript has no author placeholders or acknowledgements. |
| Title-page content | AUTHOR ACTION | Supply final authors, affiliations, corresponding-author address/email, acknowledgements, funding, competing interests, CRediT roles, and biographies. |
| Funding | AUTHOR ACTION | Confirm the final wording; do not submit the placeholder. |
| Competing interests | AUTHOR ACTION | Complete Elsevier's declarations tool and upload its DOCX; insert the confirmed statement. |
| Ethics | PASS | Public secondary data and simulations only; no participants were recruited. |
| Data statement | PASS | Separate statement and manuscript section identify repository materials, provenance, checksums, and the copyrighted-data exception. |
| Code and reproducibility | PASS | Canonical one-command build, immutable numerical-input archive, source registry, and machine-executed audits are documented. |
| Generative-AI disclosure | PASS | Uses Elsevier's required section placement and current June 2026 policy elements: tool name, purpose, human review, and responsibility. |
| AI-generated research images | PASS | None. Figures and graphical abstract are reproducible programmatic visualizations or editable schematics. |
| Supplement | PASS | None submitted: essential content was integrated into the main article (see `SUPPLEMENT_INTEGRATION_AUDIT.md`); the full sensitivity grid, falsification output, and source registry are repository files. |
| Cover letter | AUTHOR ACTION | Add submission date and corresponding-author signature; all authors must confirm originality and declarations. |
| Submission files | PASS WITH AUTHOR ACTIONS | Editable manuscript, title page, figures, tables, highlights, cover letter, graphical abstract, and statements are assembled. |

## Official-policy sources

- TFSC Guide for Authors:
  https://www.sciencedirect.com/journal/technological-forecasting-and-social-change/publish/guide-for-authors
- Elsevier generative-AI policies for journals:
  https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals

The current Elsevier policy was updated in June 2026. It requires disclosure when AI supported
manuscript preparation, and it permits reproducible data visualizations derived from underlying
data. The manuscript's disclosure is therefore required and retained.
