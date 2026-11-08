# CIC Source E1 Distance-Bank Alternative — Owner Review Required

**Status:** Proposal only. No change to the CIC source-E1 config or experiment manifest; no approximation benchmark or E1 run has been launched.

## Why an alternative is proposed

The bounded exact benchmark on actual CIC arrays estimates 2.8–12.4 hours for all 12,068,590 source-train references and 4,025,148 queries. Its projected process working set is about 7.45 GB, almost all of the 7.66 GB available before benchmarking. Exact all-reference distance is therefore not a safe full-gate plan on the current resource state. The benchmark and calculation are documented in `CIC_SOURCE_E1_BENCHMARK_DECISION.md` and the JSON records.

## Candidate definition

Keep the source-train scaler exactly as specified: fit `StandardScaler` on every CIC source-train row only. Let `z(x)` denote the standardized 46-feature row. Select a bank of `K = 500,000` source-train row offsets with the smallest lexicographic priorities

`(SHA256(b"source-e1-cic-distance-bank-v1\x00" || uint64_be(i)), i)`

where `i` is the zero-based offset in the frozen `train_X.npy`. The stage preserves source-train input order. The offset hash is deterministic, label-blind, independent of all model seeds, and samples without replacement; the offset is the explicit collision tie-break.

For source-test row `x`, define

`d_K(x) = (1/5) * sum_{r in NN_5(z(x), z(B_K))} ||z(x) - z(r)||_2`.

This is an explicit deterministic reference-bank approximation to the frozen all-source-train mean 5-NN distance. It is **not mathematically identical** to the full-reference quantity unless the bank contains all source-train rows. It remains representation-dependent and seed-independent, and would be computed once per source direction and shared across RF seeds.

## Resource and validation plan if approved

At the measured 500,000-reference scale, exact KDTree fit took 5.27 seconds, a 512-query batch took 0.335 seconds (about 1,526 queries/s), and peak process working set was 2.60 GB including the benchmark’s staged-array baseline. The stored standardized bank is about 184 MB; the current exact implementation would process 4.44 GB of standardized references. A 500k bank suggests well under one hour for 4.03M CIC source-test queries at the measured rate, subject to a bounded confirmation run.

If approved, before changing the final experiment manifest:

1. Generate the bank by the hash-priority rule above and record its offset-list hash, data hash, `K`, scaler hash, algorithm and versions.
2. Repeat the selection twice and require an identical offset-list hash and identical distance outputs.
3. On 4,096 deterministic source-test feature rows, compare `K` = 100k, 250k, and 500k banks against the bounded exact 2.4M-reference benchmark. Report median and 95th-percentile relative distance error and Spearman rank correlation. This is feature-only validation; do not use labels or RF outcomes to choose K.
4. Present those measurements for approval. Only then update and commit the CIC E1 experiment manifest with the chosen approximation and launch the final source-only gate.

Until approval, retain the exact frozen definition in the current config, preserve all staged arrays and UNSW outputs, and do not compute bank scores or start CIC seeds.
