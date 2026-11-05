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
- Finite-value replacements are fitted from UNSW baseline training rows only
  and applied unchanged at inference.

## Required decisions before freezing

1. Approve the exact predictive feature columns from `feature_registry.csv`,
   including treatment of identifiers, absolute time, and
   `FTP_COMMAND_RET_CODE` (constant in CIC2018, variable in UNSW).
2. Finalize the conservative family matrix from dataset documentation before
   any family-level target analysis.
3. Specify every remaining Random Forest parameter and software version; the
   frozen method fixes tree count and minimum leaf size but not all settings.
4. Fix the seed list. The proposal recommends at least 10 where practical;
   practical feasibility and the exact list are not yet locked.
5. Freeze the exact split/control used by the pilot and retain the temporal and
   host/session controls as separate predeclared analyses.
6. Complete the source-only in-domain E1 stability gate across the locked seeds
   before any target-label evaluation is unlocked.
7. Record exact dataset/config/registry hashes and a committed freeze manifest
   that satisfies `target_label_firewall.md`.

## Stop conditions

- Do not run the Random Forest pilot until the decisions above are frozen.
- Do not expose target labels to fitting, calibration, preprocessing,
  thresholds, feature selection, seed/config selection, or method choice.
- If source-only in-domain runs are unstable across seeds, resolve the
  reproducibility issue before unlocking target evaluation.
- Preserve all negative and failed results; do not tune after inspecting
  target results.
