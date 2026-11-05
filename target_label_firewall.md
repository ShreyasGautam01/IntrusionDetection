# Target-label firewall implementation

**Status:** Implemented as a pre-pilot access boundary; no run is unlocked.  
**Scope:** CIC2018 target data in the active UNSW → CIC2018 direction.

## Access paths

- Prediction code must call `iter_target_features` from
  `src/ids_research/target_lockbox.py` with an explicit feature-column list.
  The function rejects `Label` and `Attack`, rejects duplicate headers and
  malformed rows, and yields only a row number and selected feature values.
- Final evaluation code may call `iter_final_evaluation_labels` only after
  `verify_freeze_manifest` accepts a committed freeze record. The record must
  bind the exact source and target SHA-256 values, experiment-config SHA-256,
  feature-registry SHA-256, source/target dataset names, and a lock commit that
  is an ancestor of the current checkout. The manifest itself must be committed
  and clean in the current checkout.
- A missing or `draft` manifest fails closed. Hash mismatches also fail closed.

The firewall is a code/API boundary, not an operating-system security boundary:
raw files remain available to the local researcher. All model, calibration,
threshold, and method-selection code must use the feature-only path; the label
iterator belongs only in final evaluation code after the freeze gate.

No target labels were accessed to construct the partition or fit the source
finite-value replacements. The requested duplicate-label consistency audit
uses target labels only as a data-integrity report and is not connected to
model-selection code.
