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
2. Complete the pilot lock draft: remaining RF parameters, seed list, exact
   predictive feature set, and any sensitivity settings must be explicit.
3. Run the source-only in-domain E1 stability gate across the frozen seeds
   before target-label evaluation. This gate has not been run.
4. Commit a freeze manifest binding dataset/config/registry hashes, then use
   the target-label firewall for final evaluation only.

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
and fails closed on label access unless a matching freeze manifest is
committed, clean, and descended from the current checkout. The interface is
implemented; no freeze manifest exists yet, so target labels remain sealed.

The frozen `research_proposal.md` and `methodology_final.md` were not modified.
