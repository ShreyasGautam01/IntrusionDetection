# Intrusion Detection Research — Project Handoff

**Handoff time:** 2026-11-09
**Authoritative project folder:** D:\IntrusionDetection
**Branch:** codex/e0-e05
**Published baseline at continuation:** 38cbf95 (see branch history for the current published head)
**Active project pair:** NF-UNSW-NB15-v3 ↔ NF-CSE-CIC-IDS2018-v3

## Guardrails

- research_proposal.md and methodology_final.md are frozen and must not be modified.
- NF-ToN-IoT-v3 and XGBoost are excluded from this continuation.
- Raw datasets under D:\NF-v3-datasets are read-only and must never be committed.
- Target scoring and target-label evaluation remain locked pending source-gate acceptance and committed direction manifests.
- Preserve ignored source E1 arrays and outputs under data/processed/source-e1-lock-1; never clean or overwrite them.

## Current state

The workspace is synchronized to `codex/e0-e05` at the published UNSW-gate interpretation milestone. UNSW source-only E1 is complete for seeds 0–9, with exact feature distance shared across seeds and a same-seed repeat. The qualitative interpretation recommends conditional acceptance for descriptive transfer; project-owner acceptance is pending, so target evaluation remains locked.

CIC source staging for the reverse CIC → UNSW E1 gate is complete under the separate `source-e1-cic-lock-1` configuration. The label-blind 60/20/20 split produced 12,068,590 train, 4,021,791 calibration, and 4,025,148 source-test rows in the locked 46-feature order. All six staged arrays match their local ignored stage manifest and have finite features. CIC labels were used as source labels only. UNSW target files and labels were not read.

Bounded exact CIC distance and RF concurrency benchmarks are committed in `reports/nf_v3_audit/CIC_SOURCE_E1_BENCHMARK_DECISION.md` and the accompanying JSON evidence. Exact distance is estimated at 2.8–12.4 hours, with a projected 7.45 GB peak process working set against 7.66 GB available before benchmarking; it was judged unsafe on the current memory state. A deterministic hash-priority reference-bank proposal is in `CIC_SOURCE_E1_DISTANCE_BANK_REVIEW.md`. The proposal has not been benchmarked or run. No CIC E1 seed jobs or final CIC experiment manifest have been started.

The CIC five-signal smoke passed on deterministic class-present source subsets. It produced finite 2,000-row outputs for all five signals and did not access target files or labels. Error and attack-miss ranking metrics on that smoke subset are undefined and not interpreted.

Ignored UNSW source E1 arrays, recovered seed 0–5 RF artifacts, and completed full outputs remain preserved. CIC source arrays are also local and ignored. No target evaluation has occurred.

## Next work

1. Review and accept or reject the UNSW E1 interpretation in `reports/nf_v3_audit/SOURCE_E1_GATE_INTERPRETATION.md`.
2. Review the exact-distance resource decision and deterministic reference-bank proposal. If an alternative is approved, benchmark its deterministic bank sizes and feature-only approximation error before changing the CIC experiment manifest. If rejected, reassess exact execution only after adequate memory headroom is available.
3. Freeze and commit the approved CIC source-E1 configuration/manifest before running its full five-signal gate. Verify seeds 0–9 and a same-seed repeat; then record a qualitative CIC gate interpretation for owner acceptance.
4. Only after both source-gate interpretations are accepted, finalize the shared feature/family registry, benchmark target feature inference and exact target distance on feature-only subsets, and commit manifests for both directions.
5. Score target features through the streaming feature-only iterator. Read target labels only after the corresponding clean, committed manifest validates. Preserve per-row outputs locally and commit compact provenance/results only.

## Experiment details already frozen

The UNSW source config is source-e1-lock-1: 46 predictive columns; remaining seven raw columns retained as metadata/identifier roles; label-blind hash split; source-training-only finite replacement; 200-tree RF with minimum leaf size 5; seeds 0–9. Five signals are source-calibrated confidence, RF tree disagreement, exact mean Euclidean 5-NN distance, split conformal at alpha 0.10, and Isolation Forest.

The exact UNSW distance used all 1,418,952 source-training references and 473,171 source-test queries, completing in 1,746.4 seconds. It was not approximated. Benchmark and concurrency evidence are committed. Distance is seed-independent; Isolation Forest is fit per seed because its locked random state follows the seed.

The compact 8-feature representation is deferred to a later plan. No target transfer, ToN-IoT, XGBoost, or frozen-methodology changes are part of the current work.


## CIC source-gate benchmark status

The actual benchmark datasets, software versions, resource measurements, exact runtime envelope, and provisional two-worker RF choice are recorded in `reports/nf_v3_audit/CIC_SOURCE_E1_BENCHMARK_DECISION.md`. The stage config and finite-replacement provenance are `reports/nf_v3_audit/source_e1_cic_config.json` and `cic_train_finite_replacements.json`. No method change is active until the project owner reviews the candidate in `CIC_SOURCE_E1_DISTANCE_BANK_REVIEW.md`.
