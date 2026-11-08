# Source E1 Recovery Audit

**Audit date:** 2026-11-08  
**Branch:** `codex/e0-e05`  
**Configuration:** `source-e1-lock-1`  
**Config SHA-256:** `23fcc21d6699f4e57cf3d96966836b8610773572ad7950330b84149818515a5f`  
**Target data/labels:** not accessed during this audit; evaluation remains locked.

## Seeds 0–5

The ignored stage arrays all match `stage_manifest.json` by size and SHA-256. The stage contains 1,418,952 train rows, 473,301 calibration rows, and 473,171 source-test rows with 46 features. The config hash matches the one recorded by the previous aggregate summary. All six seeds have metrics, predictions, calibrated probabilities, and RF disagreement arrays. Array shapes, finite values, binary predictions, source/config identity fields, and RF parameters match the locked RF subconfiguration. Recomputed detector and reliability metrics match the saved reports; the Brier score check allows `2e-6` for the float32 probability files.

These are valid, recoverable partial runs. They are **not complete runs of the full locked configuration**. The config declares five reliability signals; only calibrated confidence and RF disagreement were produced. Feature-space distance, split conformal, and Isolation Forest outputs are missing. In particular, the source-calibration probability values needed for split conformal were not saved. The existing artifacts therefore cannot be upgraded to complete five-signal runs without seed reruns.

| Seed | RF fit (s) | Accuracy | Attack AUPRC | Attack misses | Partial artifacts verified |
|---:|---:|---:|---:|---:|:---:|
| 0 | 226.2 | 0.999960 | 0.9999995 | 10 | Yes |
| 1 | 6,683.2 | 0.999960 | 0.9999996 | 10 | Yes |
| 2 | 219.3 | 0.999968 | 0.9999996 | 10 | Yes |
| 3 | 257.8 | 0.999962 | 0.9999996 | 10 | Yes |
| 4 | 254.3 | 0.999962 | 0.9999995 | 10 | Yes |
| 5 | 268.4 | 0.999964 | 0.9999996 | 10 | Yes |

Keep seed 1 in all summaries. Its 6,683-second fit-time anomaly is not grounds to exclude it. Every seed has only ten attack misses, so attack-miss ranking estimates remain sparse-event diagnostics.

The machine-readable file `source_e1_recovery_audit.json` records per-file hashes and all verification checks. Rerun the read-only check with `python scripts/verify_source_e1_partial.py`.

## Full-config completion attempt

A separate full-run attempt for seed 0 was started under `data/processed/source-e1-lock-1/full_runs/`, leaving all original partial artifacts untouched. It was stopped after more than 12 minutes while the exact standardized Euclidean five-neighbor source-test distance calculation was still in progress. It produced no completed seed report or usable distance cache. The configured distance score is shared across seeds, so this establishes a runtime bottleneck for completing the full signal set on this machine. No approximate distance method was substituted.

## Gate status

The ten-seed, five-signal E1 stability gate is **incomplete**. Seeds 6–9 have not been run. The full configured outputs for seeds 0–5 are also missing. No stability acceptance rule has been recorded, so this audit does not declare the gate passed. Target evaluation remains locked. No frozen proposal or methodology document was modified.
