
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

### 2026-11-06 — Family mapping audit added

- Added a reproducible, label-inventory-only generator and compact family
  mapping report for the active UNSW-v3 → CIC2018-v3 pair.
- Retained every observed raw family label and its local audited count. The
  documentation crosswalk normalizes display names only; it does not alter
  dataset labels or use labels to select modeling decisions.
- Recorded DoS as the only directly shared documented family in this draft;
  kept UNSW DoS versus CIC DDoS and other plausible overlaps explicitly
  ambiguous. All target-exclusive claims remain withheld.
- Marked CIC WebAttacks as an inference because the three local web labels sum
  to the catalogue aggregate. This inference remains subject to review.
- ToN-IoT remains outside the active experiment. The frozen proposal and
  methodology hashes were checked and their files are unchanged.
- Mapping review, exact feature governance, complete RF configuration and seed
  lock, source-only E1 stability gate, and the target-label firewall freeze
  manifest remain blockers before the first UNSW→CIC2018 Random Forest pilot.

### 2026-11-06 — Compact representation crosswalk drafted

- The frozen methodology names a TAN-IDS-inspired 8-feature sensitivity but
  does not list the corresponding v3 columns. Added a draft crosswalk from the
  cited paper's Table 5 to the audited v3 schema, keeping all transformations
  unapplied.
- Flagged required review of bounded numeric ports, protocol-code alignment,
  source/target TCP-flag semantics, and zero-duration handling for derived
  packets-per-second. The source paper is used only for this representation;
  its data filtering, split, and adaptation procedures are not adopted.
- No target labels were used, and no model or data transformation was run.
- The representation crosswalk, exact primary predictive feature list, and
  complete model/seed lock remain review gates before E1.

### 2026-11-06 — Feature-only checks for compact representation

- Added a bounded-memory reader that requests only `FLOW_DURATION_MILLISECONDS`
  and `PROTOCOL`, in 250,000-row chunks. It does not request `Label` or
  `Attack`; both downloaded files remain unchanged.
- The source scan found 122,493/2,365,424 zero-duration rows (5.18%); target
  found 0/20,115,529. For the proposed derived packets-per-second feature, a
  zero-duration denominator must be treated as missing and replaced by a
  median fitted only on source training rows. This derived median has not yet
  been fitted and the feature has not been materialized.
- Protocol values are numeric IP protocol identifier bytes per the supplied
  dictionary. Source has 255 observed codes and target has 6; shared codes are
  1, 2, 6, 17, and 47, while 58 appears only in target. The IANA registry
  identifies these as standardized IP protocol numbers, with 58 denoting
  IPv6-ICMP. Marginal code-set differences are documented; no remapping was
  applied.
- Both protocol and cumulative TCP flag fields can use direct common v3
  columns. Ports remain the unresolved governance decision for the compact
  representation. No target labels were accessed.

### 2026-11-06 — RF pre-pilot settings made reviewable

- Added a machine-readable candidate configuration and human-readable decision
  sheet. The draft preserves the methodology's 200 trees and minimum leaf size
  5, proposes explicit documented classifier defaults for other parameters,
  and lists ten seeds (0–9). No estimator was instantiated or fit.
- The local environment is Python 3.14.7 with no scikit-learn installation;
  no dependency lock file exists. A compatible pinned runtime is required
  before E1 and before a freeze manifest can be produced.
- The frozen methodology asks for stable E1 results across seeds but supplies
  no numeric acceptance tolerance. That criterion remains to be defined before
  E1; no arbitrary threshold was added to the frozen protocol.

### 2026-11-06 — Primary feature list made reviewable

- Added a generator and explicit 53-row decision table from the audited
  dictionary and current feature registry. It proposes all 46 shared
  `predictive_candidate` fields and explicitly marks seven timestamp or
  identifier-like fields as outside the candidate predictive matrix.
- The proposal retains the complete registry and raw inputs. It is bound to
  the audited source/target SHA-256 values and is not approved or used for
  fitting. `FTP_COMMAND_RET_CODE` remains visible in the proposed list with
  the documented target-constant caution.
- Target labels and label counts do not determine the proposed feature list;
  no raw dataset rows were read by the generator and no model was trained.
