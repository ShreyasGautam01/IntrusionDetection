
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
