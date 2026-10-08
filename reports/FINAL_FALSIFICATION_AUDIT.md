# Final Falsification Audit

## Scope

The frozen cases, registered snapshots, and pre-specified primary classifications were retained. The audit recomputed or summarized:

- leave-one-primary-case-out;
- leave-one-domain-out;
- removal of WK07;
- removal of UI09;
- removal of WK07 and UI09 together;
- exclusion of simulated C-MAPSS evidence;
- null and network controls;
- exploratory classification-threshold sensitivity;
- supported model and loss alternatives.

The machine-readable results are in `outputs/analysis/final_falsification.csv`. Every added numerical result used in manuscript-facing text is registered in `MANUSCRIPT_VALUES.csv`.

## Main result

The procedural contribution survives all checks: cases can be passed through common audit gates without pooling non-common objective units. The empirical count of material oracle labels is not stable enough to support a prevalence claim.

Removing either WK07 or UI09 leaves one threshold-meeting primary case. Removing both leaves none. Excluding simulated C-MAPSS evidence also leaves one. Omitting the utilities/infrastructure domain removes UI01 and UI09 together and leaves one threshold-meeting case among the two retained primaries.

## Threshold sensitivity

The frozen reported classifications remain based on the pre-specified thresholds. An exploratory lower threshold set changes the descriptive count from two to three because BE03 then crosses its rule. The explored higher threshold set leaves the count at two. This establishes that the count is partly a decision-rule artifact and must not be interpreted as a population rate.

## Supported model and loss alternatives

- **BE03:** the nominal on-time gap varies strongly with the assumed fixed schedule and crosses classification-relevant ranges.
- **WK07:** static regret remains positive across the supported failure-cost and warning-lead settings, but all results remain simulated perfect-information comparisons.
- **UI01:** fixed-price arithmetic savings scale with the assumed flexible fraction; behavior and market equilibrium remain unidentified.
- **UI09:** the objective gap remains positive under the supported calendar estimator and shortfall penalties, but its magnitude is loss-function dependent and is not physical water savings.

## Controls

NC03 returns the exact null only for the repeated-halving similarity objective. NC01 remains unquantified because a compatibility-adjusted alternative and transition-cost ledger are absent. Together they show that the protocol does not force redesign or positive mismatch.

## Inference limits

No p-value is used as a substitute for an audit label. These are deterministic design, source-quality, threshold, and supported-model checks, not draws from a population of standards. The results do not identify a pooled effect, a population mismatch rate, or transition-adjusted superiority.
