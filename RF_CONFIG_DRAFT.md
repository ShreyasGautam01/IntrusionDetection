# Random Forest Configuration Draft

**Status:** Review proposal only. Not frozen; no estimator was instantiated or fit.

## Fixed by the frozen methodology

- Random Forest classifier.
- 200 trees.
- Minimum leaf size 5.
- Fixed seeds, with at least ten recommended where practical.
- No target-based tuning; source-only calibration and the source-only E1 gate precede target-label evaluation.

## Concrete proposal for remaining estimator settings

`rf_config_draft.json` records every candidate parameter explicitly. It uses the documented scikit-learn classifier defaults for the otherwise unspecified tree settings, with `n_jobs=1` as a proposed reproducibility setting. Ten seeds, 0 through 9, are proposed. These are review choices, not locked values.

This proposal includes `class_weight=None` (no class reweighting), bootstrap sampling enabled, `max_features="sqrt"`, and unconstrained tree depth, alongside the remaining library defaults. A different choice requires an explicit source-only justification and a pre-E1 config update.

## Runtime is not ready

The current environment reports Python 3.14.7 and does not have scikit-learn installed. No dependency lock file exists in the repository. The scikit-learn version, compatible runtime, and any additional package versions must be pinned before E1; no model run has been made.

The current draft records the implementation candidate and the unresolved version field. It must not be used to unlock the target-label firewall.

## Remaining pre-E1 decisions

1. Approve the exact primary predictive columns and the compact sensitivity mapping, including numeric port treatment.
2. Review and freeze the family ontology and mapping policy before family-level reporting.
3. Approve or revise this candidate parameter set and seed list, then pin the runtime.
4. Define the source-only stability gate's review criterion before running E1; the frozen text requires stability across seeds but does not set a numeric tolerance.
5. Freeze the source split, calibration procedure details, and all reliability-signal parameters.
6. Run source-only E1; only after the gate passes may the freeze manifest be committed for final target evaluation.

The defaults are cross-checked against the [official scikit-learn RandomForestClassifier API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html). Defaults can change across library releases, so the API version and package version must be fixed in the final lock.
