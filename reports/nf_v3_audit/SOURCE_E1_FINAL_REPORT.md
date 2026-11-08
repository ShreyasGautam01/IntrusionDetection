# Source-Only E1 Five-Signal Results

**Configuration:** `source-e1-lock-1`
**Manifest:** `source_e1_manifest.json`
**Source:** NF-UNSW-NB15-v3, SHA-256 `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`
**Target:** no CIC2018 data or labels were opened; target evaluation remains locked.

## Completion and provenance

All ten seeds (0–9) completed the full five-signal source-only run. Every result directory contains prediction, calibrated probability, the five score arrays, metrics, and artifact hashes. The summarizer verified shapes, finiteness, metadata, hashes, and all ten detector/reliability summaries. The full distance score is shared by all seeds and has SHA-256 `6149f6600428e995b8f880de60262bea25642e60a99969b713f6aa843e30c05f`.

Seeds 0–5 remain untouched in their original locations. Their recovered probability, prediction, and RF-disagreement arrays were compared with the locked refits and matched byte-for-byte; those recovered outputs were reused. The refits were needed because source calibration probabilities for the conformal subset had not been retained. Seeds 6–9 were computed fully. A separate seed-0 reproducibility run matched all seven per-row arrays and the metrics exactly.

| Seed | RF fit (s) | Recovered partial outputs reused | Attack misses |
|---:|---:|:---:|---:|
| 0 | 608.7 | Yes | 10 |
| 1 | 606.1 | Yes | 10 |
| 2 | 235.4 | Yes | 10 |
| 3 | 229.0 | Yes | 10 |
| 4 | 221.2 | Yes | 10 |
| 5 | 233.2 | Yes | 10 |
| 6 | 236.4 | No | 10 |
| 7 | 1,484.4 | No | 10 |
| 8 | 256.9 | No | 10 |
| 9 | 241.5 | No | 10 |

Retain both seed 1's historical 6,683s pilot fit and its 606s capped-thread refit, and seed 7's 1,484s fit. Neither is excluded. The 25% benchmark was not a reliable predictor of per-seed runtime; full RF fit times varied substantially despite fixed threads.

## Frozen five-signal definitions and factorization

- **Confidence:** `1 - max(source-Platt-calibrated class probabilities)`. RF-seed-dependent; reused for seeds 0–5 after exact matches.
- **RF disagreement:** `1 - max class vote fraction across the 200 trees`. RF-seed-dependent; reused for seeds 0–5 after exact matches.
- **Feature-space distance:** exact mean Euclidean distance to the five nearest rows among all 1,418,952 source-train rows after `StandardScaler` fit on source train only. Implemented by scikit-learn KDTree, `leaf_size=30`, `n_jobs=1`, float64 standardized arrays, 2,048-row query batches. It has no seed/random input, was computed once, and was shared across all seeds.
- **Split conformal:** disjoint source calibration subset; nonconformity `1 - calibrated probability assigned to the true calibration class`; finite-sample order statistic at zero-based index `ceil((n+1)*(1-alpha))-1`, `alpha=0.10`; include a class when its nonconformity is at most the fitted quantile; review score `(set_size-1)/(2-1)`. RF-seed-dependent. The configured mapping gives an empty prediction set a score of -1; this was retained as locked.
- **Isolation Forest:** fit on source train only with 100 trees, `max_samples=256`, `max_features=1.0`, `contamination="auto"`, no bootstrap; score `-score_samples` so higher is more anomalous. It does not consume RF predictions, but the config binds `random_state` to the corresponding run seed; it was therefore fit once per seed, not collapsed to a shared fit.

The exact distance run processed 473,171 queries in **1,746.4s (29m06s)**, about **271 queries/s** end to end. This is consistent with the benchmark and confirms that exact computation is practical as a long single job. No approximation was used. The bounded benchmark measured about 1.01GB peak working set for full-source scaler fitting and 0.76GB at 800k references; full exact peak was estimated at 1.0–1.5GB. The live ten-seed run retained at least 3.82GB available physical memory. The 25% RF benchmark's two-worker peak was 537MB, with 0.7–1.0GB estimated for full concurrent workers. The ten-seed two-worker batch took about 49 minutes wall time; summed RF fit CPU time was 4,352.7 seconds (72.5 core-minutes). The selected plan completed all seeds; OpenMP/BLAS/RF internal thread counts were capped at one.

See `SOURCE_E1_BENCHMARK.md` and the four machine-readable benchmark records for reference/query scaling, CPU use, fit concurrency, and measured working sets.

## Source-test stability summary

There were 25,608 attacks among 473,171 source-test rows, and each seed produced ten attack misses. Detector metrics were tightly grouped: accuracy ranged 0.9999598–0.9999683, attack AUPRC 0.99999950–0.99999963, and Brier score 0.0000268–0.0000300.

| Signal | Attack-miss AUPRC (median; min–max) | Attack capture at 5% (all-seed range) | Pairwise Spearman (median; min) | Top-5% overlap Jaccard (median; min) |
|---|---:|---:|---:|---:|
| Confidence | 0.1661; 0.1557–0.2399 | 1.00; 1.00–1.00 | 0.799; 0.605 | 0.703; 0.340 |
| RF disagreement | 0.1163; 0.0887–0.1365 | 1.00; 1.00–1.00 | 0.643; 0.307 | 0.957; 0.699 |
| Feature-space distance | 0.000488; fixed | 0.60; 0.60–0.60 | 1.000; 1.000 | 1.000; 1.000 |
| Split conformal | 0.000021; fixed | 0.00; 0.00–0.00 | 0.801; 0.592 | 0.965; 0.902 |
| Isolation Forest | 0.000088; 0.000056–0.000111 | 0.00; 0.00–0.00 | 0.957; 0.935 | 0.809; 0.695 |

Attack-miss AUPRC and review capture are based on only ten positive miss events per seed. The 5% capture result is stable for confidence and disagreement, but confidence, disagreement, conformal, and Isolation Forest show non-identical cross-seed ranks. Distance is invariant because it is seed-independent.

## Gate decision

The full computation, integrity checks, and same-seed reproduction are complete. However, `source-e1-lock-1` explicitly imposes no numeric stability tolerance, and the frozen stability draft calls for a project-level interpretation before target unlock. The observed minimum pairwise rank correlations (0.605 confidence, 0.307 disagreement, 0.592 conformal, 0.935 Isolation Forest) and the sparse ten-miss endpoint need that interpretation. **E1 is not cleared for target transfer yet.** No post-hoc threshold was invented, and no target data were evaluated.

Machine-readable per-seed values, pairwise correlations, top-review overlap, hashes, and repeat comparison are in `source_e1_final_results.json`. Reproduce the summary with `python scripts/summarize_source_e1.py`.
