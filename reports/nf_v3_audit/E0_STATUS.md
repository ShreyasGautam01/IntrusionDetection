# E0/E0.5 completion status

**Status:** E0/E0.5 artifacts and the full source-only E1 computation are complete for seeds 0–9 and five signals. Target evaluation remains locked pending project-level interpretation of source-seed stability; no target evaluation has occurred.
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

Remaining before target evaluation:

1. Review/freeze the 46-feature registry and family matrix for target analysis;
   do not infer family equivalence or unseen attacks from draft mappings.
2. Freeze the compact 8-feature sensitivity mapping before that sensitivity is
   run.
3. Record the project-level interpretation of the completed source E1 stability
   results. The locked source config defines no numeric tolerance; do not invent
   one after seeing these results.
4. Commit the final target-transfer manifest binding the approved features,
   family policy, source E1 config, and firewall conditions.
5. Only after the source E1 gate is accepted and the final manifest is in place,
   use the target-label firewall for target evaluation.

The source E1 stability procedure and current decision are in `E1_STABILITY_GATE_DRAFT.md`. Full per-seed metrics and stability summaries are in `SOURCE_E1_FINAL_REPORT.md` and `source_e1_final_results.json`. Target evaluation remains sealed because no numeric tolerance was frozen and the rank-stability interpretation remains open.

The family-count crosswalk now reconciles the existing local counts against the versioned NetFlow-v3 release paper and current UQ catalogue HTML. The local UNSW counts match the paper exactly; the live HTML page has three conflicting family cells and a prose attack total 54 below its own family-table sum. This source discrepancy is recorded in `FAMILY_MAPPING_DRAFT.md`, `family_mapping_draft.csv`, and `label_mapping_draft.md`; labels remain unchanged.

The temporal control, session split, strict host-disjoint sensitivity, repeated
flow-key check, and constants/domain-shortcut review are in
`e0_source_controls.json` and `E0_SOURCE_CONTROL_REPORT.md`. The host result is
reported as a bounded sensitivity because the retained host support is small;
do not present it as broad host generalization.

The source-only E1 feature matrices and full per-seed arrays remain local and
ignored under `data/pro