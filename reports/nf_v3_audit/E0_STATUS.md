# E0/E0.5 completion status

**Status:** Requested E0/E0.5 deliverables are generated for the active pair; frozen-protocol leakage and split-control checks remain open. No model has been trained.
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
and pair matrix are `family_inventory.csv` and `family_matrix_draft.csv`. Two
earlier SQLite approaches were stopped because they did not complete in a
practical review window; their scratch databases were discarded and no partial
values from those attempts were used.

Remaining before the full frozen E0/E0.5 gate and first pilot:

1. Complete the frozen protocol's duplicate-flow-key and practical near-
   duplicate checks; review constants and domain/capture leakage fields.
2. Build the separate temporal sensitivity split with source-derived timestamp
   boundaries, complete-flow checks, and the predeclared 60-second embargo;
   report excluded rows and exact-vector intersections.
3. Build the session-disjoint and host-disjoint source sensitivity memberships
   from observed endpoint fields; check group leakage and retained support. If
   host-disjoint grouping is impractical, report the measured reason.
4. Review and freeze the candidate feature registry and conservative family
   matrix. Do not use the draft matrix to assert family equivalence or unseen
   attacks.
5. Freeze the pilot configuration and ensure evaluation labels are isolated
   from fitting, preprocessing, calibration, and thresholds under the target-
   label firewall.

The deterministic UNSW-training-only median policy is implemented in
`scripts/finite_value_policy.py`; fitted values and source-only counts are in
`unsw_train_finite_replacements.json`. The same `apply_value` function is the
inference transform. No dataset has been transformed or overwritten.

The frozen `research_proposal.md` and `methodology_final.md` were not modified.
