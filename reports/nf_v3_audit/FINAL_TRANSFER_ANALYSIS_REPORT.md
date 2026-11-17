# Final Transfer Analysis Report

## 1. Scope

This report analyzes the completed source-only transfer artifacts for UNSW→CIC and CIC→UNSW across seeds 0–9. No RF fitting, target transfer scoring, or exact-distance computation is performed by this analysis stage.

Target labels are used only for offline evaluation after the frozen transfer manifests are validated.

## 2. Primary endpoint

The primary endpoint is target attack-miss AUPRC. The primary operational endpoint is attack-miss capture at a 5% analyst-review budget.

## 3. Primary results

| Direction | Signal | Mean attack-miss AUPRC | Mean 5% capture |
|---|---|---:|---:|
| unsw-to-cic | confidence | 0.192114 | 0.081874 |
| unsw-to-cic | random_forest_disagreement | 0.237903 | 0.123333 |
| unsw-to-cic | feature_space_distance | 0.108663 | 0.005786 |
| unsw-to-cic | split_conformal | 0.096152 | 0.173730 |
| unsw-to-cic | isolation_forest | 0.077010 | 0.007462 |
| cic-to-unsw | confidence | 0.032988 | 0.007678 |
| cic-to-unsw | random_forest_disagreement | 0.034682 | 0.008828 |
| cic-to-unsw | feature_space_distance | 0.043083 | 0.043371 |
| cic-to-unsw | split_conformal | 0.079389 | 0.147336 |
| cic-to-unsw | isolation_forest | 0.035689 | 0.004487 |

## 4. Seed variability

All primary comparisons preserve the ten matched seeds. Paired analyses use exact sign-flip permutation testing and seed-level bootstrap intervals.

See `analysis_paired_statistics.csv`.

## 5. Directional robustness

Direction-specific summaries are in `analysis_direction_shift.csv`. A score is flagged as semantically inverted only when its attack-miss AUROC falls below 0.5; performance is also interpreted relative to the attack-miss prevalence.

## 6. Family analysis

The frozen family registry supports a documented shared `DoS` category. Other cross-domain family equivalences are withheld where the registry lacks a defensible semantic crosswalk. Therefore this report does not claim unsupported unseen-family equivalence.

See `analysis_family_results.csv`.

## 7. Generic error versus attack-miss

Generic error AUPRC and AUROC, plus attack-miss AUROC, are reported in `analysis_generic_error.csv`. This separates ordinary error detection from the security-critical false-negative task.

## 8. Selective operational behavior

Residual attack-miss rates at 1%, 5%, and 10% review are in `analysis_selective_results.csv`.

## 9. Calibration and conformal diagnostics

Target calibration diagnostics are reported descriptively from the frozen source-calibrated probability outputs. No target recalibration is performed. Conformal analysis reports target ambiguity/set-size behavior and empirical coverage only when the source conformal quantile can be recovered from the saved provenance metadata.

## 10. Computational practicality

See `analysis_computational_cost.md`. The established production execution setting is RF fit `n_jobs=10`.

## 11. Limitations

- Only ten repeated seeds are available.
- The family registry intentionally withholds ambiguous semantic crosswalks.
- Unsupported unseen-family claims are not inferred from dataset-local attack names.
- Target labels are used only after source-only transfer scoring for evaluation.

## 12. Main findings

- **unsw-to-cic**: highest mean attack-miss AUPRC was `random_forest_disagreement` (0.237903); the remaining ranking should be interpreted with the paired seed analysis rather than by mean alone.
- **cic-to-unsw**: highest mean attack-miss AUPRC was `split_conformal` (0.079389); the remaining ranking should be interpreted with the paired seed analysis rather than by mean alone.

No claim of universal robustness or novelty is made from these descriptive results alone.
