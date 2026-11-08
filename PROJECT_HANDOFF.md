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
- Seeds 6–9 have not been started. A separate seed-0 full-stack attempt was stopped after over 12 minutes during the exact standardized Euclidean 5-NN source-test distance calculation; it yielded no seed result. The temporary incomplete distance files were removed after inspection. No run process remains active.

## Successor next actions

1. The full five-signal E1 configuration is still incomplete: the existing six RF runs are verified only for detector, confidence, and disagreement. Do not describe them as full-config results.
2. Assess the exact five-neighbor computation runtime and memory using source-only data. Do not silently substitute approximate neighbors or read CIC2018.
3. Preserve seed 1 and its 6,683-second runtime anomaly. Complete any missing seed outputs only under the locked config and retain every result.
4. Record and review the source-only stability interpretation; current drafts define no numeric acceptance threshold. Do not unlock target evaluation until the full source gate and interpretation are complete.

## Known commits before the handoff commit

- `380161a` — source-only config and disk-backed staging.
- `0b8500d` — source-only stability procedure.
- `0322474` — family-count source reconciliation.
- `39a9f59` — memory feasibility estimate.

Commit the handoff, compact results, and runner code. Never commit local