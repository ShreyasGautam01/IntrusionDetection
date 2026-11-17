# NF-v3 bidirectional transfer analysis

This directory contains the compact, committed analysis record for the completed source-only transfer study. The analysis covers UNSW→CIC and CIC→UNSW, seeds 0–9, the frozen 46-predictor representation, and five reliability signals. Transfer scoring and exact feature-distance computation were already complete before this analysis; this package does not rerun them.

## Status and interpretation

The master analysis checkpoint lists all 13 analysis phases as complete. The final integrity audit passes with no issues. Target labels were used for offline evaluation only; the audit records no use for fitting, tuning, recalibration, or score construction. The reports do not identify one signal as a universal winner: rankings differ by transfer direction. The family registry supports shared DoS only, so no broader unseen-family claim is made.

The results are descriptive for this two-dataset, ten-seed study. The current recommendation is not to add a dataset, detector, adaptation, recalibration, or the deferred compact 8-feature sensitivity automatically. Consider the latter only if representation sensitivity becomes a specific unresolved research question.

## Reading order

1. [Final analysis report](FINAL_TRANSFER_ANALYSIS_REPORT.md) — primary findings, direction-specific outcomes, interpretation, limitations.
2. [Next experiment recommendation](NEXT_EXPERIMENT_RECOMMENDATION.md) — follow-up decision and family-scope limitation.
3. [Per-seed metrics](analysis_per_seed_all_metrics.csv), [aggregate metrics](analysis_aggregate.csv), and [paired statistics](analysis_paired_statistics.csv) — seed-level values, descriptive summaries, paired differences, bootstrap intervals, and sign-flip tests.
4. [Direction shift](analysis_direction_shift.csv), [family results](analysis_family_results.csv), [family scope](analysis_family_scope.md), and [generic-error results](analysis_generic_error.csv).
5. [Selective risk](analysis_selective_results.csv), [calibration/conformal diagnostics](analysis_calibration_conformal.csv), and [computational-cost synthesis](analysis_computational_cost.md).
6. [Integrity audit](FINAL_ANALYSIS_AUDIT.json), [analysis lock validation](analysis_lock_validation.json), and [score artifact inventory](analysis_artifact_inventory.csv).
7. [Figures](analysis_figures/) — attack-miss AUPRC and 5% capture by direction, plus the direction comparison.

The [research artifact manifest](RESEARCH_ARTIFACT_MANIFEST.json) records SHA-256 and sizes for the committed study definition, execution provenance, analysis source, and compact analysis outputs. [Reproduction notes](../../REPRODUCTION.md) describe the locked environment and local data requirements.

## Frozen study and offline evaluation

The source study definition remains in the root [proposal](../../research_proposal.md) and [methodology](../../methodology_final.md); neither is changed by this archive update. The transfer manifests and evaluation records for both directions remain the provenance authority. Target labels were consumed only by the offline evaluation stage after frozen-manifest validation. They did not influence model fitting, signal construction, tuning, calibration, or thresholds.

## Data intentionally excluded from Git

Raw dataset files and large generated numerical assets remain local and ignored, including source-stage arrays, per-row target scores, exact-distance arrays, model caches, and runtime checkpoints. Compact committed records preserve the corresponding provenance and hashes: the score inventory contains the 100 direction/seed/signal score-array row counts and SHA-256 values, plus two aggregate target-label hash records (no label values). The transfer manifests and evaluation/checkpoint reports bind the dataset, split, and execution provenance. This directory intentionally contains summaries and audit data rather than the large arrays themselves.

To inspect the full chain, follow the committed transfer manifests, evaluation reports, artifact inventory, source E1 results, and the local-only data paths they identify. Do not interpret exclusion of large arrays as a missing analysis phase.
