# NF-v3 Audit Review and E0 Completion Plan

**Status:** Working research-control document  
**Date:** 2026-11-05  
**Reviewed branch:** `codex/nf-v3-dataset-audit`  
**Reviewed commit:** `748ddb93b3ed19ff1e94694e06caa36e482a9396`

## 1. Executive verdict

The Codex dataset audit is genuine and useful. The audit branch contains a complete machine-generated audit report, JSON results, schema table, target-value counts, and the audit script.

However, the audit does **not** establish that the frozen transfer experiment is complete.

The repository branch reviewed contains the frozen methodology plus audit artifacts, but no committed Random Forest transfer experiment artifacts corresponding to the frozen five-signal protocol. Search of the repository for the claimed transfer experiment, GBDT temporal experiment, attack-miss AUPRC result, and per-seed transfer results did not identify such committed results.

Therefore:

> The binary NF-UNSW-NB15-v3 ↔ NF-CSE-CIC-IDS2018-v3 transfer experiment must be treated as **not yet complete under the frozen protocol**.

Existing GBDT/temporal or other exploratory runs must not be counted as completion of the Random Forest reliability study.

## 2. What the audit successfully establishes

### Dataset identity

Both active datasets are valid NF-v3 BagIt packages associated with the University of Queensland dataset identifier and pass their supplied BagIt SHA-1 integrity checks.

### File hashes

NF-CSE-CIC-IDS2018-v3:

`242a6971cc801eae621b1fc4d966db2cd0af9cc866805f36a6fc5d0058dfbb74`

NF-UNSW-NB15-v3:

`4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`

### Row/column counts

CIC2018:

- 20,115,529 rows
- 55 columns
- 53 model-feature fields + Label + Attack

UNSW:

- 2,365,424 rows
- 55 columns
- 53 model-feature fields + Label + Attack

### Schema

All 53 expected features are present in both datasets.

Important caveat:

> Observed column order does not match the order in the supplied feature dictionary.

This is not inherently a data error, but the modeling pipeline must construct the canonical feature matrix by **column name**, then explicitly reorder it to the locked feature registry before converting to arrays.

## 3. Important data-quality findings

### UNSW non-finite/empty values

The audit reports:

- `SRC_TO_DST_SECOND_BYTES`: 63,425 empty values and 59,068 positive-infinity values.
- `DST_TO_SRC_SECOND_BYTES`: 122,493 positive-infinity values.

These are real preprocessing constraints and must be handled by a deterministic source-fitted policy.

No target-derived imputation or replacement statistics are allowed.

### Duplicate rows

CIC2018:

- 628,474 exact duplicate rows beyond the first (~3.12% of rows).
- 628,914 duplicate 53-feature vectors beyond the first (~3.13%).

UNSW:

- 14,815 exact duplicate rows beyond the first (~0.63%).
- 14,815 duplicate 53-feature vectors beyond the first (~0.63%).

Duplicates are **not** automatically a reason to delete records. The critical question is whether duplicates cross training/calibration/test/target boundaries.

### Feature-vector duplicate discrepancy

CIC2018 has 440 more repeated 53-feature vectors than exact duplicate full rows.

This requires a focused consistency check:

> Do repeated feature vectors ever occur with conflicting Label/Attack values?

If yes, this is a potentially important data-quality issue that must be resolved before modeling.

## 4. Feature governance findings

The audit identifies fields that can behave as host/session/time identifiers:

- IPV4_SRC_ADDR;
- IPV4_DST_ADDR;
- source/destination ports;
- FLOW_START_MILLISECONDS;
- FLOW_END_MILLISECONDS;
- DNS_QUERY_ID.

The frozen methodology already requires identifier fields to receive explicit feature-registry treatment before training.

Therefore this is **not currently a frozen-methodology error**.

The next artifact must explicitly classify each field as:

- predictive feature;
- split/audit metadata only;
- excluded.

No silent inclusion of identifiers is permitted.

## 5. Catalogue-count discrepancy

The local UNSW file contains 127,693 attack rows.

The earlier UQ catalogue reference count is 127,639.

The difference is 54 rows.

Because the actual downloaded file:

- passes the BagIt manifest;
- has an exact recorded SHA-256;
- has internally consistent Label/Attack counts,

the local file should be treated as authoritative for the experiment.

The discrepancy must be documented rather than "corrected" by deleting rows.

## 6. What remains in E0

E0 should not be declared complete yet.

Remaining required outputs:

1. temporal distribution/coverage report;
2. attack-episode/run structure where derivable;
3. duplicate-feature-vector label consistency;
4. split-boundary leakage design and precheck;
5. explicit feature registry;
6. exact preprocessing policy for empty/Inf values;
7. conservative source/target family matrix;
8. source/target sample construction rules;
9. confirmation that audit artifacts are reproducible from the committed script.

## 7. Required next stage

The next implementation stage is **E0.5: split design and feature-governance audit**, not model training.

Sequence:

```
Existing dataset audit
        ↓
Feature registry
        ↓
Non-finite handling policy
        ↓
Duplicate/label consistency check
        ↓
Temporal/episode audit
        ↓
Source train/calibration/test design
        ↓
Target lockbox design
        ↓
Cross-boundary leakage check
        ↓
E0 completion
        ↓
Pilot E1
```

## 8. Experiment-completion status

The repository evidence does not support a claim that the frozen Random Forest five-signal transfer experiment is complete.

The following must not be counted as completion unless independently verified against the frozen methodology:

- GBDT experiments;
- temporal reliability experiments;
- monotonicity sensitivity experiments;
- undocumented local runs;
- results without committed configurations and run manifests.

## 9. Frozen-document status

No changes to:

- `research_proposal.md`
- `methodology_final.md`

are required at this stage.

The audit findings fit within the existing methodology's feature-governance and data-audit provisions.

## 10. Audit branch handling

The Codex audit branch should remain separate until E0 is complete and the audit has been reviewed.

Do not merge the audit branch into `main` merely because it contains valid audit artifacts.

Once E0 is complete, the audited artifacts can be merged or selectively promoted after review.
