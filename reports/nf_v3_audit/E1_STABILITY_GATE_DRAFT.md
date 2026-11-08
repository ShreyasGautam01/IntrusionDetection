# E1 Source-Only Stability Gate (Draft)

**Status:** Full five-signal results for seeds 0–9 and an exact seed-0 repeat are complete. Numeric acceptance thresholds remain unspecified by the locked config; target evaluation remains locked pending project-level stability interpretation.
**Scope:** UNSW-only in-domain gate for the active UNSW → CIC2018 direction.
**Target labels:** CIC2018 remains sealed; no target rows or labels are needed for this gate.
**Prepared from:** frozen `methodology_final.md` E1 requirement and `rf_config_draft.json` (`rf-draft-4`); source file SHA-256 `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`.

## What the frozen protocol requires

The E1 section requires a source in-domain control that trains the Random Forest, calibrates probabilities, fits the reliability layers, and evaluates on held-out source test data. It calls for detector metrics, generic-error ranking, attack-miss ranking, calibration, and score-distribution outputs. The acceptance statement requires stable results across seeds but defines neither a numeric tolerance nor one summary statistic for stability.

The recovery checks are recorded in `SOURCE_E1_RECOVERY_AUDIT.md`. The completed five-signal results, all-seed summaries, rank agreement, review-set overlap, and exact repeat are recorded in `SOURCE_E1_FINAL_REPORT.md` and `source_e1_final_results.json`. The exact shared distance calculation took 1,746.4 seconds. The full computation is complete; target unlock is still pending because the frozen config provides no numeric stability tolerance and the source-only rank variation requires interpretation.

## Proposed reporting procedure

1. Use the approved UNSW train/calibration/source-test partitions and the same frozen preprocessing and estimator configuration for each of the ten proposed seeds (0–9). Do not tune any setting between seeds.
2. Save per-seed predictions, calibrated probabilities, and each reliability score on the same source-test rows. Record input/config hashes and software versions with every run.
3. For every seed, report the frozen E1 output groups: detector performance; reliability ranking of generic errors; reliability ranking of attack false negatives; calibration; and score distributions. For the core security endpoint, treat an attack false negative as an event to rank and report attack-miss AUPRC and attack-miss capture at the predeclared review budgets.
4. Summarize each scalar metric across seeds with median, interquartile range, minimum, and maximum. For the per-row ranking outputs, report pairwise seed-to-seed Spearman rank correlations and their median/minimum; also report whether score ordering changes at each declared review budget. Do not average scores or predictions across seeds unless a separately frozen protocol explicitly requires it.
5. Repeat one fixed seed once in a clean process under the same locked runtime and input/config hashes. Compare predictions and metrics exactly; if they differ, stop for a reproducibility investigation before interpreting cross-seed variation.
6. Keep all ten seed results, including failures. Do not exclude a seed based on performance. A failed run is classified using a predeclared technical invalid-run rule, documented with the raw error and rerun provenance.

## Target-evaluation decision still required

The reporting procedure above makes seed variation visible but cannot determine whether a particular spread is acceptable. Before target evaluation is unlocked, review and record a stability decision rule for at least:

- the maximum acceptable across-seed spread for source-test attack-miss AUPRC and capture at the primary review budget;
- the minimum acceptable seed-to-seed rank agreement for attack-miss rankings;
- whether any calibration or detector-performance metric is a hard gate or descriptive only; and
- the treatment of ties in score rankings and review-budget cutoffs.

The completed source-only results show stable detector metrics and stable 5% capture for confidence/disagreement, while seed-to-seed Spearman minima are 0.605 for confidence, 0.307 for disagreement, 0.592 for conformal, and 0.935 for Isolation Forest. Each seed has only ten attack misses. No numeric cutoffs are supplied by the frozen protocol, and none were added after seeing results. The target gate remains closed until the project-level interpretation is recorded.

## Scope protections

- This draft uses only the already-audited UNSW source split for E1. It does not evaluate CIC2018 or inspect CIC2018 labels.
- It records the source-only gate procedure and current status; it does not authorize target evaluation.
- It does not modify `research_proposal.md` or `methodology_final.md`.
- The separate temporal and host/session controls remain separate analyses and are not mixed into the baseline seed-stability summary.
