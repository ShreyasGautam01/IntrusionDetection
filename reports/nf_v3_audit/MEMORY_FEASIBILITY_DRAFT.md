# Pre-Pilot Memory Feasibility (Draft)

**Status:** Planning estimate only. No dataset rows were read and no model was trained.
**Configuration:** `memory-estimate-draft-1`; machine-readable values are in `memory_estimate_draft.json`.

## Dense numeric input lower bounds

The estimates assume a dense `float32` matrix (4 bytes per value) and the current, unapproved 46-column primary feature proposal. They do not include labels, string parsing, object/array overhead, preprocessing copies, estimator workspace, or Random Forest trees.

| Partition | Rows | Candidate columns | `float32` matrix lower bound |
|---|---:|---:|---:|
| UNSW train | 1,418,952 | 46 | 249 MiB |
| UNSW calibration | 473,301 | 46 | 83 MiB |
| UNSW source test | 473,171 | 46 | 83 MiB |
| All UNSW partitions together | 2,365,424 | 46 | 415 MiB |
| CIC2018 target, full table | 20,115,529 | 46 | 3.45 GiB |
| CIC2018 target, 8,192-row batch | 8,192 | 46 | 1.44 MiB |

At the full 53-feature interface, the CIC2018 dense `float32` feature matrix alone would be about 3.97 GiB. These are array-size calculations from the existing audited row counts and the draft feature count, not observed peak memory.

## Processing recommendation

- Keep CIC2018 prediction streaming through `iter_target_feature_batches` at the default 8,192 rows; convert each selected batch to the locked numeric dtype, score it, and write only the compact prediction outputs needed for evaluation.
- Do not create a full CIC2018 feature matrix in RAM. The raw CSV is 4.22 GB and a numeric matrix would require at least the bounds above before model and runtime overhead.
- For source training, stream the chosen columns into a disk-backed staging matrix after the feature set and transformations are frozen. Fit only from the source training partition. Whether scikit-learn copies that matrix and the Random Forest's peak memory remain to be measured in E1; the lower-bound table is not a capacity guarantee.
- Keep calibration and source-test arrays partitioned and load each only when needed. Do not stage all source splits together without a measured reason.

## Reproducibility and limits

Source/target row counts and file SHA-256 values are inherited from `audit.json`; the exact values and the 46-feature assumption are recorded in `memory_estimate_draft.json`. The estimate does not inspect target labels, validate final feature governance, or change the split. Recalculate if the feature set or split counts change.
