# CIC Source E1 Distance-Bank Alternative — Owner Review Required

**Status:** Bounded feature-only bank benchmarking and revalidation are complete. The selected approximation and final CIC experiment manifest remain unapproved; no full E1 run has been launched.

## Why an alternative is proposed

The bounded exact benchmark on actual CIC arrays estimates 2.8–12.4 hours for all 12,068,590 source-train references and 4,025,148 queries. Its projected process working set is about 7.45 GB, almost all of the 7.66 GB available before benchmarking. Exact all-reference distance is therefore not a safe full-gate plan on the current resource state. The benchmark and calculation are documented in `CIC_SOURCE_E1_BENCHMARK_DECISION.md` and the JSON records.

## Candidate definition

Keep the source-train scaler exactly as specified: fit `StandardScaler` on every CIC source-train row only. Let `z(x)` denote the standardized 46-feature row. Select a bank of `K = 500,000` source-train row offsets with the smallest lexicographic priorities

`(SHA256(b"source-e1-cic-distance-bank-v1\x00" || uint64_be(i)), i)`

where `i` is the zero-based offset in the frozen `train_X.npy`. The stage preserves source-train input order. The offset hash is deterministic, label-blind, independent of all model seeds, and samples without replacement; the offset is the explicit collision tie-break.

For source-test row `x`, define

`d_K(x) = (1/5) * sum_{r in NN_5(z(x), z(B_K))} ||z(x) - z(r)||_2`.

This is an explicit deterministic reference-bank approximation to the frozen all-source-train mean 5-NN distance. It is **not mathematically identical** to the full-reference quantity unless the bank contains all source-train rows. It remains representation-dependent and seed-independent, and would be computed once per source direction and shared across RF seeds.

## Bounded benchmark results

The bank was selected twice over all 12,068,590 source-train offsets. Both passes returned the same ordered offset hash. Selection took 19.09 and 18.86 seconds, with 338 MB peak working set for the second pass. The 500,000-row standardized bank required 0.261 seconds to build and occupies about 184 MB on disk. The all-source-train `StandardScaler` fit took 5.05 seconds. Its parameter hash is `7ad1b9bf9f21fc9b9009b862cf98ac83e6b0119255d148ef1ca41839831ec560`.

The bounded exact baseline used the same 4,096 deterministic source-test queries and 2,400,000 evenly spaced source-train references. KDTree fit took 32.07 seconds; query took 10.14 seconds (404 queries/s). Its process peak was 3.46 GB. The score vector was finite; 1,830 of 4,096 rows had exact zero distance, the median score was 0.0002713, and p95 was 0.1330. This is not a full 12.07M-reference result. The earlier full exact envelope remains 2.8–12.4 hours with a projected 7.45 GB working set against about 7.66 GB available at that earlier benchmark, so exact full-scale execution remains unsafe on the measured machine state.

| Bank K | Query rate | Projected full source-test query time | Median absolute error | p95 absolute error | Median absolute error / exact-score median | Spearman rank correlation | Zero-score rows (bank / exact) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 4,771/s | 14.1 min | 0.004463 | 0.4109 | 16.45× | 0.8277 | 1,310 / 1,830 |
| 250,000 | 2,530/s | 26.6 min | 0.001429 | 0.2354 | 5.27× | 0.8847 | 1,452 / 1,830 |
| 500,000 | 1,666/s | 40.4 min | 0.0005314 | 0.1209 | 1.96× | 0.9213 | 1,565 / 1,830 |

The projections use the measured 4,096-query rates and add one index fit; they exclude the one-time scaler fit, bank selection, and bank transform. They are feature-only estimates, not a full E1 run. The largest timed phase peak across validation was 3.42 GB; 16 logical CPUs were available, while the single-thread phases used about one core (roughly 6.1% of logical capacity). System memory available fell from 7.96 GB before the validation to 5.73 GB afterward.

The first benchmark writer aggregated per-row relative errors and produced overflow at zero and near-zero exact distances. No such statistic is used here. The revalidation recomputed finite scores on the same samples and reports absolute error, exact and bank zero counts, score summaries, and rank correlation. It repeated the K=500,000 query and obtained bit-identical scores. No labels or target files were read. Both machine-readable reports are committed beside this review. For provenance, the first-pass generator was an uncommitted working-tree file and its exact executed bytes were not archived before correcting the metric aggregation; the revalidation script hash, first-pass report hash, and bank offset hashes are recorded in the final JSON. Treat the revalidation script and its checks as the reproducible evidence.

## Decision gate

The 500,000-row bank is the best measured candidate by absolute error and rank correlation, but it does not reproduce the exact signal: about 6.5 percentage points fewer sampled queries have zero distance, and its median score is about 4.5 times the exact median. This matters because duplicate-heavy rows create tied exact distances. The approximation has not been selected for E1.

The current CIC source config still specifies exact all-source-train mean Euclidean 5-NN. Do not change the config, freeze a CIC E1 manifest, or launch the CIC seed gate until the owner accepts the 500,000-row definition or directs another justified method. The target evaluation remains locked. The benchmark did not use source labels, RF outcomes, target data, or target labels to select the candidate.
