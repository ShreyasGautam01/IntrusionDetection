# E0/E0.5 completion status

**Status:** Incomplete; no model has been trained.  
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

Remaining before E0 can close:

1. Review the proposed hash-based 60/20/20 UNSW split against temporal and
   host/session controls in the frozen methodology; the configured split is a
   reproducible baseline, not the required temporal/host sensitivity controls.
2. Implement and persist UNSW-training-fitted median replacement values, then
   demonstrate identical application to calibration, source test, and target.
3. Review and freeze the candidate feature registry and conservative family
   matrix. Do not use the draft matrix to assert family equivalence or unseen
   attacks.

The frozen `research_proposal.md` and `methodology_final.md` were not modified.
