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

Bounded distance and RF concurrency benchmarks are committed in `reports/nf_v3_audit/CIC_SOURCE_E1_BENCHMARK_DECISION.md` and accompanying JSON. The monolithic exact KDTree was estimated at 2.8–12.4 hours and 7.45 GB peak against 7.66 GB available at that earlier measurement, so it is not the production plan. After the owner delegated the choice based on research fidelity and hardware limits, the selected plan is mathematically equivalent exact chunked 5-NN with duplicate multiplicities. At 500k-row chunks it estimates 3.62 hours and about 3.10 GB peak including two disk-backed merge-state slots. A two-chunk merge matched raw exact scores within 6.94e-18 maximum absolute error and preserved zero scores. The lossy K=500k reference bank was rejected because it changed the zero-distance mass. The production module and direction-aware runner are committed at `bfbe880`; the frozen CIC manifest is committed at `9d1447c` and bound to `bfbe880`. Full CIC distance/seeds remain unstarted.

The CIC five-signal smoke passed on deterministic class-present source subsets. It produced finite 2,000-row outputs for all five signals and did not access target files or labels. Error and attack-miss ranking metrics on that smoke subset are undefined and not interpreted.

Ignored UNSW source E1 arrays, recovered seed 0–5 RF artifacts, and completed full outputs remain preserved. CIC source arrays are also local and ignored. No target evaluation has occurred.

## Next work

1. Confirm the clean-tree/manifest preflight on the committed branch. The manifest lock commit is `bfbe880c4c05f408774d244d407a108736bf4d8f`.
2. Run the exact CIC distance job. Preserve its chunk checkpoints and outputs under ignored `data/processed/source-e1-cic-lock-1/full_runs/common`.
3. Run the CIC source-only five-signal gate for seeds 0–9 with one RF worker and one internal thread. Refit seed 0 independently and compare all artifacts; verify hashes, shapes, finiteness, and provenance; then record the qualitative CIC gate interpretation for acceptance.
4. Only after both source-gate interpretations are accepted, finalize the shared feature/family registry, benchmark target feature inference and exact target distance on feature-only subsets, and commit manifests for both directions. Read target labels only after the corresponding clean, committed manifest validates.

## Experiment details already frozen

The UNSW source config is source-e1-lock-1: 46 predictive columns; remaining seven raw columns retained as metadata/identifier roles; label-blind hash split; source-training-only finite replacement; 200-tree RF with minimum leaf size 5; seeds 0–9. Five signals are source-calibrated confidence, RF tree disagreement, exact mean Euclidean 5-NN distance, split conformal at alpha 0.10, and Isolation Forest.

The exact UNSW distance used all 1,418,952 source-training references and 473,171 source-test queries, completing in 1,746.4 seconds. It was not approximated. Benchmark and concurrency evidence are committed. Distance is seed-independent; Isolation Forest is fit per seed because its locked random state follows the seed.

The compact 8-feature representation is deferred to a later plan. No target transfer, ToN-IoT, XGBoost, or frozen-methodology changes are part of the current work.


## CIC source-gate benchmark status

The exact distance and RF concurrency envelope is in `CIC_SOURCE_E1_BENCHMARK_DECISION.md`. Bank comparison and exact-preserving duplicate compression/multi-chunk evidence are summarized in `CIC_SOURCE_E1_DISTANCE_BANK_REVIEW.md`; machine-readable reports are `cic_distance_bank_benchmark.json`, `cic_distance_bank_benchmark_validation.json`, `cic_exact_duplicate_compression_benchmark.json`, and `cic_chunked_exact_merge_benchmark_validated.json`. `cic_chunked_exact_merge_benchmark_preliminary_superseded.json` is retained with its incorrect projection clearly marked; use only the validated report. Candidate bank offsets remain local and ignored. The source config and finite-replacement provenance are unchanged. The first bank report's relative-error aggregate overflowed for zero/near-zero exact distances; validation uses absolute errors. The source runner now requires a committed, clean, direction-bound CIC manifest descended from its lock commit before full distance or seed jobs.

## Next-account checkpoint

The CIC exact-distance manifest is committed and descends from its code lock commit. The local checkout was backed up and synchronized to the published branch at `53cc3f6` without cleaning ignored artifacts. Manifest preflight and six staged-array hash/size checks pass. The exact source distance started after 6.90 GB available memory cleared the 4.20 GB frozen startup floor. Three of 25 chunks are complete, with full-source-test query times of 992.2, 575.5, and 770.4 seconds; their mean projects about 5.4 hours total (roughly 4.8 hours remaining), subject to later timings. Peak process working set is 3.24 GB. The checkpoint and double-buffered state are under ignored `data/processed/source-e1-cic-lock-1/full_runs/common`; the shared distance is incomplete and the job remains active/resumable. CIC RF seeds have not started. After exact distance completion, verify its score and metadata hashes before starting seeds 0–9. Do not begin target transfer.



