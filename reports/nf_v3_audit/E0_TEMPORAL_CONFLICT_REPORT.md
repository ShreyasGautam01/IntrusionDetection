# E0 temporal and duplicate-label checks

**Generated:** 2026-11-05T18:39:49Z  
**Inputs:** the exact NF-UNSW-NB15-v3 and NF-CSE-CIC-IDS2018-v3 CSVs listed in `e0_results.json`; SHA-256 values were matched to the acquisition audit.  
**Scope:** E0 data checks only; no modeling and no ToN-IoT.

## CIC2018 duplicate-vector label consistency

Among repeated 53-feature vectors, **440 vector groups have conflicting `Attack` values**. **Zero groups have conflicting `Label` values.** These 440 groups account for the audit's difference between repeated feature vectors (628,914 beyond first) and exact duplicate full rows (628,474 beyond first). No row was removed or relabeled. The conflict counts are an integrity finding only; labels were not used for partition assignment or modeling decisions.

## Temporal coverage

Dates below are UTC calendar days with at least one valid timestamp. Daily benign/attack counts use the dataset's existing `Label`/`Attack` fields for descriptive audit only.

| Dataset | Valid rows | First flow start (UTC) | Last flow start (UTC) | Capture days | Attack rows | Sorted 60-second episodes |
|---|---:|---|---|---:|---:|---:|
| NF-UNSW-NB15-v3 | 2,365,424 | 2015-01-22 11:49:36.907 | 2015-02-18 12:29:24.927 | 3 | 127,693 | 18 |
| NF-CSE-CIC-IDS2018-v3 | 20,115,529 | 2018-02-14 12:28:07.705 | 2018-03-02 20:04:25.524 | 11 | 2,600,903 | 27 |

UNSW capture-day counts (rows; attacks): 2015-01-22 (1,095,574; 17,462), 2015-01-23 (39,778; 0), 2015-02-18 (1,230,072; 110,231).

CIC2018 capture-day counts (rows; attacks): 2018-02-14 (2,138,838; 575,194), 2018-02-15 (1,665,321; 97,340), 2018-02-16 (1,784,129; 205,626), 2018-02-20 (1,829,859; 288,589), 2018-02-21 (2,712,803; 1,035,761), 2018-02-22 (2,040,128; 2,538), 2018-02-23 (1,933,002; 0), 2018-02-27 (828; 0), 2018-02-28 (2,032,727; 84,327), 2018-03-01 (2,147,533; 103,825), 2018-03-02 (1,830,361; 207,703).

Episode definition: sort all rows labeled attack by numeric flow-start time; a new episode begins when the next attack flow starts more than 60 seconds after the maximum end time observed in the current episode. This is a deterministic temporal grouping heuristic, not a ground-truth campaign identity. The source CSV row order is not timestamp-monotone in either dataset, so chronology must be derived from timestamp values rather than row order.

## Label-blind split and exact-vector overlap precheck

The E0.5 proposal assigns each UNSW feature vector by SHA-256 of the canonical 53 raw feature strings: first eight digest bytes modulo 100; 0–59 train, 60–79 calibration, 80–99 source test. All CIC2018 rows form the target lockbox. Membership does not read labels. Resulting UNSW row counts are 1,418,952 train, 473,301 calibration, and 473,171 source test. CIC2018 lockbox contains 20,115,529 rows.

Exact 53-feature-vector intersections were zero between all UNSW source partitions and between each UNSW partition and the CIC2018 lockbox. The same digest determines a vector's UNSW partition, so within-source cross-partition overlap is zero by construction; CIC cross-domain zero is observed by the complete streamed key comparison.

## Family mapping guard

`family_inventory.csv` lists every observed raw `Attack` value and exact row count for the active pair. `family_matrix_draft.csv` expands the source/target combinations but marks all as unmapped pending documentation review. The broad DoS rows are only a candidate semantic correspondence; no equivalence or target-exclusive-family claim is asserted. These files are descriptive and do not define binary model behavior.

## Limitations and status

These summaries close the requested timestamp and duplicate-label inventory checks, but **do not by themselves close E0 or authorize the pilot**. Review the hash partition proposal against the frozen temporal and host/session controls, finalize the feature registry and family matrix, and implement/test persisted UNSW-training-only replacements for empty and non-finite numeric values before fitting any model. Machine-readable full daily counts, episode-size histograms, exact split counts, conflict counts, and overlap counts are in `e0_results.json`.
