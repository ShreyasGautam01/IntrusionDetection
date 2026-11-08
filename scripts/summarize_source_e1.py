"""Integrity-check and summarize completed source-only E1 outputs."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import rankdata
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/source-e1-lock-1"
RUNS = DATA / "full_runs"
REPORTS = ROOT / "reports/nf_v3_audit"
SIGNALS = ["confidence", "random_forest_disagreement", "feature_space_distance", "split_conformal", "isolation_forest"]
FILES = {name: f"{name}.npy" for name in SIGNALS}
FILES["prediction"] = "prediction.npy"
FILES["calibrated_probability"] = "calibrated_probability.npy"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stats(values: list[float]) -> dict:
    a = np.asarray(values, dtype=np.float64)
    return {"median": float(np.median(a)), "q1": float(np.quantile(a, .25)), "q3": float(np.quantile(a, .75)), "iqr": float(np.quantile(a, .75) - np.quantile(a, .25)), "min": float(np.min(a)), "max": float(np.max(a))}


def summarize() -> dict:
    y = np.asarray(np.load(DATA / "source_test_y.npy", mmap_mode="r"), dtype=np.uint8)
    miss_counts = int(y.sum())
    per_seed = {}
    score_arrays = {name: [] for name in SIGNALS}
    metric_arrays: dict[str, list[float]] = {}
    valid = True
    for seed in range(10):
        folder = RUNS / f"seed-{seed}"
        metrics_path = folder / "metrics.json"
        m = json.loads(metrics_path.read_text(encoding="utf-8"))
        values = {name: np.load(folder / filename, mmap_mode="r") for name, filename in FILES.items()}
        checks = {name: values[name].shape == y.shape for name in FILES}
        finite = {name: bool(np.isfinite(values[name]).all()) for name in FILES}
        hashes = {filename: sha256(folder / filename) for filename in FILES.values()}
        hash_match = all(hashes[name] == m["artifact_sha256"].get(name) for name in FILES.values())
        source_results = m["source_test_results"]
        identity_ok = (m.get("seed") == seed and m.get("configuration_id") == "source-e1-lock-1" and m.get("target_file_read") is False and m.get("target_labels_read") is False and m.get("source_test_rows") == len(y) and m.get("feature_count") == 46)
        ok = all(checks.values()) and all(finite.values()) and hash_match and identity_ok
        valid &= ok
        pred = np.asarray(values["prediction"], dtype=np.uint8)
        prob = np.asarray(values["calibrated_probability"], dtype=np.float32)
        misses = (y == 1) & (pred == 0)
        errors = y != pred
        detector = {
            "accuracy": float(accuracy_score(y, pred)),
            "attack_auprc": float(average_precision_score(y, prob)),
            "attack_auroc": float(roc_auc_score(y, prob)),
            "brier_score": float(brier_score_loss(y, prob)),
            "attack_miss_rows": int(misses.sum()),
            "generic_error_rows": int(errors.sum()),
        }
        key_values = {f"detector.{k}": v for k, v in detector.items() if isinstance(v, (float, int)) and k not in ("attack_miss_rows", "generic_error_rows")}
        for name in SIGNALS:
            risk = np.asarray(values[name], dtype=np.float32)
            key_values[f"{name}.generic_error_auprc"] = float(average_precision_score(errors.astype(np.uint8), risk))
            key_values[f"{name}.attack_miss_auprc"] = float(average_precision_score(misses.astype(np.uint8), risk))
            score_arrays[name].append(risk)
            order = np.argsort(-risk, kind="mergesort")
            for budget in (.01, .05, .10):
                n = max(1, int(np.ceil(len(y) * budget)))
                capture = float(misse