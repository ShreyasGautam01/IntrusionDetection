# Research Worklog

**Project:** Evaluating the Transportability of Lightweight Reliability Signals in Network Intrusion Detection under Compound Distribution Shift

## Documentation policy

### Frozen core documents

The following are frozen:

- `research_proposal.md`
- `methodology_final.md`

They should not be edited during normal iteration.

A core-document change requires:

1. identification of a substantive error;
2. explanation of why the existing text is incorrect;
3. proposed replacement;
4. explicit confirmation before modification.

### Working documents

The following may evolve:

- `dataset_selection.md`
- `experiment_lock_draft.md`
- future dataset manifests;
- label-mapping documentation;
- leakage audits;
- implementation notes;
- pilot reports;
- result ledgers.

The repository should therefore distinguish stable research decisions from implementation learning.

## 2026-11-05 — Dataset/experiment control pass

### Completed

- Confirmed repository state.
- Confirmed frozen core documents exist:
  - `research_proposal.md`
  - `literature_review.md`
  - `methodology_final.md`
- Added `dataset_selection.md`.
- Added `experiment_lock_draft.md`.
- Added this worklog.
- Verified the current UQ NetFlow-v3 catalogue.
- Confirmed NetFlow-v3 uses 53 extended NetFlow features.
- Confirmed current catalogue counts and family labels for NF-UNSW-NB15-v3, NF-CSE-CIC-IDS2018-v3, and NF-ToN-IoT-v3.
- Confirmed TAN-IDS as an important precedent for the compact 8-feature sensitivity representation and source-only transfer methodology.

### Current decision

Primary datasets:

- NF-UNSW-NB15-v3
- NF-CSE-CIC-IDS2018-v3

Replication:

- NF-ToN-IoT-v3

Primary representation:

- 53-feature NetFlow-v3

Sensitivity representation:

- compact 8-feature NetFlow interface inspired by TAN-IDS

### Important caution discovered

The attack taxonomies of UNSW-NB15-v3 and CSE-CIC-IDS2018-v3 are not directly identical. Therefore the study will use binary attack/benign detection as the primary cross-domain task and treat attack-family analysis conservatively.

A "target-exclusive family" claim will require an explicit semantic mapping decision. Ambiguous families will not be forced into a cross-dataset correspondence.

### Next steps

1. Obtain exact dataset files.
2. Compute SHA-256 hashes.
3. Produce schema reports.
4. Produce exact class/family counts.
5. Audit duplicates and invalid values.
6. Build the first label-mapping artifact.
7. Define the 53-feature registry.
8. Implement the pilot scoring pipeline.
9. Test the target-label firewall.
10. Run the first single-direction pilot.
11. Only after the pilot, create the final `experiment_lock.md`.

## External sources used in this pass

- UQ ML-Based NIDS Datasets:
  https://staff.itee.uq.edu.au/marius/NIDS_datasets/
- TAN-IDS:
  https://doi.org/10.1371/journal.pone.0346801
- NetFlow-v3 dataset paper:
  https://arxiv.org/abs/2503.04404


## 2026-11-05 — Source manifest and label-control pass

### Completed

- Added `dataset_source_manifest.md` with current UQ catalogue and RDM download endpoints for the three selected NetFlow-v3 datasets.
- Added `label_mapping_draft.md` to prevent unsupported cross-dataset family equivalence.
- Added `methodology_change_log.md` to enforce the frozen-core-document policy.
- Confirmed current UQ catalogue values for the 53-feature NetFlow-v3 collection and the three selected datasets.

### Important methodological conclusion

The primary UNSW-NB15-v3 and CSE-CIC-IDS2018-v3 datasets have substantially different attack-family taxonomies. The binary attack/benign task therefore remains the primary cross-domain task; family-level analysis will use conservative mappings and will not force semantic equivalence.

### Current repository state

Core/frozen:

- `research_proposal.md`
- `methodology_final.md`

Working/evolving:

- `literature_review.md`
- `dataset_selection.md`
- `dataset_source_manifest.md`
- `label_mapping_draft.md`
- `experiment_lock_draft.md`
- `methodology_change_log.md`
- `research_worklog.md`

### Next execution step

Acquire the exact dataset files from the locked UQ RDM endpoints, compute SHA-256 hashes, and generate the first machine-derived schema/class/family audit. The final experiment lock remains blocked until that audit and the pilot pass.
