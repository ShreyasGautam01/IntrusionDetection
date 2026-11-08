# E0/E0.5 completion status

**Status:** E0/E0.5 artifacts and the full UNSW source-only E1 computation are complete for seeds 0–9 and five signals. The qualitative gate recommendation is recorded in SOURCE_E1_GATE_INTERPRETATION.md and awaits project-owner acceptance. The CIC source-only E1 gate required for CIC→UNSW is not yet complete. No target evaluation has occurred.
**Active pair:** NF-UNSW-NB15-v3 ↔ NF-CSE-CIC-IDS2018-v3; each direction requires its own source-only E1 gate.
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

1. Obtain project-owner acceptance of the UNSW E1 interpretation.
2. Review the CIC exact-distance benchmark decision and deterministic reference-bank proposal. No alternative or full CIC E1 run starts before approval.
3. After method approval, freeze the CIC source-only E1 config and manifest, complete and verify seeds 0–9, then obtain acceptance of the CIC gate interpretation.
4. Only after both source-gate interpretations are accepted, freeze the 46-feature registry, conservative family mapping, and direction-specific manifests before target scoring.
5. Keep target labels sealed until the matching clean, committed manifest validates.


The E1 evidence and conditional qualitative recommendation are in SOURCE_E1_GATE_INTERPRETATION.md; owner acceptance is pending. Full per-seed metrics remain in SOURCE_E1_FINAL_REPORT.md and source_e1_final_results.json. No post-hoc numeric threshold has been added, and target evaluation remains sealed.

The family-count crosswalk now reconciles the existing local counts against the versioned NetFlow-v3 release paper and current UQ catalogue HTML. The local UNSW counts match the paper exactly; the live HTML page has three conflicting family cells and a prose attack total 54 below its own family-table sum. This source discrepancy is recorded in `FAMILY_MAPPING_DRAFT.md`, `family_mapping_draft.csv`, and `label_mapping_draft.md`; labels remain unchanged.

The temporal control, session split, strict host-disjoint sensitivity, repeated
flow-key check, and constants/domain-shortcut review are in
`e0_source_controls.json` and `E0_SOURCE_CONTROL_REPORT.md`. The host result is
reported as a bounded sensitivity because the retained host support is small;
do not present it as broad host generalization.

The complete UNSW source-only E1 matrices and per-seed arrays remain local and
ignored under `data/processed/source-e1-lock-1`; seeds 0–9 and all five signals
are complete, with compact results in `SOURCE_E1_FINAL_REPORT.md` and
`source_e1_final_results.json`. CIC source arrays for the reverse-direction gate
are separately staged and ignored under `data/processed/source-e1-cic-lock-1`.
CIC labels were used only as CIC source labels; no CIC seed E1 job or target
label evaluation has occurred.

CIC staging hashes, bounded exact-distance measurements, RF concurrency
results, runtime/memory estimates, smoke evidence, and the owner-review decision
are in `CIC_SOURCE_E1_BENCHMARK_DECISION.md`,
`CIC_SOURCE_E1_DISTANCE_BANK_REVIEW.md`, and their JSON evidence. Exact CIC
5-NN was not launched at full scale because the measured resource estimate
leaves inadequate available-memory headroom. No alternative was run or written
into an experiment manifest. The CIC source-only five-signal smoke passed with
finite outputs and no target access.

The deterministic UNSW-training-only median policy is implemented in
`scripts/finite_value_policy.py`; fitted values and source-only counts are in
`unsw_train_finite_replacements.json`. The same `apply_value` function is the
inference transform. The source-only E1 model and reliability settings are
consolidated in `source_e1_config.json`; this config does not unlock CIC2018 or
authorize target evaluation. No raw dataset has been transformed or overwritten.

`src/ids_research/target_lockbox.py` implements feature-only target streaming
and now provides bounded batch output for target scoring. It fails closed on
label access unless a matching freeze manifest is committed, clean, and
descended from the current checkout. No freeze manifest exists yet, so target
labels remain sealed.

The dense-matrix lower bounds and chunking guidance are in
`MEMORY_FEASIBILITY_DRAFT.md` and `memory_estimate_draft.json`. They use the
46-column proposal and exclude model/workspace overhead. Source E1's measured
bounded resource benchmarks and full distance runtime are in
`SOURCE_E1_BENCHMARK.md` and `SOURCE_E1_FINAL_REPORT.md`; full-process peak RSS
was estimated from the bounded benchmarks, not sampled during every full run.

The frozen `research_proposal.md` and `methodology_final.md` were not modified.
