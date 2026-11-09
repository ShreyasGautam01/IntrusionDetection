# CIC Source E1 Benchmark and Resource Decision

**Date:** 2026-11-09 local run; benchmark clock recorded in UTC in the JSON evidence.
**Direction:** CIC → UNSW source-only E1 gate.
**Status:** The original monolithic exact KDTree fit was too close to available-memory limits. Follow-up exact duplicate-compression and multi-chunk benchmarks support a mathematically equivalent, memory-bounded implementation with an estimated 3.62-hour distance runtime and roughly 3.10 GB projected peak. The CIC experiment manifest is being frozen before seed runs. Target evaluation remains sealed.

## Frozen inputs and staging

- CIC source CSV SHA-256: `242a6971cc801eae621b1fc4d966db2cd0af9cc866805f36a6fc5d0058dfbb74`.
- Source configuration ID: `source-e1-cic-lock-1`; config SHA-256: `ace3a131113d1c56f8488b2dcea562154829eceeff75b57bb38da1d8505c8124`.
- Staged source manifest SHA-256: `a0c3e3f618f35c5bbed7ad1fb3b252f06f215b2146a79aa511b9574f4f414665`.
- The staged 46-feature order is copied from `source-e1-lock-1`. The seven excluded identifier/metadata columns are not predictors.
- Label-blind SHA-256 split over the canonical raw 53-feature strings; first eight digest bytes as big-endian modulo 100; buckets 0–59 train, 60–79 calibration, 80–99 source test.
- Row counts: 12,068,590 train; 4,021,791 calibration; 4,025,148 source test; 20,115,529 total. Class counts and all six array hashes are in the ignored local `stage_manifest.json`.
- All staged features are finite. No target UNSW file or labels were read. CIC labels were used only as CIC source labels for this reverse-direction gate.

## Five frozen signals and seed factorization

1. **Confidence:** `1 - max(p0, p1)` using the seed-specific Platt-calibrated RF probabilities.
2. **RF disagreement:** `1 - max_c(votes_c / 200)` from the seed-specific forest’s 200 tree predictions.
3. **Feature-space distance:** exact mean Euclidean distance to the five nearest CIC source-train rows after a `StandardScaler` fitted only on CIC source train.
4. **Split conformal:** disjoint calibration sub-split; nonconformity `1 - calibrated probability of the true source class`; alpha 0.10 finite-sample order statistic at `ceil((n+1)*0.9)`; scalar `(prediction_set_size - 1)/(2 - 1)`.
5. **Isolation Forest:** `-score_samples`, 100 estimators, `max_samples=256`, `max_features=1.0`, `contamination="auto"`, fitted on source train with `random_state=seed`.

Confidence, RF disagreement, and conformal vary with the RF seed. Distance has no RF-seed dependency and is to be computed once and shared. Isolation Forest does not consume RF outputs, but its frozen random state equals each run seed, so it is to be fitted once for each of seeds 0–9. No additional random choice has been introduced.

## Bounded exact distance benchmark

The benchmark used the actual staged CIC train and source-test arrays, the full 12,068,590-row source-train scaler statistics (deterministic 100,000-row `StandardScaler.partial_fit` blocks), exact scikit-learn KDTree Euclidean 5-NN, and bounded deterministic evenly spaced reference/query rows. The largest reference bank was 2,400,000 rows (19.9% of source train); the largest query batch was 4,096 rows. Each operation records wall time, process CPU, logical CPU utilization, process working set, throughput, and index/query hashes. The extended report is `cic_source_e1_benchmark_extended.json`; the initial 1.6M sweep, including the RF comparison, is `cic_source_e1_benchmark.json`.

| References | Transform (s) | KDTree fit (s) | 512-query time (s) | Query throughput (rows/s) | Peak process working set (GB) |
|---:|---:|---:|---:|---:|---:|
| 100,000 | 0.05 | 0.77 | 0.108 | 4,724 | 2.43 |
| 250,000 | 0.11 | 2.29 | 0.391 | 1,311 | 2.50 |
| 500,000 | 0.24 | 5.27 | 0.335 | 1,526 | 2.60 |
| 800,000 | 0.37 | 8.74 | 0.526 | 974 | 2.72 |
| 1,200,000 | 0.54 | 14.14 | 0.743 | 689 | 2.90 |
| 1,600,000 | 0.74 | 18.52 | 1.739 | 294 | 3.05 |
| 2,000,000 | 0.91 | 24.90 | 1.051 | 487 | 3.26 |
| 2,400,000 | 6.17 | 30.77 | 1.246 | 411 | 3.41 |

