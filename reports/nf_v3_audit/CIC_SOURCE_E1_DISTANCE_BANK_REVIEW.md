# CIC Source E1 Feature-Distance Decision

**Status:** The project owner delegated the method choice on 2026-11-09. The lossy reference bank was rejected in favor of a mathematically equivalent, memory-bounded exact implementation. The final experiment manifest is being frozen before any full CIC E1 seed run.

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

## Exact duplicate-compression benchmark

The decision was informed by an exact-preserving alternative. On deterministic source-train feature samples, `np.unique(axis=0, return_counts=True)` found these distinct-row fractions:

| Sample rows | Unique rows | Unique fraction | Dedup wall time | Dedup peak process working set |
|---:|---:|---:|---:|---:|
| 100,000 | 64,592 | 64.6% | 0.36 s | 2.42 GB |
| 250,000 | 152,210 | 60.9% | 1.03 s | 2.51 GB |
| 500,000 | 291,036 | 58.2% | 2.27 s | 2.62 GB |

For each unique row, retain its exact integer multiplicity. A bounded comparison on 500,000 raw references and 1,024 source-test queries compared the original KDTree 5-NN mean with the weighted unique-row calculation. Scores matched within `6.94e-18` absolute error at `rtol=1e-12, atol=1e-12`; both methods returned 388 zero-distance scores. The arrays were not bitwise identical because the two KDTree layouts sum floating-point distances in a different order. The mathematical score and zero-distance count matched.

A second bounded benchmark split the same 500,000-reference sample into two disjoint 250,000-row chunks, deduplicated each chunk independently, and merged each chunk's five nearest distinct rows with their multiplicities. The merged result matched the raw 500,000-reference exact result within the same tolerance, with the same 388 zero scores. The query-side merge took 0.00075 seconds for 1,024 rows after the two chunk queries. No labels or target data were read.

## Selected implementation

Use **exact chunked 5-NN with duplicate multiplicities** for CIC. The scaler is fitted on all original CIC source-train rows. Divide source-train rows in input order into 500,000-row chunks; within each chunk, collapse identical finite float32 feature rows and keep their integer counts; standardize those unique rows; fit one KDTree; and query the source-test rows in batches. For every query, merge the chunk's five nearest distinct vectors and their multiplicities into the current five-neighbor candidate pool. After all chunks, compute the mean of the five nearest original reference rows with multiplicity weights. The top five distinct vectors from each chunk suffice because a sixth distinct vector from that same chunk cannot be closer than its first five; any tie at the boundary has the same distance. This preserves the frozen all-source-train mean Euclidean 5-NN definition without an approximation.

There are 25 planned 500,000-row chunks. A measured 500,000-reference unique-row index queried all 4,025,148 CIC source-test rows at the bounded rate projects 516 seconds per reference chunk. Adding the measured per-chunk unique extraction, scaling, and KDTree fit yields **about 3.62 hours** for the full exact distance signal, excluding checkpoint and output I/O. The maximum bounded phase working set was 2.62 GB. The implementation uses two disk-backed top-five state slots (about 483 MB total); a conservative additive estimate is **about 3.10 GB** peak. The machine had 7.42 GB available before the multi-chunk check and 4.93 GB afterward; the production runner refuses to start below 4.20 GB available.

One CIC RF worker with one internal thread is selected for the full seed gate. The two-worker sample was 1.74× faster for two fits but had only 2% of the source-train rows; a single full forest avoids compounding full-data memory demand. Isolation Forest and RF internal threads remain capped at one. The distance signal is computed once and shared across seeds; Isolation Forest is fitted once for each seed under the frozen seed-specific `random_state`.

The hash-priority K=500,000 bank remains a benchmark-only comparison and is **not selected**. It had Spearman 0.9213, but returned 1,565 zero scores instead of 1,830 exact zeros on 4,096 queries, demonstrating a meaningful distribution change. No alternative signal definition is being introduced.

The current CIC config still defines the exact signal. A separate frozen experiment manifest will bind the exact chunked implementation, benchmark hashes, source data/split/features, RF settings, software, and one-worker concurrency before the full E1 run. CIC seeds have not started, and target transfer remains locked until both source-only gate interpretations are accepted.
