# E0/E0.5 Data Governance and Split Design

**Status:** Draft for review before the first pilot  
**Scope:** NF-UNSW-NB15-v3 source and NF-CSE-CIC-IDS2018-v3 target  
**ToN-IoT:** Deferred; excluded from this stage and the first pilot.

## Freeze boundary

This document operationalizes the current repository plan. It does not change
`research_proposal.md` or `methodology_final.md`, and does not authorize model
training. E0/E0.5 artifacts must be reviewed before the UNSW-to-CIC2018 pilot.

## Feature registry

All 53 NetFlow-v3 fields remain visible in the registry. The pipeline must
select columns by name and reorder them to the locked registry. No column is
silently dropped. Proposed roles:

- **Predictive candidate:** numeric flow measurement/protocol fields, pending
  the feature-governance review.
- **Audit/split metadata:** `FLOW_START_MILLISECONDS` and
  `FLOW_END_MILLISECONDS`; retain for chronology and complete-flow checks,
  never pass raw absolute timestamps to the predictive matrix by default.
- **Identifier-like:** `IPV4_SRC_ADDR`, `IPV4_DST_ADDR`, `L4_SRC_PORT`,
  `L4_DST_PORT`, and `DNS_QUERY_ID`. Preserve in audit/split layers; keep out
  of the first pilot matrix pending explicit shortcut-risk review.
- **Targets:** `Label` and `Attack`; never predictive. `Label` is the binary
  evaluation target; `Attack` is reserved for post-freeze family reporting.

This classification is a draft. Any change to the predictive feature set
requires a versioned registry update before fitting.

## UNSW empty and non-finite handling

For numeric predictive candidates, parse empty strings and non-finite values
(including positive infinity) as missing. Fit one replacement value per
feature using only the UNSW training partition: the median of finite training
values. If a training feature has no finite values, use `0.0` and record that
fallback in metadata. Apply the stored values unchanged to UNSW calibration,
UNSW source test, and CIC2018 inference. Do not fit or update replacement
values from either held-out partition or target data. Preserve raw values in
the immutable input and record per-partition replacement counts.

## Proposed source partitions

Use deterministic 60/20/20 UNSW train/calibration/source-test proportions,
consistent with the frozen methodology's recommended starting point. Assign
rows by a stable SHA-256 digest of the canonicalized 53-feature vector, with
the first eight digest bytes interpreted as an unsigned integer modulo 100:

- 0–59: train;
- 60–79: calibration;
- 80–99: source test.

This assignment is independent of both target columns. Identical feature
vectors necessarily receive the same assignment, avoiding duplicate vectors
crossing source partitions. Record the exact seedless hash rule, data hash,
per-partition row counts, and membership digests. This is the primary
reproducible partition proposal; it does not replace the separately reported
temporal-coverage and temporal-control analysis.

## CIC2018 target lockbox

For the first UNSW-to-CIC2018 pilot, the complete CIC2018 feature table is the
target lockbox. Its membership is fixed by the audited file SHA-256 and
canonical row order; no CIC2018 labels may be read by fitting, preprocessing,
calibration, threshold selection, or pilot decisions. Target labels remain
sealed until the model and analysis configuration are frozen. The duplicate
consistency audit is an E0 data-integrity check and is reported separately;
it does not tune model decisions.

## Required overlap checks

Using the same canonical 53-feature digest, report exact-vector intersections
for UNSW train/calibration, train/source-test, calibration/source-test, and
each UNSW partition against the CIC2018 lockbox. Also report repeated vectors
within each partition and any CIC2018 vectors with conflicting `Label` or
`Attack`. Do not automatically delete or relabel rows. Any overlap is reported
with counts and investigated before the pilot; no target labels are used to
change source membership.

## Pending evidence before E0 can close

1. CIC2018 duplicate-vector label/attack conflict counts.
2. Daily temporal coverage and attack-episode summaries for both datasets.
3. Machine-readable 53-feature registry.
4. Exact split membership and cross-boundary overlap report.
5. Preprocessing implementation that persists UNSW-training medians and
   applies them identically to all later partitions.

Until those outputs are generated and reviewed, the pilot remains blocked.
