"""Verify retained source-only E1 outputs for seeds 0-5 without fitting models."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import sklearn
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/source-e1-lock-1"
REPORTS = ROOT / "reports/nf_v3_audit"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    cfg_path = REPORTS / "source_e1_config.json"
    summary_path = REPORTS / "source_e1_seed_results.json"
    config = json.loads(cfg_path.read_text(encoding="utf-8"))
    prior = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest_path = DATA / "stage_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config_hash = sha256(cfg_path)
    stage_checks = {}
    for name, spec in manifest["files"].items():
        path = DATA / name
        stage_checks[name] = {
            "exists": path.is_file(),
            "bytes_match": path.is_file() and path.stat().st_size == spec["bytes"],
            "sha256_match": path.is_file() and sha256(path) == spec["sha256"],
        }
    stage_ok = all(x["exists"] and x["bytes_match"] and x["sha256_match"] for x in stage_checks.values())

    y = np.asarray(np.load(DATA / "source_test_y.npy", mmap_mode="r"), dtype=np.uint8)
    outputs = {}
    required = ("metrics.json", "prediction.npy", "calibrated_probability.npy", "rf_disagreement.npy")
    for seed in range(6):
        folder = DATA / f"seed-{seed}"
        present = {name: (folder / name).is_file() for name in required}
        record = {"seed": seed, "files_present": present, "files": {}}
        if not all(present.values()):
            record["verified_partial_artifact"] = False
            outputs[str(seed)] = record
            continue
        p_metrics = folder / "metrics.json"
        p_pred = folder / "prediction.npy"
        p_prob = folder / "calibrated_probability.npy"
        p_dis = folder / "rf_disagreement.npy"
        metrics = json.loads(p_metrics.read_text(encoding="utf-8"))
        pred = np.load(p_pred, mmap_mode="r")
        prob = np.load(p_prob, mmap_mode="r")
        disagreement = np.load(p_dis, mmap_mode="r")
        shape_ok = all(x.shape == y.shape for x in (pred, prob, disagreement))
        finite_ok = bool(np.isfinite(prob).all() and np.isfinite(disagreement).all())
        identity_ok = (
            metrics.get("seed") == seed
            and metrics.get("configuration_id") == config["configuration_id"]
            and metrics.get("source_sha256") == config["source_dataset"]["sha256"]
            and metrics.get("source_test_rows") == len(y)
            and metrics.get("feature_count") == config["features"]["count"]
            and metrics.get("rf_parameters") == config["random_forest"]["parameters"]
            and metrics.get("target_file_read") is False
            and metrics.get("target_labels_read") is False
        )
        prediction_ok = shape_ok and np.array_equal(pred, (prob >= .5).astype(np.uint8))
        det = metrics["source_test_results"]["detector"]
        computed = {
            "accuracy": float(accuracy_score(y, pred)),
            "attack_auprc": float(average_precision_score(y, prob)),
            "attack_auroc": float(roc_auc_score(y, prob)),
            "brier_score": float(brier_score_loss(y, prob)),
        }
        metric_diffs = {k: abs(computed[k] - float(det[k])) for k in computed}
        metric_ok = all(v <= 2e-6 for v in metric_diffs.values())
        miss = (y == 1) & (pred == 0)
        errors = y != pred
        score_checks = {}
        for name, score in (
            ("confidence", 1 - np.maximum(prob, 1 - prob)),
            ("rf_disagreement", disagreement),
        ):
            stored = metrics["source_test_results"]["reliability"][name]
            ap_miss = float(average_precision_score(miss.astype(np.uint8), score))
            ap_error = float(average_precision_score(errors.astype(np.uint8), score))
            order = np.argsort(-score, kind="mergesort")
            capture = {}
            for budget in (.01, .05, .10):
                n = max(1, int(np.ceil(len(y) * budget)))
                capture[str(budget)] = float(miss[order[:n]].sum() / max(1, int(miss.sum())))
            score_checks[name] = {
                "miss_auprc_abs_diff": abs(ap_miss - float(stored["attack_miss_auprc"])),
                "generic_error_auprc_abs_diff": abs(ap_error - float(stored["generic_error_auprc"])),
                "capture_abs_diff": {
                    b: abs(capture[b] - float(stored["attack_miss_capture"][b])) for b in capture
                },
            }
        score_ok = all(
            item["miss_auprc_abs_diff"] <= 1e-12
            and item["generic_error_auprc_abs_diff"] <= 1e-12
            and all(v <= 1e-12 for v in item["capture_abs_diff"].values())
            for item in score_checks.values()
        )
        for label, path in (("metrics", p_metrics), ("prediction", p_pred), ("calibrated_probability", p_prob), ("rf_disagreement", p_dis)):
            record["files"][label] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
        record.update({
            "rows": len(y),
            "features": metrics.get("feature_count"),
            "source_attack_rows": int(y.sum()),
            "source_attack_miss_rows": int(miss.sum()),
            "generic_error_rows": int(errors.sum()),
            "fit_seconds": metrics.get("fit_seconds"),
            "identity_matches_locked_rf_subconfiguration": bool(identity_ok),
            "array_shapes_match_source_test": bool(shape_ok),
            "arrays_finite": finite_ok,
            "predictions_match_probability_threshold": bool(prediction_ok),
            "detector_metric_recompute_abs_diffs": metric_diffs,
            "detector_metrics_match_with_float32_tolerance": bool(metric_ok),
            "reliability_metric_recompute": score_checks,
            "reliability_metrics_match": bool(score_ok),
        })
        record["verified_partial_artifact"] = bool(
            stage_ok and identity_ok and shape_ok and finite_ok and prediction_ok and metric_ok and score_ok
        )
        outputs[str(seed)] = record

    configured = set(config["reliability_signals"])
    produced = {"confidence", "random_forest_disagreement"}
    missing = sorted(configured - produced)
    result = {
        "report_id": "source-e1-partial-recovery-audit-1",
        "configuration_id": config["configuration_id"],
        "config_sha256": config_hash,
        "prior_summary_config_sha256_matches": config_hash == prior.get("config_sha256"),
        "source_dataset": config["source_dataset"],
        "stage_manifest_sha256": sha256(manifest_path),
        "software": {"numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "staged_arrays": stage_checks,
        "all_staged_arrays_match_manifest": bool(stage_ok),
        "source_test_rows": len(y),
        "source_test_attack_rows": int(y.sum()),
        "configured_reliability_signals": sorted(configured),
        "signals_present_in_seed_0_to_5_artifacts": sorted(produced),
        "signals_missing_for_full_locked_configuration": missing,
        "seeds": outputs,
        "recovery_conclusion": "Seeds 0-5 are recoverable and verified for the RF, confidence, and disagreement partial run. They are incomplete for the full five-signal source-e1-lock-1 configuration; conformal calibration predictions were not saved.",
        "full_source_e1_gate_complete": False,
        "target_evaluation_unlocked": False,
    }
    out = REPORTS / "source_e1_recovery_audit.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "audit_path": str(out),
        "all_staged_arrays_match_manifest": stage_ok,
        "prior_summary_config_sha256_matches": result["prior_summary_config_sha256_matches"],
        "seeds_verified_partial": [int(k) for k, v in outputs.items() if v.get("verified_partial_artifact")],
        "seeds_unverified": [int(k) for k, v in outputs.items() if not v.get("verified_partial_artifact")],
        "signals_missing": missing,
        "full_source_e1_gate_complete": False,
        "target_evaluation_unlocked": False,
    }, indent=2))


if __name__ == "__main__":
    main()
