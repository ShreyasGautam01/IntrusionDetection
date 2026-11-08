# Intrusion Detection Research — Project Handoff

**Handoff time:** 2026-11-08
**Authoritative project folder:** D:\IntrusionDetection
**Branch:** codex/e0-e05
**Published head:** 28e01c8
**Active project pair:** NF-UNSW-NB15-v3 ↔ NF-CSE-CIC-IDS2018-v3

## Guardrails

- research_proposal.md and methodology_final.md are frozen and must not be modified.
- NF-ToN-IoT-v3 and XGBoost are excluded from this continuation.
- Raw datasets under D:\NF-v3-datasets are read-only and must never be committed.
- Target scoring and target-label evaluation remain locked pending source-gate acceptance and committed direction manifests.
- Preserve ignored source E1 arrays and outputs under data/processed/source-e1-lock-1; never clean or overwrite them.

## Current state

E0/E0.5 dataset, feature, split, family, and leakage-control artifacts are committed. Source-only UNSW E1 is complete for seeds 0–9 and all five reliability signals. The exact feature-distance result is shared across seeds. Seeds 0–5 recovered outputs were verified and reused; full outputs for seeds 0–9 remain local and ignored. The seed-0 repeat matched all seven arrays and metrics.

The result and resource records are in reports/nf_v3_audit/SOURCE_E1_FINAL_REPORT.md, source_e1_final_results.json, and SOURCE_E1_BENCHMARK.md. The UNSW gate interpretation and conditional recommendation are in SOURCE_E1_GATE_INTERPRETATION.md; project-owner acceptance is pending. No target evaluation has occurred.

The local checkout has been synchronized to the published branch. Backup ref backup/codex-e0-e05-pre-sync-2611acd preserves the prior local commit chain. Ignored E1 outputs were retained.

## Next work

1. Obtain project-owner acceptance or rejection of the UNSW E1 interpretation. Do not access target labels or begin transfer before acceptance.
2. Prepare a CIC source-only config and disk-backed split using the same 46-feature order, label-blind SHA-256 60/20/20 split, source-only finite replacements, calibration/conformal split, RF settings, five-signal definitions, and seeds 0–9.
3. Benchmark exact CIC source-train 5-NN distance on bounded subsets of the actual staged arrays, and benchmark one versus two RF workers with internal threads limited to one. Record wall time, CPU, peak memory, throughput, and full-run estimates before a full CIC E1 run.
4. If the measured exact/computation plan is impractical, stop and prepare a deterministic, mathematically specified alternative for owner review. Do not change a manifest or launch an alternative before approval.
5. Complete and integrity-check the CIC source-only E1 run, including a same-seed repeat, then obtain owner acceptance of its qualitative interpretation.
6. Only after both source gates are accepted, finalize the 46-feature registry and conservative family mapping, benchmark target-feature scoring without labels, and commit one clean frozen manifest per direction before scoring.
7. Use the feature-only target iterator for scoring; invoke the final label iterator only after the corresponding committed manifest validates. Preserve per-row outputs locally and commit compact provenance/results only.

## Experiment details already frozen

The UNSW source config is source-e1-lock-1: 46 predictive columns; remaining seven raw columns retained as metadata/identifier roles; label-blind hash split; source-training-only finite replacement; 200-tree RF with minimum leaf size 5; seeds 0–9. Five signals are source-calibrated confidence, RF tree disagreement, exact mean Euclidean 5-NN distance, split conformal at alpha 0.10, and Isolation Forest.

The exact UNSW distance used all 1,418,952 source-training references and 473,171 source-test queries, completing in 1,746.4 seconds. It was not approximated. Benchmark and concurrency evidence are committed. Distance is seed-independent; Isolation Forest is fit per seed because its locked random state follows the seed.

The compact 8-feature representation is deferred to a later plan. No target transfer, ToN-IoT, XGBoost, or frozen-methodology changes are part of the current work.
