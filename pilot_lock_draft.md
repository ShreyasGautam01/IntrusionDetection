# First Random Forest pilot lock — working draft

**Status:** Not frozen; target labels remain sealed.
**Repository branch:** `codex/e0-e05`.
**Active direction:** NF-UNSW-NB15-v3 → NF-CSE-CIC-IDS2018-v3.
**ToN-IoT-v3:** Excluded.

This draft translates the frozen protocol into a reviewable pilot checklist.
It does not authorize training or target evaluation. The frozen proposal and
`methodology_final.md` remain unchanged.

## Protocol-defined settings

| Item | Frozen-methodology setting |
|---|---|
| Detector | Fixed Random Forest |
| Forest size | 200 trees |
| Minimum leaf size | 5 |
| Probability calibration | Source-only sigmoid/Platt calibration |
| RF disagreement | `1 - max(tree vote fraction)` |
| Distance | Source-training reference; standardized feature space; kNN, starting `k=5` |
| Conformal | Split conformal using source calibration; headline `alpha=0.10` |
| Isolation Forest | Fit on source reference data only; orient higher as more unreliable |
| Reliability orientation | Higher score means more deserving of review |
| Primary endpoint | Target attack-miss AUPRC |
| Co-primary endpoint | Attack-miss capture at 5% review |
| Review budgets | 1%, 5%, and 10% |
| Transfer directions in initial lock | UNSW→CIC2018 and CIC2018→UNSW |

## Random Forest implementation proposal

The concrete review proposal is in `rf_config_draft.json`, with rationale in
`RF_CONFIG_DRAFT.md`. It records the method-fixed settings (200 trees and leaf
size 5), proposes the documented classifier defaults for remaining tree
parameters, proposes seeds 0–9, and sets single-job execution. These values
are **not frozen**. A pinned `uv.lock` resolves scikit-learn 1.9.1. Six limited source-only
RF runs used the separate `source-e1-lock-1` config; this is not the full
reliability stack or target-transfer study.

The frozen E1 gate also requires stable results across seeds without defining
a numeric stability tolerance. Define and record that review criterion before
any E1 run.

## Current E0/E0.5 settings and cautions

- The deterministic 60/20/20 label-blind UNSW hash partition is the baseline
  source split proposal. A separate chronological control is recorded in
  `reports/nf_v3_audit/e0_source_controls.json`.
- The temporal control uses 60%/80% start-time order statistics and a 60-second
  complete-flow embargo. Keep it separate from the baseline random-like hash
  split in reporting.
- The strict host-disjoint split is a limited sensitivity: it excludes about
  half the UNSW flows and retains only 6 calibration and 7 source-test hosts.
- The current feature registry and family matrix remain drafts. No cross-domain
  family equivalence or unseen-family conclusion is frozen.
- The frozen methodology also requires a compact 8-feature representation
  sensitivity. Its draft crosswalk to v3 columns is in
  `reports/nf_v3_audit/representation_8feature_draft.csv`, with discussion in
  `reports/nf_v3_audit/REPRESENTATION_8FEATURE_DRAFT.md`. It is not implemented
  or frozen. Protocol and TCP-flag alignment are supported by the supplied
  feature dictionary. Port inclusion remains a feature-governance decision.
  The packet-rate formula yields undefined values for 122,493 source flows
  whose duration is zero; the draft policy maps these to missing and uses a
  source-training-only median, with the exact derived-feature fit still to be
  implemented and recorded before E1.
- Finite-value replacements are fitted from UNSW baseline training rows only
  and applied unchanged at inference.
- The source-only matrices are staged locally at `data/processed/source-e1-lock-1/`. Seeds 0–5 completed; current RSS stayed modest, but per-run peak memory was not recorded. The remaining seed runs and reliability signals are documented in `reports/nf_v3_audit/PROJECT_HANDOFF.md`.

## Required decisions before freezing

1. Review and approve the explicit 46-column primary-set proposal in
   `reports/nf_v3_audit/primary_feature_set_draft.csv` (backed by
  