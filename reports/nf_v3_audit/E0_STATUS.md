# E0/E0.5 completion status

**Status:** Requested active-pair E0/E0.5 checks and source split controls are generated; review and pilot-lock gates remain. No model has been trained.
**Active pair:** NF-UNSW-NB15-v3 → NF-CSE-CIC-IDS2018-v3.
**ToN-IoT:** Excluded from the active project scope.

The inherited `REPORT.md`, `audit.json`, `schema.csv`, and
`target_value_counts.csv` document the completed acquisition and schema audit
for the two active datasets. `feature_registry.csv` records the draft role for
all 53 features and both targets. `e0_e05_design.md` records the proposed
label-blind split and source-fitted missing/non-finite handling rules.

A bounded-memory external-sort pass has completed for CIC2018 duplicate-vector
label conflicts, daily temporal coverage and attack episodes, deterministic
label-blind partition counts, and exact feature-vector intersections. Results
are in `e0_results.json`, with interpretation in
`E0_TEMPORAL_CONFLICT_REPORT.md`. The conservative observed family inventory
and pair matrix are `family_inventory.csv` and `family_matrix_draft.csv`; the
raw-label crosswalk and interpretation are `family_mapping_draft.csv` and
`FAMILY_MAPPING_DRAFT.md`. The compact 8-feature sensitivity mapping required
by the frozen methodology is drafted in `representation_8feature_draft.csv`
and `REPRESENTATION_8FEATURE_DRAFT.md`; v3-specific encoding questions remain
limited to port governance and derived packet-rate handling. A targeted
streaming scan of only duration and protocol is recorded in
`representation_input_check.json`; it found 122,493 source zero-duration rows,
no target zero-duration rows, and the protocol-code counts/overlap. It did not
request `Label` or `Attack`. Two
earlier SQLite approaches were stopped because they did not complete in a
practical review window; their scratch databases were discarded and no partial
values from those attempts were used.

Remaining before the first pilot:

1. Review and freeze the candidate feature registry and conservative family
   matrix. Do not use the draft matrix to assert family equivalence or unseen
   attacks.
2. Review and freeze the explicit 46-column primary-set proposal in
   `primary_feature_set_draft.csv` and its summary JSON/Markdown; all other
   fields remain in the full registry.
3. Review the candidate RF parameters and 10-seed list in `rf_config_draft.json`
   and approve a complete experiment configuration. The pinned runtime now
   exists in `uv.lock` and `.venv`; no estimator has been instantiated.
4. Freeze the compact sensitivity mapping. Define the
   source-only E1 stability review criterion; the frozen protocol gives no
   numeric tolerance.
5. Run the source-only in-domain E1 stability gate across the frozen seeds
   before target-label evaluation. This gate has not been run.
6. Commit a freeze manifest binding dataset/config/registry hashes, then use
   the target-label firewall for final evaluation only.

A review-only source E1 stability procedure is drafted in `E1_STABILITY_GATE_DRAFT.md`. It defines per-seed reporting and reproducibility checks but intentionally leaves numerical pass tolerances open for project-owner review; no E1 model has been run.

The family-count crosswalk now reconciles the existing local counts against the versioned NetFlow-v3 release paper and current UQ catalogue HTML. The local UNSW counts match the paper exactly; the live HTML page has three conflicting family cells and a prose attack total 54 below its own family-table sum. This source discrepancy is recorded in `FAMILY_MAPPING_DRAFT.md`, `family_mapping_draft.csv`, and `label_mapping_draft.md`; labels remain unchanged.

The temporal control, session split, strict host-disjoint sensitivity, repeated
flow-key check, and constants/domain-shortcut review are in
`e0_source_controls.json` and `E0_SOURCE_CONTROL_REPORT.md`. The host result is
reported as a bounded sensitivity because the retained host support is small;
do not present it as broad host generalization.

The deterministic UNSW-training-only median policy is implemented in
`scripts/finite_value_policy.py`; fitted values and source-only counts are in
`unsw_train_finite_replacements.json`. The same `apply_value` function is the
inference transform. No dataset has been transformed or overwritten.

`src/ids_research/target_lockbox.py` implements feature-only target streaming
and now provides bounded batch output for target scoring. It fails closed on
label access unless a matching freeze manifest is committed, clean, and
descended from the current checkout. No freeze manifest exists yet, so target
labels remain sealed.

The dense-matrix lower bounds and chunking guidance are in
`MEMORY_FEASIBILITY_DRAFT.md` and `memory_estimate_draft.json`. They use the
current 46-column proposal and do not include model/workspace overhead; no
memory benchmark or fit has been performed.

The frozen `research_proposal.md` and `methodology_final.md` were not modified.
