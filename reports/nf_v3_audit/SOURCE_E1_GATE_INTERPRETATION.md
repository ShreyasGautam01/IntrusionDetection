# UNSW Source E1 Stability Interpretation

**Status:** Project owner accepted conditional descriptive use on 2026-11-09. CIC E1 and target gates remain pending.
**Source configuration:** source-e1-lock-1, NF-UNSW-NB15-v3, seeds 0–9.
**Evidence:** SOURCE_E1_FINAL_REPORT.md and source_e1_final_results.json.

## Evidence

The ten-seed source-only five-signal run completed with verified artifacts. A separate same-seed repeat reproduced all seven per-row arrays and metrics exactly. Detector metrics were tightly grouped: accuracy 0.9999598–0.9999683, attack AUPRC 0.99999950–0.99999963, and Brier score 0.0000268–0.0000300.

Each seed had ten source-test attack misses. At the primary 5% review budget, confidence and RF disagreement captured all ten for every seed; distance captured six; conformal and Isolation Forest captured none. Pairwise Spearman minima were 0.605 for confidence, 0.307 for RF disagreement, 1.000 for distance, 0.592 for conformal, and 0.935 for Isolation Forest. Top-5% review-set Jaccard minima were 0.340, 0.699, 1.000, 0.902, and 0.695 respectively.

The attack-miss ranking endpoint is sparse: its ten positive events per seed limit how strongly its AUPRC and rank variation can support a comparative conclusion. No threshold was specified in the frozen config, and no numeric cutoff is introduced here.

## Interpretation and recommendation

The pipeline is computationally reproducible, and detector metrics are stable. Operational capture at 5% is consistent for confidence and disagreement, but the cross-seed ordering of confidence, disagreement, and conformal scores is not uniformly stable. This does not support a single pooled “best signal” conclusion from source E1.

**Recommendation: conditional acceptance for descriptive target-transfer analysis.** If accepted, preserve all seeds and report per-seed values and ranges, with no winner selected from an across-seed average. Treat source rank variation and the ten-miss limitation as material findings. This recommendation does not itself unlock target evaluation.

## Gate state

Target evaluation remains locked until the project owner accepts or rejects this interpretation. The CIC→UNSW direction also requires its own complete CIC source-only E1 gate and an accepted interpretation. No CIC target evaluation or target-label access is authorized by this record.


## Owner decision

On 2026-11-09, the project owner accepted the recommendation for descriptive target-transfer analysis. Preserve all seeds and report per-seed results and ranges without selecting a winner from an across-seed average. This acceptance closes the UNSW interpretation gate only; target evaluation remains sealed until the CIC source-only E1 gate is completed and accepted and the direction manifests are committed.
