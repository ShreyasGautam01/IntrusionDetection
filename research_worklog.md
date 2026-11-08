
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
  NumPy 2.5.2 and pandas 3.0.6 were present. The official scikit-learn 1.9.1
  documentation sets Python 3.11 as its minimum; the detected Python meets
  this requirement. Continued below with a project-local lock and environment.
- The frozen methodology asks for stable E1 results across seeds but supplies
  no numeric acceptance tolerance. That criterion remains to be defined before
  E1; no arbitrary threshold was added to the frozen protocol.

### 2026-11-06 — Isolated experiment runtime resolved

- Added `pyproject.toml` with direct dependency pins and generated `uv.lock`;
  the lock contains exact transitive versions and Windows CPython 3.14 wheels.
- Pinned the resolver itself to uv 0.11.19 so future lock refreshes are
  attributable and reproducible.
- Installed the lock into the repository's ignored `.venv` (not the global
  Python environment). Version-only imports confirmed Python 3.14.7, NumPy
  2.5.2, pandas 3.0.6, SciPy 1.18.1, and scikit-learn 1.9.1.
- Recorded the runtime and lock hash in RF config draft `rf-draft-4`. No
  estimator was instantiated or fit, no target labels were used, and no model
  experiment was run.

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

### 2026-11-06 — Batched target feature-only reader

- Added `iter_target_feature_batches` to the lockbox reader with a default
  batch size of 8,192 rows. It returns only explicitly selected feature tuples
  and zero-based starting row numbers; `Label` and `Attack` are rejected.
- Kept the row-wise feature-only API by implementing it over one-row batches.
  Both paths validate requested columns, duplicate headers, and row widths.
- This makes the 20.1-million-row CIC lockbox practical to score in bounded
  memory once a future model/config is frozen. The feature API does not index
  or return label values, change the dataset, or authorize evaluation.
- No tests were run and no model was trained; the target-label freeze manifest
  is still absent.

### 2026-11-06 — Pre-pilot memory plan

- Calculated dense float32 input lower bounds from the already-audited row
  counts and the 46-column feature proposal; no dataset rows were scanned.
- The source train matrix alone is about 249 MiB. The full CIC2018 46-column
  matrix would be about 3.45 GiB, versus about 1.44 MiB of numeric values per
  default 8,192-row batch. These estimates exclude parsing, copies, model
  structures, and estimator workspace.
- Documented target streaming and a possible disk-backed source staging plan
  for after feature freeze. Actual Random Forest peak memory remains unmeasured
  and must be observed during the eventual source-only E1 gate.
- No target labels were read, no dataset was transformed, and no model was
  trained.

### 2026-11-06 — NetFlow-v3 family-count source reconciliation

- Compared existing BagIt-verified active-pair label counts with Table 3 of the versioned NetFlow-v3 release paper and the current UQ catalogue HTML; no raw dataset scan was repeated.
- The local UNSW family counts match the versioned paper exactly. The current UQ HTML table has three conflicting UNSW counts (Analysis, Backdoor, Shellcode), and its prose attack total is 127,639 versus 127,693 in its own family-table sum and the local/release-paper counts. CIC counts match.
- Added per-label and aggregate comparisons to `family_mapping_draft.csv` and documented the discrepancy in the family report and label-mapping draft. No labels, rows, or dataset files were changed.
- This is a source-documentation correction only; the family mapping remains draft, and target-exclusive claims remain withheld. No features were selected from labels and no model was trained.

### 2026-11-06 — Source-only E1 stability gate prepared for review

- Mapped the frozen E1 acceptance statement to a proposed run/reporting procedure in `reports/nf_v3_audit/E1_STABILITY_GATE_DRAFT.md`.
- The draft requires fixed source partitions/configuration across the ten proposed seeds, per-seed detector and reliability outputs, seed-spread summaries, ranking agreement, and a repeated fixed-seed reproducibility check.
- It deliberately sets no numeric pass tolerance: the frozen protocol requires stability but does not define a cutoff. Owner review is still required before any E1 fitting.
- No model was instantiated or trained, target rows/labels were not accessed, and neither frozen core document was modified.

### 2026-11-06 — Source-only E1 setup consolidated

- Consolidated the 46-feature primary candidate, deterministic UNSW 60/20/20 hash split, source-training-only finite replacements, fixed 200-tree/minimum-leaf-5 Random Forest, ten seeds, and source-only sigmoid calibration in `reports/nf_v3_audit/source_e1_config.json`.
- Fixed source-only settings for confidence, forest disagreement, standardized kNN distance, split conformal at alpha 0.10, and Isolation Forest. The source-only config cannot access CIC2018 data or unlock target evaluation.
- Hardware preflight showed 15.7 GiB physical RAM total but 1.9 GiB available at inspection time. The planned numeric source matrices require about 415 MiB before the RF trees and working copies; no training was started because peak model memory is not yet bounded.
- The source-only config reports all ten seeds and their variation; no arbitrary numeric pass tolerance was inserted. Target evaluation remains sealed pending interpretation of the frozen stability gate.

### 2026-11-06 — UNSW source E1 matrices staged

