# Intrusion Detection Research — Project Handoff

**Handoff time:** 2026-11-09
**Authoritative project folder:** D:\IntrusionDetection
**Branch:** codex/e0-e05
**Prior published baseline:** 4eaea7d; this handoff is published at the current `codex/e0-e05` branch HEAD.
**Active project pair:** NF-UNSW-NB15-v3 ↔ NF-CSE-CIC-IDS2018-v3

## Guardrails

- research_proposal.md and methodology_final.md are frozen and must not be modified.
- NF-ToN-IoT-v3 and XGBoost are excluded from this continuation.
- Raw datasets under D:\NF-v3-datasets are read-only and must never be committed.
- Target scoring and target-label evaluation remain locked pending source-gate acceptance and committed direction manifests.
- Preserve ignored source E1 arrays and outputs under `data/processed/source-e1-lock-1` and `data/processed/source-e1-cic-lock-1`; never clean or overwrite them.

## Current state

The workspace is synchronized to `codex/e0-e05` at the published UNSW-gate interpretation milestone. UNSW source-only E1 is complete for seeds 0–9, with exact feature distance shared across seeds and a same-seed repeat. The qualitative interpretation recommends conditional acceptance for descriptive transfer; the project owner accepted this on 2026-11-09. Target evaluation remains locked pending the CIC source gate and committed direction manifests.

CIC source staging for the reverse CIC → UNSW E1 gate is complete under the separate `source-e1-cic-lock-1` configuration. The label-blind 60/20/20 split produced 12,068,590 train, 4,021,791 calibration, and 4,025,148 source-test rows in the locked 46-feature order. All six staged arrays match their local ignored stage manifest and have finite features. CIC labels were used as source labels only. UNSW target files and labels were not read.

Bounded exact CIC distance and RF concurrency benchmarks are committed in `reports/nf_v3_audit/CIC_SOURCE_E1_BENCHMARK_DECISION.md` and the accompanying JSON evidence. Exact distance is estimated at 2.8–12.4 hours, with a projected 7.45 GB peak process working set against 7.66 GB available at that earlier measurement; it was judged unsafe on that measured resource state. The owner approved a bounded bank comparison, now complete on staged source features. Hash-priority selection repeated identically. Against a 2.4M-reference exact subset, K=500k reached Spearman 0.9213 and p95 absolute error 0.1209, but reproduced 1,565 zero-distance rows compared with 1,830 exact zeros among 4,096 queries; its median score was 0.001215 versus 0.000271 exact. The approximation is not selected. Full CIC seed jobs and the final CIC E1 manifest remain unstarted pending owner review.

The CIC five-signal smoke passed on deterministic class-present source subsets. It produced finite 2,000-row outputs for all five signals and did not access target files or labels. Error and attack-miss ranking metrics on that smoke subset are undefined and not interpreted.

Ignored UNSW source E1 arrays, recovered seed 0–5 RF artifacts, and completed full outputs remain preserved. CIC source arrays are also local and ignored. No target evaluation has occurred.

## Next work

1. Review `reports/nf_v3_audit/CIC_SOURCE_E1_DISTANCE_BANK_REVIEW.md`. Accept K=500k as the explicit CIC-only deterministic approximation or direct another justified method. Do not launch CIC seeds before this decision; the source config still specifies exact distance.
2. Once approved, update and commit the CIC E1 manifest to bind the accepted distance definition, then run the complete source-only five-signal gate for seeds 0–9 and same-seed repeat. Do not use target data or labels.
3. Record a qualitative CIC gate interpretation and obtain its acceptance. Only after both source-gate interpretations are accepted, finalize the shared feature/family registry, benchmark target feature inference and exact target distance on feature-only subsets, and commit manifests for both directions.
4. Score target features through the streaming feature-only iterator. Read target labels only after the corresponding clean, committed manifest validates. Preserve per-row outputs locally and commit compact provenance/results only.

## Experiment details already frozen

The UNSW source config is source-e1-lock-1: 46 predictive columns; remaining seven raw columns retained as metadata/identifier roles; label-blind hash split; source-training-only finite replacement; 200-tree RF with minimum leaf size 5; seeds 0–9. Five signals are source-calibrated confidence, RF tree disagreement, exact mean Euclidean 5-NN distance, split conformal at alpha 0.10, and Isolation Forest.

The exact UNSW distance used all 1,418,952 source-training references and 473,171 source-test queries, completing in 1,746.4 seconds. It was not approximated. Benchmark and concurrency evidence are committed. Distance is seed-independent; Isolation Forest is fit per seed because its locked random state follows the seed.

The compact 8-feature representation is deferred to a later plan. No target transfer, ToN-IoT, XGBoost, or frozen-methodology changes are part of the current work.


## CIC source-gate benchmark status

The exact distance and RF concurrency envelope, versions, CPU use, and memory measurements are in `reports/nf_v3_audit/CIC_SOURCE_E1_BENCHMARK_DECISION.md`. Bank timing, validation, sample hashes, scaler hash, and finite score summaries are in `cic_distance_bank_benchmark.json` and `cic_distance_bank_benchmark_validation.json`; candidate banks remain local and ignored under `data/processed/source-e1-cic-lock-1/distance-bank-benchmark-v1`. The stage config and finite-replacement provenance are `source_e1_cic_config.json` and `cic_train_finite_replacements.json`. The first relative-error aggregation overflowed for zero/near-zero exact distances; revalidation replaced it with finite-checked absolute error and rank statistics. No final method change is active until the owner reviews `CIC_SOURCE_E1_DISTANCE_BANK_REVIEW.md`.

## Next-account checkpoint

This continuation completes only the approved bounded feature-only benchmark and commits its evidence. It does not complete CIC E1 or authorize target transfer. The user reported 23% usage remaining at the start and asked the agent to stop near 5%; the available goal-status tool reports cumulative token use but exposes no total or remaining percentage. Do not infer a precise percentage. Work stops at the owner method-acceptance gate so the next account can continue from this clean, published branch.
