# UNSW Source E1 Staging Report

**Status at report generation:** Source-only partitions staged; fitting had not yet started. Current partial results are in `SOURCE_E1_PARTIAL_REPORT.md`.
**Config:** `source-e1-lock-1`
**Source SHA-256:** `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5` (rechecked against the audited file).
**Target access:** None. CIC2018 files and labels were not opened.

## Staged arrays

| Partition | Rows | Feature matrix |
|---|---:|---|
| Train | 1,418,952 | `train_X.npy`, 46 columns, float32 |
| Calibration | 473,301 | `calibration_X.npy`, 46 columns, float32 |
| Source test | 473,171 | `source_test_X.npy`, 46 columns, float32 |

Binary source labels are stored separately as int8 arrays. Empty and non-finite values in the two audited columns were replaced with the previously recorded UNSW-train medians. The raw CSV was not changed.

The staged arrays total 437,604,208 bytes and are kept under the ignored local path `data/processed/source-e1-lock-1`; only their hashes and summary are committed. `scripts/stage_source_e1.py` now verifies the source SHA-256 before staging and refuses to overwrite an existing staging directory.

## Fit status

At report generation, the machine had 15.7 GiB total physical memory, with 1.9 GiB available before staging and 2.5 GiB afterward. The user later instructed us to proceed; six source-only RF fits completed. Peak model memory was not instrumented. Machine-readable details and staged-file hashes are in `source_e1_stage_report.json`; current partial model results are in `source_e1_seed_results.json`. The target remains sealed.
