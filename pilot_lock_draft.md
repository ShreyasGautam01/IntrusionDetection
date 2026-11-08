# First Random Forest pilot lock — working draft

**Status:** Target-transfer lock remains unfrozen; source-only E1 is complete and target labels remain sealed.
**Repository branch:** `codex/e0-e05`.
**Active direction:** NF-UNSW-NB15-v3 → NF-CSE-CIC-IDS2018-v3.
**ToN-IoT-v3:** Excluded.

This draft translates the frozen protocol into a reviewable target-transfer
checklist. It does not authorize target evaluation. The frozen proposal and
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

The frozen E1 gate requires stable results across seeds but defines no numeric
tolerance. The ten-seed results and exact seed-0 repeat are in
`reports/nf_v3_audit/SOURCE_E1_FINAL_REPORT.md`; record the project-level
interpretation before target evaluation.

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
- The source-only matrices and full per-seed arrays are local/ignored at `data/processed/source-e1-lock-1/`. Seeds 0–9 and all five signals completed under `source-e1-lock-1`; bounded resource measurements and the full-run summary are in the source E1 benchmark/final report.

## Required decisions before target transfer

1. Review and approve the explicit 46-column primary-set proposal in
   `reports/nf_v3_audit/primary_feature_set_draft.csv` (backed by
   `primary_feature_set_draft.json`), including identifier treatment and
   `FTP_COMMAND_RET_CODE` (constant in CIC2018, variable in UNSW). The full
   registry retains all 53 fields.
2. Review and freeze the eight-feature sensitivity crosswalk, especially its
   derived values and identifier-like ports, before any fitting.
3. Finalize the conservative family matrix from dataset documentation before
   any family-level target analysis.
4. Review the explicit candidate Random Forest parameters and seeds in
   `rf_config_draft.json`; the isolated package runtime is pinned in `uv.lock`.
5. Review `reports/nf_v3_audit/E1_STABILITY_GATE_DRAFT.md` and the completed
   `SOURCE_E1_FINAL_REPORT.md`; record a project-level stability interpretation
   before target evaluation.
6. Freeze the exact split/control used by the pilot and retain the temporal and
   host/session controls as separate predeclared analyses.
7. Keep target evaluation locked until the source-only stability interpretation
   is accepted.
8. Record exact dataset/config/registry hashes and a committed freeze manifest
   that satisfies `target_label_firewall.md`.

## Stop conditions

- Do not begin target evaluation until the decisions above are frozen.
- Do not expose target labels to fitting, calibration, preprocessing,
  thresholds, feature selection, seed/config selection, or method choice.
- If source-only in-domain runs are unstable across seeds, resolve the
  reproducibility issue before unlocking target evaluation.
- Preserve all negative and failed results; do not tune after inspecting
  target results.
