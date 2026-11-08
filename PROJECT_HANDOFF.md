# Intrusion Detection Research — Project Handoff

**Handoff time:** 2026-11-06 14:41 UTC
**Authoritative project folder:** `D:\IntrusionDetection`
**Do not use:** `D:\ids_implementation_rebuilt` (deprecated copy).
**Branch:** `codex/e0-e05`
**GitHub:** https://github.com/ShreyasGautam01/IntrusionDetection

## Guardrails

- `research_proposal.md` and `methodology_final.md` are frozen; neither was changed.
- Active pair: NF-UNSW-NB15-v3 → NF-CSE-CIC-IDS2018-v3. NF-ToN-IoT is excluded.
- Raw data under `D:\NF-v3-datasets` are read-only and must never be committed.
- No CIC2018 features or labels were accessed by the source-only E1 work. Keep target labels sealed until source E1 stability is complete and the committed freeze manifest is in place.

## Current state

E0/E0.5 audit, temporal/duplicate/split controls, feature registry, label mapping, source-only replacement policy, and target-label firewall are in `reports/nf_v3_audit/` and the repository root. Family-count discrepancy is documented; raw labels remain unchanged.

Source-only E1 is bound to `reports/nf_v3_audit/source_e1_config.json` (`source-e1-lock-1`): 46 shared candidate features; label-blind SHA-256 60/20/20 UNSW split; source-train finite replacements; 200-tree RF; minimum leaf 5; seeds 0–9.

### Data staged locally

Disk-backed arrays are at ignored path `data/processed/source-e1-lock-1/`; do not commit them. Rows: train 1,418,952, calibration 473,301, source test 473,171. Each matrix has 46 float32 columns; source labels are separate int8 arrays. Current UNSW source SHA-256 rechecked as `4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5`. Raw CSV was not modified.

### E1 partial results

- Seeds 0–5 completed. Compact metrics: `reports/nf_v3_audit/SOURCE_E1_PARTIAL_REPORT.md` and `source_e1_seed_results.json`. Full per-row outputs remain local and ignored.
- Implemented outputs cover RF detector metrics, source-sigmoid-calibrated confidence, and RF tree disagreement. kNN distance, split conformal reliability, and Isolation Forest are still not implemented.
- On 2026-11-08, all stage-array hashes and seed 0–5 partial outputs were verified by `scripts/verify_source_e1_partial.py`; see `SOURCE_E1_RECOVERY_AUDIT.md` and `source_e1_recovery_audit.json`.
- Every seed had 10 source-test attack misses. The 1% review capture was 100% for confidence and disagreement, but there are only ten events, so do not overinterpret it.
- Seed 1 fit time is 6,683 seconds; other completed seeds took 219–268 seconds. Retain seed 1 and investigate the runtime anomaly; do not remove it based on model performance.
- The earlier seed-0 full-stack attempt was stopped during exact distance search, but the subsequent bounded benchmark justified a long exact run. Full distance and five-signal outputs for seeds 0–9 are now complete; see `SOURCE_E1_FINAL_REPORT.md` and `source_e1_final_results.json`.

### 2026-11-08 bounded benchmark and run lock

- Bounded exact KD-tree distance benchmarks used deterministic subsets up to 800,000 of the 1,418,952 source-train references. Throughput at 800,000 was about 437 queries/s for 512 source-test queries; query-size scaling was near-linear. Full exact distance is estimated at 38–55 minutes and 1.0–1.5 GiB peak working set. The decision is to run the exact method once as a long single job; no approximation is authorized.
- A 25% RF benchmark measured 42.4 seconds for one worker and 49.8 seconds for two concurrent workers (two jobs), with peak process working set 518MB and 537MB respectively. Two-worker throughput was 1.70×. Full RF runs use two concurrent seed workers with OpenMP/BLAS and estimator jobs capped at one.
- The five-signal factorization is explicit in `reports/nf_v3_audit/source_e1_manifest.json`: distance is seed-independent and computed once. Isolation Forest is independent of RF outputs but uses the matching run seed for `random_state`, so it is fit once per configured seed. Confidence, disagreement, and conformal are RF-seed-dependent.
- The full-pipeline subset smoke passed for all five score shapes and finite outputs. Its 2,000-row test prefix had no attack misses, so its ranking metrics are not interpreted.
- The run manifest was frozen after benchmarks and smoke, before full E1 computation. Do not alter the signal definitions or thread plan without a documented, pre-run manifest revision.
- The exact distance stage finished in 1,746.4s (29m06s), 271 source-test queries/s end-to-end. Each of seeds 0–9 completed with ten source-test attack misses. Seeds 0–5 exactly reused recovered probability, prediction, and disagreement arrays after a matching refit; seed 0's separate complete repeat matched all arrays and metrics exactly.
- The source-only computational run is complete, but target evaluation remains locked. The frozen config has no numeric stability tolerance; the report records rank-correlation minima and capture ranges for project-level interpretation.

## Successor next actions

1. Review `SOURCE_E1_FINAL_REPORT.md` and record a project-level interpretation of the completed source-seed stability results. The original config deliberately defines no numeric tolerance.
2. Do not begin target transfer until that stability interpretation is recorded and the E1 gate is deemed acceptable.
3. Preserve seed 1's historical 6,683-second fit and seed 7's 1,484-second fit as runtime anomalies; do not exclude either result.

## Known commits before the handoff commit

- `380161a` — source-only config and disk-backed staging.
- `0b8500d` — source-only stability procedure.
- `0322474` — family-count source reconciliation.
- `39a9f59` — memory feasibility estimate.

Commit the handoff, compact results, and runner code. Never commit local matrices, per-row predictions, logs, model objects, or raw data.
