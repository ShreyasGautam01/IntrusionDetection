# CIC-to-UNSW Source E1 Gate Interpretation

Generated 2026-11-12T04:36:42.219636+00:00. This report interprets only CIC source-test results under the frozen source-only protocol. No UNSW target data or labels were read.

## Verification

- All ten seeds (0–9) have complete, hash-verified artifacts: prediction, calibrated probability, and all five reliability signals. Each array has 4,025,148 finite rows and matches the frozen configuration, stage, and experiment manifest.
- The shared exact feature-distance artifact has SHA-256 `16f25ebc8a4f53e09b3143e997bb520525d464da677dd23f8610fcaeff5d8d8e` and is identical across all seeds.
- The independent seed 0 repeat exactly matches all seven arrays and source-test metrics. The repeat verification report records hashes for each array.
- Target files and target labels remain sealed; target transfer has not begun.

## Qualitative findings

The source detector is stable across RF seeds: accuracy median 0.9929 (range 0.9929–0.9929), attack AUPRC median 0.9761 (range 0.9761–0.9761), and attack AUROC median 0.9898 (range 0.9898–0.9898). Missed attack counts range from 26,434 to 26,504 of 4,025,148 source-test rows.

| Signal | 5% budget attack-miss capture (median; range) | Pairwise rank agreement, Spearman (median; range) | Top-5% review-set Jaccard (median; range) |
|---|---:|---:|---:|
| confidence | 0.2478 (0.2458–0.2493) | 0.9432 (0.9360–0.9476) | 0.8578 (0.8507–0.8659) |
| random forest disagreement | 0.1438 (0.1407–0.1466) | 0.5418 (0.5300–0.5538) | 0.5418 (0.5270–0.5572) |
| feature space distance | 0.0407 (0.0405–0.0408) | 1.0000 (1.0000–1.0000) | 1.0000 (1.0000–1.0000) |
| split conformal | 0.0000 (0.0000–0.0000) | 0.9324 (0.9273–0.9389) | 0.9900 (0.9886–0.9914) |
| isolation forest | 0.0355 (0.0326–0.0376) | 0.9660 (0.9487–0.9805) | 0.6548 (0.5016–0.7762) |

Confidence has the strongest observed miss capture at 5% and consistent review ranking. RF disagreement captures a smaller but nonzero share, with more seed variation in the selected review set. Feature-space distance is seed-independent by construction and its selected set is identical across seeds, but its miss capture is modest. Split conformal has stable rankings but captured no attack misses at 1%, 5%, or 10% in these source results. Isolation Forest captures a modest share, while its selected sets vary more, especially at smaller review budgets.

## Recommendation

**PASS for descriptive source-only E1 analysis, pending owner acceptance.** The detector and reproducibility evidence are stable enough to proceed with the planned interpretation, while the signal results do not support a blanket claim that all five methods capture misses equally or produce equally stable rankings. No numerical pass threshold was specified in the frozen configuration, so this recommendation is qualitative and does not introduce one.

**Transfer remains gated.** Do not begin target evaluation until the owner accepts this interpretation. Target transfer is not authorized by this report alone.

See `source_e1_cic_final_results.json` for per-seed metrics, stability intervals, ranking correlations, and review-set overlaps; see `cic_to_unsw_same_seed_repeat.json` for the exact repeat comparison.
