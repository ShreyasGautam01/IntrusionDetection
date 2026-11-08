
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
  `origin/mai