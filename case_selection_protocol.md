# Case-selection protocol

## Purpose

Select heterogeneous standards capable of testing technology-mediated
constraint change without selecting on observed effect size.

## Eligibility criteria

A primary case must have:

1. a verifiable incumbent and history of adoption, formalization, or lock-in;
2. a specific technological change that altered the feasible set, information
   structure, control capability, coordination mechanism, or relevant costs;
3. a clear current decision variable and objective;
4. public current data adequate for a reproducible counterfactual;
5. an interpretable incumbent-versus-current comparison;
6. a defensible treatment of uncertainty and material omitted constraints;
7. a feasible switching, coordination, safety, regulatory, or network-cost
   assessment;
8. relevance to technological change and standards governance.

## Exclusions

- Age alone is the rationale.
- Historical objective or rationale cannot be verified.
- The incumbent cannot be validated.
- Current data are private, irretrievable, or legally unsuitable.
- A counterfactual requires invented observations or unverifiable valuation.
- The technological mechanism is decorative rather than material.

## Diversity and controls

The frozen set should cover multiple domains and technology mechanisms. It must
retain at least one plausible null/negative control and should include a
non-technological change comparator where evidence permits.

## Pre-specified scoring

Candidates receive ordinal scores from 0–3 for historical evidence,
technology-mediated relevance, decision clarity, current-data quality,
identifiability, counterfactual feasibility, transition-cost feasibility,
source quality, and cross-case comparability. Safety or legal infeasibility is
an exclusion flag, not a compensable score.

Selection uses evidence and design quality only. Preliminary effect direction or
magnitude is not an input.

## Freeze procedure

The final primary, supplementary, and control sets are written below,
timestamped in UTC, and accompanied by input and artifact SHA-256 values in
`frozen_case_set.json` and `frozen_case_set.sha256`. After freezing, changes
require a dated deviation entry in `DECISION_LOG.md`; replacements are not
permitted solely because a result is null or contrary.

## Frozen set

Frozen at `2026-09-24T09:55:00Z`, before confirmatory estimation.

### Primary cases

- `BE03`: scheduled building lighting versus occupancy-responsive control.
- `WK07`: fixed-age maintenance versus condition-informed maintenance.
- `UI01`: flat electricity tariffs versus interval-aware pricing.
- `UI09`: calendar irrigation versus weather-adaptive scheduling.

### Supplementary case

- `TR01`: pre-timed versus responsive traffic-signal control. This case cannot
  support a redesign recommendation unless local incumbent timing, geometry,
  pedestrian, and safety constraints can be validated.

### Controls

- `NC01`: ISO freight-container dimensions as a high-network-cost compatibility
  control.
- `NC03`: ISO A-series paper proportions as an analytic null control for
  repeated-halving aspect-ratio invariance.

The full scores, source identifiers, limitations, input hashes, and selection
rationales are in `case_selection_evidence.csv` and `frozen_case_set.json`.
The frozen artifact SHA-256 is
`07fd1d1e2a4878eda2aab7e292f698a7b8232622645ff2544bb50e858cc05ea8`.
