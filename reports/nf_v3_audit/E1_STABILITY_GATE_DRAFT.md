# E1 Source-Only Stability Gate (Draft)

**Status:** Seeds 0–5 partial outputs were integrity-checked and reproduced; the full five-signal, ten-seed gate is incomplete. No numeric acceptance threshold is frozen.
**Scope:** UNSW-only in-domain gate for the active UNSW → CIC2018 direction.
**Target labels:** CIC2018 remains sealed; no target rows or labels are needed for this gate.
**Prepared from:** frozen `methodology_final.md` E1 requirement and `rf_config_draft.json` (`rf-draft-4`); source file SHA-256 `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`.

## What the frozen protocol requires

The E1 section requires a source in-domain control that trains the Random Forest, calibrates probabilities, fits the reliability layers, and evaluates on held-out source test data. It calls for detector metrics, generic-error ranking, attack-miss ranking, calibration, and score-distribution outputs. The acceptance statement requires stable results across seeds but defines neither a numeric tolerance nor one summary statistic for stability.

The partial run and its checks are recorded in `SOURCE_E1_PARTIAL_REPORT.md` and `SOURCE_E1_RECOVERY_AUDIT.md`. The original artifacts reproduce for the RF detector, confidence, and disagreement signals. They do not contain the configured kNN distance, split conformal, or Isolation Forest outputs. A separate exact distance computation did not finish within more than 12 minutes and produced no usable result. The full stability gate has not passed and no target-derived choice was made.

## Proposed reporting procedure

1. Use the approved UNSW train/calibration/source-test partitions and the same frozen preprocessing and estimator configuration for each of the ten proposed seeds (0–9). Do not tune any setting between seeds.
2. Save per-seed predictions, calibrated probabilities, and each reliability score on the same source-test rows. Record input/config hashes and software versions with every run.
3. For every seed, report the frozen E1 output groups: detector performance; reliability ranking of generic errors; reliability ranking of attack false negatives; calibration; and score distributions. For the core security endpoint, treat an attack false negative as an event to rank and report attack-miss AUPRC and attack-miss capture at the predeclared review budgets.
4. Summarize each scalar metric across seeds with median, interquartile range, minimum, and maximum. For the per-row ranking outputs, report pairwise seed-to-seed Spearman rank correlations and their median/minimum; also report whether score ordering changes at each declared review budget. Do not average scores or predictions across seeds unless a separately frozen protocol explicitly requires it.
5. Repeat one fixed seed once in a clean process under the same locked runtime and input/config hashes. Compare predictions and metrics exactly; if they differ, stop for a reproducibility investigation before interpreting cross-seed variation.
6. Keep all ten seed results, including failures. Do not exclude a seed based on performance. A failed run is classified using a predeclared technical invalid-run rule, documented with the raw error and rerun provenance.

## Decision still required before target evaluation

The reporting procedure above makes seed variation visible but cannot determine whether a particular spread is acceptable. Before target evaluation is unlocked, review and record a stability decision rule for at least:

- the maximum acceptable across-seed spread for source-test attack-miss AUPRC and capture at the primary review budget;
- the minimum acceptable seed-to-seed rank agreement for attack-miss rankings;
- whether any calibration or detector-performance metric is a hard gate or descriptive only; and
- the treatment of ties in score rankings and review-budget cutoffs.

No numeric cutoffs are proposed here because the frozen protocol supplies none, and inventing them without review would add an unapproved method