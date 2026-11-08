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