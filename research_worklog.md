
# Research Worklog

**Project:** Evaluating the Transportability of Lightweight Reliability Signals in Network Intrusion Detection under Compound Distribution Shift

## Documentation policy

### Frozen core documents

The following are frozen:

- `research_proposal.md`
- `methodology_final.md`

A change to either requires identification of a substantive error and explicit confirmation.

### Working documents

The following may evolve:

- `dataset_selection.md`
- `dataset_source_manifest.md`
- `label_mapping_draft.md`
- `experiment_lock_draft.md`
- `methodology_change_log.md`
- this worklog;
- future audit and pilot documents.

## 2026-11-05 — Dataset scope narrowing

### Decision

The initial experiment will actively use only:

- NF-UNSW-NB15-v3
- NF-CSE-CIC-IDS2018-v3

NF-ToN-IoT-v3 remains downloaded but deferred.

### Rationale

The research question does not require three datasets. Two domains already provide:

- in-domain controls;
- both transfer directions;
- a common NetFlow-v3 representation;
- domain shift;
- a conservative compound-shift analysis;
- five reliability signals;
- repeated-seed evaluation;
- attack-miss endpoints;
- review-budget analysis.

Using ToN-IoT immediately would increase scope and data-processing burden without being necessary to answer the primary question.

### Literature support

TAN-IDS itself uses UNSW-NB15 and NF-CSE-CIC-IDS2018 as its principal two-domain cross-dataset setting, with a common NetFlow representation and source-only transfer scenarios. citeturn638957search0turn638957search2

### Operational consequence

The local Codex workflow should initially receive/access only the two active dataset directories.

ToN-IoT should not be included in the first audit or pilot.

### Next step

Use Codex locally to audit only the two active datasets and generate the machine-derived schema, label, family, duplicate, and leakage artifacts.


## 2026-11-05 — Independent review of Codex audit branch

### Verified

- Codex audit branch `codex/nf-v3-dataset-audit` exists.
- Commit `748ddb93b3ed19ff1e94694e06caa36e482a9396` contains the NF-v3 audit artifacts.
- The audit confirms both active datasets are valid NF-v3 packages with 53 features plus `Label` and `Attack`.
- Exact SHA-256 hashes and BagIt integrity checks are recorded.
- The current downloaded files are therefore suitable candidates for the core study.

### Important findings

- CIC2018 contains 628,474 exact duplicate rows and 628,914 repeated 53-feature vectors.
- UNSW contains 14,815 exact duplicate rows and repeated 53-feature vectors.
- UNSW contains empty and positive-infinity values in throughput-related fields.
- Observed CSV feature order differs from the supplied NetFlow-v3 dictionary order; the implementation must canonicalize feature order by name.
- Several fields are identifier/time-like and require explicit feature-governance decisions before training.
- The local UNSW file has 127,693 attack rows versus the earlier catalogue reference of 127,639; the file passes its BagIt integrity check, so the local file count should be documented rather than corrected.

### Experiment-status correction

Independent repository inspection did **not** find committed evidence that the frozen Random Forest five-signal transfer experiment has been completed.

Existing claims about GBDT/temporal or other exploratory experiments must not be counted as completion of the frozen protocol.

### Next step

Complete E0/E0.5 before model training:

1. feature registry;
2. non-finite handling policy;
3. duplicate feature-vector label consistency;
4. temporal/attack-episode audit;
5. source train/calibration/test and target lockbox design;
6. cross-boundary leakage checks;
7. final label/family matrix.

Then run a single controlled Random Forest pilot for UNSW → CIC2018.

## 2026-11-06 — Active-pair E0/E0.5 progress

### Completed on `codex/e0-e05`

- Verified the frozen proposal and methodology in this checkout match
  `origin/main` byte-for-byte; neither was modified.
- Added the existing acquisition/schema audit outputs for only UNSW-v3 and
  CIC-IDS2018-v3 to this project branch. ToN-specific artifacts remain out of
  the active scope.
- Generated `feature_registry.csv` with an explicit draft role for all 53
  features and the two target fields.
- Completed a bounded-memory external-sort pass. CIC2018 has 440 repeated
  feature-vector groups with conflicting `Attack` values and zero with
  conflicting `Label` values. Both source CSVs are not timestamp-ordered;
  daily UTC coverage and a sorted 60-second attack-episode summary are in the
  E0 report.
- Fixed the label-blind baseline partition proposal at UNSW 60/20/20 by
  SHA-256 of the canonical 53-feature vector; CIC2018 is the target lockbox.
  The exact-vector precheck found zero source cross-partition duplicates and
  zero exact 53-feature intersections with CIC2018.
- Implemented the source-only finite-value policy and fitted exact medians on
  the 1,418,952-row UNSW training partition. Replacements are 162.0 for
  `SRC_TO_DST_SECOND_BYTES` and 75.37562877263582 for
  `DST_TO_SRC_SECOND_BYTES`; no dataset was transformed.
- Added the temporal control from the frozen protocol. The 60%/80% UNSW time
  boundaries are 2015-02-18 03:20:22.862 UTC and 07:57:39.998 UTC; complete-flow
  checks plus the 60-second embargo exclude 7,252 rows. Exact feature-vector
  groups do not cross temporal partitions.
- Added a direction-canonicalized 5-tuple session control and exact flow-key
  check: 63,898 repeated session groups (497,708 extra rows) and 24,071
  repeated full flow-key groups (24,081 extra rows). No rows were removed.
- The strict host-disjoint sensitivity retains 1,060,409 train, 46,314
  calibration, and 66,299 test flows, while excluding 1,192,402 flows; only
  27/6/7 distinct hosts remain in those partitions. Treat this as a limited
  sensitivity, not broad host-generalization evidence.
- Reviewed constants/domain shortcuts: `FTP_COMMAND_RET_CODE` is zero in
  CIC2018 but varies from 0 to 501 in UNSW. Absolute time, endpoint addresses
  and ports, and `DNS_QUERY_ID` remain explicitly flagged in the registry.

### Remaining before the frozen-methodology pilot

- Review and freeze feature governance and the conservative family mapping.
- Complete the pilot lock draft with remaining RF parameters, seed list, exact
  predictive columns, and sensitivity settings.
- Run the source-only E1 stability gate before any target-label evaluation.
- Commit a freeze manifest and use the target-label firewall for final target
  evaluation. Its feature-only access interface is implemented, but no lock
  manifest exists yet.
- Treat the strict host-disjoint sensitivity as limited due to sparse held-out
  host support; do not claim broad host generalization.

The machine-readable and human-readable E0 results are under
`reports/nf_v3_audit/`. The E0/E0.5 branch is pushed; the first Random Forest
pilot has not been run.
