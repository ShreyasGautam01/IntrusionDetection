# Frozen Transfer Representation and Family Crosswalk

**Status:** Frozen for the two core NF-v3 transfer directions.

**Feature source:** Both source E1 configurations, each with 46 predictors in the same ordered list.

**Registry:** `transfer_feature_registry.csv`.

## Feature roles

The transfer predictor list is exactly the ordered 46-column E1 list. Each dataset has 55 audited columns: 46 predictors, seven non-predictor metadata/identifier columns (two split/chronology fields and five identifier-like fields), and the `Label` and `Attack` evaluation targets. The two targets are available only to final evaluation after the direction manifests validate. Target preprocessing uses only replacements fitted on the source training partition; distance scaling also fits on source training only.

## Family crosswalk

Only the audited `DoS` ↔ `DoS` pair is assigned cross-domain ID `shared:DoS` (Same documented canonical category.). This denotes a documented shared category; it does not claim identical attack scenarios. The `DoS`/`DDoS` relationship and all other ambiguous or undocumented pairs remain dataset-local. Raw labels and local family groupings are preserved. **No target-exclusive or “unseen family” claim is made solely from absent or different label strings.**

Machine-readable records are in `transfer_family_registry.csv` and `transfer_family_pair_matrix.csv`; their bases and sources are retained from the audited draft artifacts. The frozen feature order is reproducible with `scripts/finalize_transfer_registry.py --check`.
