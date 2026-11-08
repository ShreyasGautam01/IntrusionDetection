# Source E1 Resource Benchmark and Execution Decision

**Date:** 2026-11-08  
**Source:** UNSW staged E1 arrays only; no target paths opened.  
**Runtime:** Python 3.14.7, NumPy 2.5.2, scikit-learn 1.9.1; 16 logical CPUs.  
**Thread caps:** OpenMP=1, BLAS=1, RF `n_jobs=1`.

## Exact feature-space distance

The benchmark used the intended definition: fit `StandardScaler` on the full source-train matrix; select deterministic, evenly spaced source-train reference rows and source-test query rows; fit scikit-learn `NearestNeighbors(algorithm="kd_tree", leaf_size=30, metric="euclidean", n_jobs=1)`; return the mean of the five exact nearest-neighbor distances. Every benchmark row is a subset of the actual frozen arrays. Query time and throughput below exclude scaler fitting and index construction.

| Reference rows | Query rows | Index fit (s) | Query (s) | Throughput (queries/s) | Peak process working set (MB) |
|---:|---:|---:|---:|---:|---:|
| 25,000 | 512 | 0.15–0.18 | 0.054–0.066 | 7,734–9,414 | 434 |
| 50,000 | 512 | 0.34–0.36 | 0.067–0.070 | 7,358–7,691 | 445 |
| 100,000 | 512 | 0.76–0.77 | 0.158–0.194 | 2,638–3,237 | 466 |
| 200,000 | 512 | 1.63–1.68 | 0.505–0.509 | 1,006–1,013 | 508–510 |
| 400,000 | 512 | 3.96–4.00 | 0.463–0.471 | 1,087–1,107 | 591–592 |
| 600,000 | 512 | 6.48–6.50 | 0.684–0.744 | 688–749 | 681–682 |
| 800,000 | 512 | 8.56 | 1.172 | 437 | 758 |

At 800,000 references, query-count scaling was near-linear: 256 queries took 0.564s, 512 took 1.122s, 1,024 took 2.396s, and 2,048 took 4.528s (427–456 queries/s). Results varied with reference subset size, so extrapolation is an interval rather than a point estimate.

Using the measured 400k→800k and 600k→800k tail scaling independently, full 1,418,952-reference / 473,171-query execution is estimated at **38–55 minutes**, including a small index-build cost. That is category **(b): exact computation is practical as one long single job**. The production plan is exact KD-tree search with one worker, bounded query batches, progress checkpoints, and no RF work concurrent with it. No approximation or reference-bank reduction is justified by these measurements.

The full-source `StandardScaler.fit` took 0.58–0.75s but peaked at about **1.01GB working set** due to temporary copies. The 800k-reference search peaked at about **0.76GB working set**; the full float64 standardized reference matrix is 522MB versus 294MB at 800k. Estimated full distance peak is **1.0–1.5GB**. Available physical memory at planning time was 3.79GB; D: had 128.11GB free. This leaves workable headroom for the isolated distance job.

## Random Forest concurrency

The exact 200-tree RF parameters were fit on one deterministic 25% source-train sample (354,738 × 46). The sample row-index hash is in `source_e1_rf_benchmark_25pct.json`.

| Concurrent RF workers | Total elapsed for benchmark jobs | Per-fit time | Peak working set | Peak increment over run baseline | CPU use of 16 logical CPUs |
|---:|---:|---:|---:|---:|---:|
| 1 | 42.42s | 42.42s | 517.8MB | 26.6MB | 6.1% (0.97 core) |
| 2 | 49.79s | 47.98–49.79s | 537.3MB | 43.0MB | 12.1% (1.94 cores) |

Two workers complete two sample fits in 49.79s versus 84.84s if run one at a time, a measured 1.70× throughput gain. Use **two concurrent RF seeds**, with OpenMP and BLAS limited to one thread and each estimator `n_jobs=1`. The bounded 25% peak was 537MB; scaling for full data/model size gives a planning range of **0.7–1.0GB working set** for the RF workers. Run the distance job separately so it does not compete for this memory.

For ten full seeds, including source calibration, disagreement, conformal scoring, Isolation Forest, scoring, and one same-seed reproducibility repeat, reserve **30–60 minutes**. The previous seed-1 fit-time anomaly remains included; concurrency results do not invalidate or exclude it. Total estimated E1 compute budget is **about 68–115 minutes**, plus any resume overhead.

## Five-signal factorization

- Confidence depends on each seed’s calibrated RF probabilities.
- RF disagreement depends on that seed’s tree votes.
- Split conformal depends on that seed’s calibrated RF probabilities on the fixed disjoint conformal-calibration subset.
- Feature-space distance depends only on the fixed source-train scaler/reference and source-test feature arrays. It has no random seed and is computed once, then shared across all RF seeds.
- Isolation Forest does not consume RF predictions, but `source-e1-lock-1` sets its `random_state` to the corresponding RF run seed. It is therefore seed-varying under the frozen config and will be fit once for each declared seed; changing to one shared IF fit would change the protocol.

The full measured benchmark records are `source_e1_benchmark.json`, `source_e1_benchmark_extended.json`, `source_e1_benchmark_800k.json`, and `source_e1_rf_benchmark_25pct.json`. The experiment manifest records their hashes and the selected resource plan.
