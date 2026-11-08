# Partial UNSW Source E1 Results

**Status:** Six-seed source-only pilot; E1 stability gate incomplete.
**Configuration:** `source-e1-lock-1` · **Completed seeds:** 0–5 · **Remaining:** 6–9.
**Target access:** None. CIC2018 files and labels were not read.

All staged array hashes and all six saved partial seed artifacts were checked against their metadata and recomputed source-test metrics. See `SOURCE_E1_RECOVERY_AUDIT.md` and `source_e1_recovery_audit.json`. These six artifacts contain only RF, calibrated confidence, and disagreement outputs; they do not complete the five-signal configuration.

## Per-seed results

| Seed | RF fit (s) | Accuracy | Attack AUPRC | Attack misses | Confidence miss AUPRC | RF disagreement miss AUPRC |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 226.2 | 0.999960 | 1.000000 | 10 | 0.1685 | 0.0887 |
| 1 | 6683.2 | 0.999960 | 1.000000 | 10 | 0.1573 | 0.1019 |
| 2 | 219.3 | 0.999968 | 1.000000 | 10 | 0.1664 | 0.1248 |
| 3 | 257.8 | 0.999962 | 1.000000 | 10 | 0.1652 | 0.1289 |
| 4 | 254.3 | 0.999962 | 1.000000 | 10 | 0.1747 | 0.1182 |
| 5 | 268.4 | 0.999964 | 1.000000 | 10 | 0.1646 | 0.1168 |

Accuracy ranged from 0.999960 to 0.999968; attack AUPRC ranged from 1.000000 to 1.000000. Each run had ten source-test attack misses. Both implemented reliability scores captured all ten at the 1% review budget, but the small event count limits interpretation.

## Limits and remaining work

- The current runner computes the detector, sigmoid-calibrated confidence, and tree disagreement only. kNN distance, split conformal reliability, and Isolation Forest remain unimplemented.
- Seeds 6–9 were not started. The ten-seed stability gate is incomplete.
- Seed 1 records 6,683 seconds for the RF fit; the other five fits took 219–268 seconds. Preserve the anomaly and investigate execution history; do not drop seed 1 based on its results.
- These are in-domain UNSW results only. No cross-domain claim is supported, and target evaluation remains locked.
- Per-row score arrays and predictions stay local under ignored `data/processed/source-e1-lock-1/seed-*/`. Compact metrics and hashes are in `source_e1_seed_results.json`.
