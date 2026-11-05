# UNSW source temporal and group controls

**Input:** NF-UNSW-NB15-v3, audited SHA-256 `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`.
**Generated:** 2026-11-06 (Asia/Kolkata).
**Method:** label-blind; details and exact counts are in `e0_source_controls.json`.

## Temporal source control

Boundaries use start-time order statistics at floor(0.60N) and floor(0.80N), with no label access. The resulting timestamps are:

| Boundary | UTC |
|---|---|
| 60% (`b1`) | 2015-02-18 03:20:22.862 |
| 80% (`b2`) | 2015-02-18 07:57:39.998 |

With complete-flow assignment and a 60-second embargo at each boundary, the row counts are:

| Partition | Rows |
|---|---:|
| Train | 1,417,416 |
| Calibration | 469,631 |
| Source test | 471,125 |
| Excluded at boundaries/embargo | 7,252 |

The temporal partitions had zero repeated 53-feature-vector groups across partition boundaries. The exact source/target feature-vector intersection remains zero as reported in `E0_TEMPORAL_CONFLICT_REPORT.md`.

## Session and flow-key audit

The direction-canonicalized session key uses the observed source/destination IP and port endpoint pairs plus `PROTOCOL`. Whole sessions are assigned by a stable SHA-256 60/20/20 rule. There are 63,898 repeated session-key groups, with 497,708 rows beyond the first in those groups. Since assignment is by the session key, a session cannot cross partitions by construction.

The stricter flow key adds the exact start and end timestamp strings to the canonical endpoints and protocol. The audit found 24,071 repeated flow-key groups and 24,081 rows beyond the first. These rows are reported, not removed.

## Constants and potential domain/capture leakage

No constant columns were found in UNSW. In CIC2018, `FTP_COMMAND_RET_CODE` is constant at zero, while UNSW ranges from 0 to 501; keep it flagged as a possible domain-specific signal, not silently removed. The audit/registry also flags absolute start/end time, source/destination IPs and ports, and `DNS_QUERY_ID` as potential capture, host/service, transaction, or timestamp shortcuts. The two datasets have non-overlapping years in their observed time ranges. These fields remain explicitly classified in the registry; this audit did not fit a dataset-identity model or use labels to select features.

## Host-disjoint sensitivity

Each observed IP endpoint is independently assigned by a fixed salted SHA-256 60/20/20 rule; a flow is retained only if both endpoints map to the same partition. This produces 1,060,409 train rows, 46,314 calibration rows, and 66,299 source-test rows, while excluding 1,192,402 cross-partition flows. The retained partitions contain 27, 6, and 7 distinct hosts, respectively.

This strict host-disjoint construction leaves sparse calibration and test host support and excludes about half of all flows. Treat it as a limited sensitivity analysis; it cannot support broad host-generalization claims. The source-only hash split remains the baseline partition proposal.

## Decision and limits

These are control constructions and integrity counts only. No model was trained and no raw row was changed. The very short temporal intervals between `b1` and `b2` reflect the concentration of UNSW rows on 2015-02-18; retain that context when interpreting the temporal control. Review the split proposal, feature registry, family mapping, and target-label firewall before locking the first pilot.
