"""Source-only E1 signals. No target dataset path is used in this module."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, brier_score_loss, roc_auc_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/source-e1-lock-1"
CONFIG_PATH = ROOT / "reports/nf_v3_audit/source_e1_config.json"
RUNS = DATA / "full_runs"
COMMON = RUNS / "common"
LOG = DATA / "runlogs" / "source-e1-full.log"
WORKERS = 2
THREADS = 1


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def event(msg: str) -> None:
    text = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(text, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n")


def cal_mask(x: np.ndarray) -> np.ndarray:
    return np.fromiter(
        (int.from_bytes(hashlib.sha256(b"source-e1-cal-v1\x00" + row.tobytes()).digest()[:8], "big") % 100 < 50 for row in x),
        dtype=np.bool_, count=len(x),
    )


def rf_config(cfg: dict, seed: int) -> RandomForestClassifier:
    return RandomForestClassifier(**{**cfg["random_forest"]["parameters"], "random_state": seed})


def binary_scores(prob: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    p = np.column_stack((prob, 1.0 - prob))
    return p, p.argmax(axis=1).astype(np.uint8)


def distance_full() -> None:
    """Exact deterministic 5-NN source-test distance with resumable query chunks."""
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    COMMON.mkdir(parents=True, exist_ok=True)
    final = COMMON / "feature_space_distance.npy"
    meta_path = COMMON / "feature_space_distance.json"
    part = COMMON / "feature_space_distance.partial.npy"
    checkpoint = COMMON / "feature_space_distance.checkpoint.json"
    scaled_path = COMMON / "source_train_standardized.float64.npy"
    scaled_partial = COMMON / "source_train_standardized.partial.npy"
    scaled_meta_path = COMMON / "source_train_standardized.json"
    xtr = np.load(DATA / "train_X.npy", mmap_mode="r")
    xte = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    identity = {
        "configuration_id": cfg["configuration_id"],
        "config_sha256": sha256(CONFIG_PATH),
        "stage_manifest_sha256": sha256(DATA / "stage_manifest.json"),
        "train_X_sha256": sha256(DATA / "train_X.npy"),
        "source_test_X_sha256": sha256(DATA / "source_test_X.npy"),
        "reference_rows": len(xtr), "query_rows": len(xte),
        "features": cfg["features"]["columns"], "feature_count": int(xtr.shape[1]),
        "scaler": "sklearn StandardScaler fit only on all UNSW source-train rows",
        "metric": "Euclidean", "neighbors": 5, "algorithm": "sklearn NearestNeighbors KDTree, leaf_size=30, n_jobs=1",
        "score": "mean distance to the five nearest source-train rows",
    }
    if final.exists() and meta_path.exists():
        existing = json.loads(meta_path.read_text(encoding="utf-8"))
        if all(existing.get(k) == v for k, v in identity.items()) and existing.get("score_sha256") == sha256(final):
            event("distance artifact already verified; reuse")
            return
        raise RuntimeError("Existing completed distance artifact does not match frozen inputs/config; preserving it")
    if final.exists() or meta_