- Added `scripts/stage_source_e1.py`, which verifies the audited source SHA-256, partitions by the locked feature-vector digest, applies the recorded source-train replacements, and writes disk-backed arrays. It refuses overwrite and never opens CIC2018.
- Staged the 1,418,952/473,301/473,171 train/calibration/test rows in the locked 46-column order. The current UNSW source hash rechecked exactly against the audit.
- Added `SOURCE_E1_STAGE_REPORT.md` and `source_e1_stage_report.json` with the array hashes and execution limits. Local matrices are ignored under `data/processed/`; raw data are unchanged.
- At the time, model fitting was deferred for low free RAM. The user later directed us to proceed; seeds 0–5 completed under sequential/three-worker execution. Forest peak memory was not instrumented.

### 2026-11-06 — Partial source-only E1 results and handoff

- Completed source-only RF seeds 0–5 using the locked 200-tree configuration. Current implemented outputs cover detector metrics, sigmoid-calibrated confidence, and RF disagreement only. CIC2018 was not read.
- Aggregated the six seeds in `SOURCE_E1_PARTIAL_REPORT.md` and `source_e1_seed_results.json`. Each run had ten source-test attack misses; treat ranking metrics as sparse-event diagnostics. Seed 1 recorded 6,683 seconds fit time versus 219–268 seconds for the other completed seeds; it remains included and needs runtime investigation.
- Stopped after seeds 3–5 completed and before seeds 6–9 launched, per user request. Prepared `PROJECT_HANDOFF.md` with repository location, guardrails, staged-data path, run commands, and remaining methodology work.
- No final cross-domain experiment or target-label evaluation was performed. Frozen core documents are unchanged.

### 2026-11-08 — Partial-result recovery audit

- Verified the hashes of all six ignored stage arrays against `stage_manifest.json`; verified the active config hash against the partial aggregate.
- Recomputed detector and reliability metrics from each saved seed's source-test arrays. Seeds 0–5 are internally consistent for the three outputs that were produced: the RF detector, calibrated confidence, and RF disagreement. Their parameters match the locked RF subconfiguration.
- Confirmed that the saved runs are not complete for the five-signal config: kNN feature-space distance, split conformal, and Isolation Forest are absent. The original seeds have no saved calibrated probabilities for the conformal calibration subset.
- Tried the exact configured standardized Euclidean 5-NN distance calculation in a separate full-run output directory. After more than 12 minutes it had not completed; stopped without a result or approximate substitute. Original seed artifacts remain unchanged.
- The ten-seed, five-signal source-only stability gate remains incomplete. No target data or labels were opened, and target evaluation remains locked.

### 2026-11-08 — Bounded E1 compute benchmark and execution lock

- Benchmarked exact StandardScaler + KDTree Euclidean 5-NN on actual UNSW source arrays up to 800,000 reference rows and 2,048 queries. At 800k, throughput was 437 queries/s for 512 queries and approximately 427–456 queries/s across query sizes. Tail-scaling estimates put the full 1.419M-reference / 473k-query run at 38–55 minutes, with 1.0–1.5 GiB estimated peak working set. Selected exact one-worker execution with query checkpoints; no approximation.
- Benchmarked 200-tree RF at 25% of source train: one worker fit in 42.42s, peak 518MB; two concurrent workers completed two fits in 49.79s, peak 537MB. CPU use rose from 0.97 to 1.94 cores; estimated throughput gain was 1.70×. Selected two workers with OpenMP/BLAS/RF internal counts capped at one.
- Verified distance is independent of RF seed and is computed once/shared. Isolation Forest does not consume RF output but is configured with `random_state` equal to each seed, so fit once per declared seed. Confidence, RF disagreement, and conformal outputs depend on the RF seed.
- Ran a 5,000-train / 2,000-calibration / 2,000-test source-only five-signal smoke test. All five arrays had expected shape and finite values. The smoke test had zero attack misses in its test prefix, so ranking metrics are not interpreted.
- Froze `source_e1_manifest.json` after benchmark/smoke and before full E1 computation. Target remains sealed; no target arrays were opened.

### 2026-11-08 — Complete source-only five-signal E1

- Ran the exact full-reference 5-NN distance once: all 473,171 source-test queries against 1,418,952 source-train references, 46 features, completed in 1,746.4s (29m06s; 271 queries/s end-to-end). Validated shape, nonnegative finite values, and output hash.
- Completed all five configured signals for seeds 0–9 with two concurrent workers and one OpenMP/BLAS/RF thread per worker. Seeds 0–5 refits exactly reproduced their recovered probability, prediction, and disagreement arrays; those original artifacts were reused. The refits also supplied the missing calibration probabilities needed for split conformal. Seeds 6–9 are newly generated.
- Completed an exact separate seed-0 repeat. All seven per-row arrays, detector/signal metrics, and conformal quantile matched exactly.
- The first repeat invocation reached the runner's deliberate no-overwrite guard because its alternate output path was not applied; it wrote no output and changed no recovered result. The corrected repeat wrote under a separate directory and matched exactly.
- Verified all ten per-seed output hashes and metric reports. Each seed had ten source-test attack misses. Detector metrics were tightly clustered; confidence/disagreement captured all misses at 5%, distance captured six, and conformal/Isolation Forest captured none.
- Cross-seed rank correlation minima were 0.605 (confidence), 0.307 (RF disagreement), 1.0 (distance), 0.592 (split conformal), and 0.935 (Isolation Forest). The frozen config provides no numeric acceptance tolerance, so target transfer remains locked pending project-level stability interpretation. No target data or labels were accessed.