At 2.4M references, query batches of 128, 512, 2,048, and 4,096 rows achieved 497, 417, 418, and 408 rows/s; the 4,096-query run took 10.05 seconds. Per-query performance was stable across those batch sizes, but not monotonic as the reference subset grew, so the runtime projection is an envelope rather than a single extrapolation. At 2.4M, fit and query each used about one CPU core (about 6% of 16 logical CPUs). The full-source streaming scaler fit took 4.93 seconds and about one core. Reference transform throughput was generally high; the 2.4M transform had a measured I/O/page-fault delay and is retained in the estimate.

## Full exact runtime and memory estimate

For all 12,068,590 references and 4,025,148 source-test queries, the measured tail-scaling envelope estimates:

- Full scaler fit: 4.9 seconds measured on all source-train rows.
- Reference transform: about 31 seconds estimated from the largest bounded transform.
- Source-test transform: about 15 seconds estimated.
- KDTree construction: about 200–263 seconds estimated.
- Exact queries: about 9,796–44,317 seconds estimated.
- **Total exact distance: about 2.8–12.4 hours.** Query-growth uncertainty is material: the latest reference-size tail produces query-time exponents from −2.26 to 0.93; the lower estimate clamps growth at zero and the upper uses the measured positive tail exponent.

The complete float64 standardized source-train reference array alone needs **4.44 GB**. At 2.4M rows, exact KDTree fitting added 1.003 GB of measured process working set over its baseline; linear scaling to all references adds about 5.04 GB. With the measured 2.41 GB baseline, the projected process peak is **about 7.45 GB**. The machine had 16.85 GB total physical RAM, but only 7.66 GB available before the extended benchmark and 5.39 GB afterward. The linear projection leaves about 0.21 GB versus the pre-benchmark available memory, before allowing for system variation or other work. D: had about 137 GB free, so disk capacity is not the limiting resource.

**Decision:** category (c), exact full-scale distance is impractical with the current available-memory headroom. The bounded measurement supports the runtime estimate, but the projected peak nearly consumes all memory available at launch and is not a safe basis for an unattended full E1 job. The exact calculation was not started. No approximation, manifest change, or CIC seed run was started.

## Random Forest concurrency benchmark

Two fits on the same deterministic 2% sample (241,371 rows, 46 features, seeds 0 and 1) were measured sequentially and concurrently. Internal OpenMP/BLAS threads and estimator `n_jobs` were capped at one.

| Workers | Two-fit wall time | Per-fit time | CPU core equivalents | Peak working set |
|---:|---:|---:|---:|---:|
| 1 | 119.3 s | 59.5, 59.9 s | 0.97 | 2.52 GB |
| 2 | 68.5 s | 67.9, 68.5 s | 1.96 | 2.60 GB |

Two workers gave 1.74× pair throughput, with a measured peak increment of 143 MB over the sample-run baseline. **Provisional choice for later seed fitting: two workers, one internal thread each; run only after the distance job and recheck full-fit memory.** The full RF seeds were not launched.

## Smoke test

`source_e1_smoke_cic-to-unsw_seed0.json` records a deterministic class-present source sample (2,500 rows per class for training; 1,000 per class for calibration and source test). All five outputs had shape `(2000,)` and finite values. The smoke used exact 5-NN distance on the bounded training sample, and reports no target-file or target-label access. The smoke test had zero detector errors/misses, so its error-ranking endpoints are not interpreted. The first smoke attempt on the raw prefix exposed a one-class RF sample; the final plumbing test corrects this by selecting class-present rows only for smoke, with the frozen full-run split unchanged.

## Follow-up exact-preserving implementation

`CIC_SOURCE_E1_DISTANCE_BANK_REVIEW.md` records the bounded bank comparison and the selected exact alternative. Repeated vectors are collapsed within deterministic 500,000-row source-train chunks and their exact integer multiplicities are carried into the top-five merge. Raw-versus-weighted and two-chunk-versus-raw comparisons matched within `6.94e-18` maximum absolute error on 1,024 source-test rows, with equal zero-distance counts. The formula remains the exact five nearest original source-train rows; no approximation was selected.

The measured full-distance projection is about 3.62 hours and 3.10 GB peak, including the two disk-backed merge-state slots. The runtime projection excludes checkpoint and output I/O. The full job has not started. The source E1 manifest and a production startup memory check are required before launching it.

## Gate state

UNSW E1 seeds 0–9 and their exact-distance artifact remain complete and untouched from the published prior milestone. The UNSW gate interpretation was accepted for descriptive use on 2026-11-09. CIC E1 seeds 0–9 have **not** been run; no CIC five-signal final results exist. The CIC source gate is incomplete, so neither transfer direction is ready for target evaluation.
