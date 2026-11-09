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
DIRECTION = "unsw-to-cic"


def configure_direction(direction: str) -> None:
    """Select the source-only E1 config/data for the requested transfer direction."""
    global DATA, CONFIG_PATH, RUNS, COMMON, LOG, DIRECTION, WORKERS
    if direction == "unsw-to-cic":
        DATA = ROOT / "data/processed/source-e1-lock-1"
        CONFIG_PATH = ROOT / "reports/nf_v3_audit/source_e1_config.json"
        WORKERS = 2
    elif direction == "cic-to-unsw":
        DATA = ROOT / "data/processed/source-e1-cic-lock-1"
        CONFIG_PATH = ROOT / "reports/nf_v3_audit/source_e1_cic_config.json"
        WORKERS = 1
    else:
        raise ValueError(f"Unsupported source direction: {direction}")
    DIRECTION = direction
    RUNS = DATA / "full_runs"
    COMMON = RUNS / "common"
    LOG = DATA / "runlogs" / "source-e1-full.log"


def require_cic_manifest(cfg: dict) -> tuple[str | None, str | None]:
    if DIRECTION != "cic-to-unsw":
        return None, None
    import subprocess

    manifest_path = ROOT / "reports/nf_v3_audit/source_e1_cic_experiment_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("CIC full source runs require the committed source E1 experiment manifest")
    relative = manifest_path.relative_to(ROOT).as_posix()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", relative], cwd=ROOT,
                             capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain", "--", relative], cwd=ROOT,
                           capture_output=True, text=True)
    whole_tree_dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                      capture_output=True, text=True)
    if tracked.returncode != 0 or dirty.stdout.strip() or whole_tree_dirty.stdout.strip():
        raise RuntimeError("CIC experiment manifest is not committed and clean")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lock_commit = manifest.get("lock_commit")
    if (manifest.get("direction") != DIRECTION
            or manifest.get("status") != "frozen"
            or manifest.get("configuration_id") != cfg["configuration_id"]
            or manifest.get("configuration_sha256") != sha256(CONFIG_PATH)
            or manifest.get("stage_manifest_sha256") != sha256(DATA / "stage_manifest.json")
            or manifest.get("source_dataset_sha256") != cfg["source_dataset"]["sha256"]
            or not manifest.get("distance_execution", {}).get("mathematically_equivalent", False)
            or manifest.get("target_access") != {"features_read": False, "labels_read": False}):
        raise RuntimeError("CIC experiment manifest does not bind the current direction/config/stage")
    for name, expected in manifest.get("code_sha256", {}).items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"CIC experiment manifest code hash mismatch: {name}")
    for name, expected in manifest.get("benchmark_reports", {}).items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"CIC experiment manifest benchmark hash mismatch: {name}")
    if manifest.get("software_lock_sha256") != sha256(ROOT / "uv.lock"):
        raise RuntimeError("CIC experiment manifest software-lock hash mismatch")
    if not lock_commit or subprocess.run(
        ["git", "merge-base", "--is-ancestor", lock_commit, "HEAD"], cwd=ROOT
    ).returncode != 0:
        raise RuntimeError("CIC experiment manifest is not descended from its lock commit")
    return sha256(manifest_path), lock_commit


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


def deterministic_smoke_sample(x: np.ndarray, y: np.ndarray, per_class: int) -> tuple[np.ndarray, np.ndarray]:
    """Select an input-order-preserving class-present sample for plumbing smoke only."""
    labels = np.unique(y)
    if len(labels) != 2:
        raise ValueError("Five-signal smoke requires both source classes in each partition")
    selected = []
    for label in labels:
        rows = np.flatnonzero(y == label)
        if len(rows) < per_class:
            raise ValueError(f"Not enough source rows for smoke label {label}")
        selected.append(rows[:per_class])
    indices = np.sort(np.concatenate(selected))
    return np.asarray(x[indices]), np.asarray(y[indices])


def distance_full() -> None:
    """Exact deterministic 5-NN source-test distance with resumable query chunks."""
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if cfg["configuration_id"] == "source-e1-cic-lock-1":
        from cic_exact_chunked_5nn import compute_cic_feature_distance

        manifest_sha256, lock_commit = require_cic_manifest(cfg)
        event("distance: CIC exact chunked duplicate-compression path; no approximation")
        result = compute_cic_feature_distance(cfg, CONFIG_PATH, DATA, COMMON,
                                              manifest_sha256, lock_commit)
        event(f"distance: CIC {result['status']}; score_sha256={result.get('score_sha256')}")
        return
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
    if final.exists() or meta_path.exists():
        raise RuntimeError("Incomplete distance artifact pair exists; inspect before resume")

    scaler_path = COMMON / "scaler.json"
    if scaled_path.exists():
        if not scaled_meta_path.exists():
            raise RuntimeError("Standardized train map has no completion metadata; inspect before reuse")
        scaled_meta = json.loads(scaled_meta_path.read_text(encoding="utf-8"))
        if not all(scaled_meta.get(k) == v for k, v in identity.items()) or scaled_meta.get("array_sha256") != sha256(scaled_path):
            raise RuntimeError("Standardized train map does not match inputs/config; preserving it")
        scaler_info = json.loads(scaler_path.read_text(encoding="utf-8"))
        scaler = StandardScaler(copy=True)
        scaler.mean_ = np.asarray(scaler_info["mean"], dtype=np.float64)
        scaler.scale_ = np.asarray(scaler_info["scale"], dtype=np.float64)
        scaler.var_ = scaler.scale_ ** 2
        scaler.n_features_in_ = len(scaler.mean_)
        event("distance: reuse integrity-verified standardized source-train map")
    elif scaled_partial.exists():
        raise RuntimeError("Incomplete standardized train map exists; inspect it before restarting transformation")
    else:
        event("distance: fitting StandardScaler on full source train")
        with threadpool_limits(limits=THREADS):
            scaler = StandardScaler(copy=True).fit(xtr)
        scaler_info = {
            "mean_sha256": hashlib.sha256(np.asarray(scaler.mean_, dtype=np.float64).tobytes()).hexdigest(),
            "scale_sha256": hashlib.sha256(np.asarray(scaler.scale_, dtype=np.float64).tobytes()).hexdigest(),
            "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
        }
        scaler_path.write_text(json.dumps({**identity, **scaler_info}, indent=2) + "\n", encoding="utf-8")
        event("distance: transforming source train in 20000-row blocks to float64 disk map")
        ztr = np.lib.format.open_memmap(scaled_partial, mode="w+", dtype=np.float64, shape=xtr.shape)
        for start in range(0, len(xtr), 20000):
            end = min(start + 20000, len(xtr))
            ztr[start:end] = scaler.transform(xtr[start:end])
            if end == len(xtr) or end % 200000 == 0:
                ztr.flush()
                event(f"distance: transformed {end}/{len(xtr)} train rows")
        ztr.flush()
        del ztr
        os.replace(scaled_partial, scaled_path)
        scaled_meta_path.write_text(json.dumps({**identity, "array_sha256": sha256(scaled_path), "dtype": "float64", "completed_utc": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n", encoding="utf-8")

    ztr = np.load(scaled_path, mmap_mode="r")
    event("distance: fitting exact KDTree")
    nn = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30, metric="euclidean", n_jobs=1).fit(ztr)
    done = 0
    if checkpoint.exists() or part.exists():
        if not (checkpoint.exists() and part.exists()):
            raise RuntimeError("Partial distance output/checkpoint mismatch; preserving files")
        cp = json.loads(checkpoint.read_text(encoding="utf-8"))
        if not all(cp.get(k) == v for k, v in identity.items()):
            raise RuntimeError("Partial distance output provenance mismatch; preserving files")
        done = int(cp["completed_query_rows"])
        if not 0 <= done <= len(xte):
            raise RuntimeError("Invalid distance checkpoint row count")
        values = np.load(part, mmap_mode="r+")
        if values.shape != (len(xte),):
            raise RuntimeError("Partial distance output shape mismatch")
    else:
        values = np.lib.format.open_memmap(part, mode="w+", dtype=np.float32, shape=(len(xte),))
    event(f"distance: querying {len(xte)} test rows from {len(xtr)} train references; resume={done}")
    last_report = done
    t0 = time.perf_counter()
    with threadpool_limits(limits=THREADS):
        for start in range(done, len(xte), 2048):
            end = min(start + 2048, len(xte))
            q = scaler.transform(xte[start:end])
            d, _ = nn.kneighbors(q, return_distance=True)
            values[start:end] = d.mean(axis=1).astype(np.float32)
            if end - last_report >= 8192 or end == len(xte):
                values.flush()
                checkpoint.write_text(json.dumps({**identity, "completed_query_rows": end, "elapsed_seconds": time.perf_counter() - t0}, indent=2) + "\n", encoding="utf-8")
                event(f"distance: completed {end}/{len(xte)} query rows; elapsed={time.perf_counter()-t0:.1f}s")
                last_report = end
    values.flush()
    del values, nn, ztr
    os.replace(part, final)
    meta_path.write_text(json.dumps({**identity, "score_sha256": sha256(final), "dtype": "float32", "completed_utc": datetime.now(timezone.utc).isoformat(), "scaler_provenance": "scaler.json"}, indent=2) + "\n", encoding="utf-8")
    checkpoint.unlink(missing_ok=True)
    scaled_path.unlink(missing_ok=True)
    event(f"distance: complete; score_sha256={sha256(final)}")


def metric_bundle(y: np.ndarray, pred: np.ndarray, probability: np.ndarray, scores: dict[str, np.ndarray]) -> dict:
    misses = (y == 1) & (pred == 0)
    errors = y != pred
    detector = {
        "accuracy": float(accuracy_score(y, pred)),
        "attack_auprc": float(average_precision_score(y, probability)),
        "attack_auroc": float(roc_auc_score(y, probability)),
        "attack_miss_rows": int(misses.sum()),
        "generic_error_rows": int(errors.sum()),
        "brier_score": float(brier_score_loss(y, probability)),
    }
    signals = {}
    for name, risk in scores.items():
        order = np.argsort(-risk, kind="mergesort")
        captures = {}
        for budget in (.01, .05, .10):
            n = max(1, int(np.ceil(len(y) * budget)))
            captures[str(budget)] = (float(misses[order[:n]].sum() / int(misses.sum()))
                                     if misses.any() else None)
        signals[name] = {
            "generic_error_auprc": (float(average_precision_score(errors.astype(np.uint8), risk))
                                    if errors.any() else None),
            "attack_miss_auprc": (float(average_precision_score(misses.astype(np.uint8), risk))
                                  if misses.any() else None),
            "ranking_endpoints_defined": bool(errors.any() and misses.any()),
            "attack_miss_capture": captures,
            "score_distribution": {"min": float(np.min(risk)), "p25": float(np.quantile(risk, .25)), "median": float(np.median(risk)), "p75": float(np.quantile(risk, .75)), "max": float(np.max(risk)), "mean": float(np.mean(risk)), "std": float(np.std(risk))},
        }
    return {"detector": detector, "reliability": signals}


def run_seed(seed: int, *, smoke: bool = False, repeat: bool = False) -> dict:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    manifest_sha256, manifest_lock_commit = require_cic_manifest(cfg) if not smoke else (None, None)
    xtr = np.load(DATA / "train_X.npy", mmap_mode="r")
    ytr = np.load(DATA / "train_y.npy", mmap_mode="r")
    xcal = np.load(DATA / "calibration_X.npy", mmap_mode="r")
    ycal = np.load(DATA / "calibration_y.npy", mmap_mode="r")
    xte = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    yte = np.asarray(np.load(DATA / "source_test_y.npy", mmap_mode="r"), dtype=np.uint8)
    if smoke:
        xtr, ytr = deterministic_smoke_sample(xtr, ytr, 2500)
        xcal, ycal = deterministic_smoke_sample(xcal, ycal, 1000)
        xte, yte = deterministic_smoke_sample(xte, yte, 1000)
    mask = cal_mask(xcal)
    model = rf_config(cfg, seed)
    tfit = time.perf_counter()
    with threadpool_limits(limits=THREADS):
        model.fit(xtr, ytr)
        fit_seconds = time.perf_counter() - tfit
        raw_cal = np.clip(model.predict_proba(xcal[mask])[:, 1], 1e-7, 1 - 1e-7)
        logits_cal = np.log(raw_cal / (1 - raw_cal)).reshape(-1, 1)
        calibrator = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=seed)
        calibrator.fit(logits_cal, ycal[mask])
        raw_test = np.clip(model.predict_proba(xte)[:, 1], 1e-7, 1 - 1e-7)
        probability = calibrator.predict_proba(np.log(raw_test / (1 - raw_test)).reshape(-1, 1))[:, 1].astype(np.float32)
        pred = (probability >= .5).astype(np.uint8)
        votes = np.zeros((len(yte), 2), dtype=np.uint8)
        rows = np.arange(len(yte))
        for tree in model.estimators_:
            tree_pred = tree.predict(xte).astype(np.uint8, copy=False)
            votes[rows, tree_pred] += 1
        disagreement = (1 - votes.max(axis=1).astype(np.float32) / len(model.estimators_)).astype(np.float32)
        xconf = xcal[~mask]
        raw_conf = np.clip(model.predict_proba(xconf)[:, 1], 1e-7, 1 - 1e-7)
        pconf = calibrator.predict_proba(np.log(raw_conf / (1 - raw_conf)).reshape(-1, 1))[:, 1]
    recovered = None
    if not smoke and seed < 6 and (DATA / f"seed-{seed}" / "metrics.json").exists():
        old = DATA / f"seed-{seed}"
        old_metrics = json.loads((old / "metrics.json").read_text(encoding="utf-8"))
        old_probability = np.load(old / "calibrated_probability.npy", mmap_mode="r")
        old_prediction = np.load(old / "prediction.npy", mmap_mode="r")
        old_disagreement = np.load(old / "rf_disagreement.npy", mmap_mode="r")
        recovered = {
            "seed": seed,
            "prior_metrics_sha256": sha256(old / "metrics.json"),
            "prior_probability_sha256": sha256(old / "calibrated_probability.npy"),
            "prior_prediction_sha256": sha256(old / "prediction.npy"),
            "prior_disagreement_sha256": sha256(old / "rf_disagreement.npy"),
            "probability_exact_match": bool(np.array_equal(probability, old_probability)),
            "prediction_exact_match": bool(np.array_equal(pred, old_prediction)),
            "disagreement_exact_match": bool(np.array_equal(disagreement, old_disagreement)),
            "prior_config_id": old_metrics.get("configuration_id"),
        }
        recovered["recovered_outputs_reused"] = all(recovered[k] for k in ("probability_exact_match", "prediction_exact_match", "disagreement_exact_match"))
        if recovered["recovered_outputs_reused"]:
            probability, pred, disagreement = old_probability, old_prediction, old_disagreement
    yconf = np.asarray(ycal[~mask], dtype=np.uint8)
    pconf_true = np.where(yconf == 1, pconf, 1 - pconf)
    nonconf = 1 - pconf_true
    alpha = cfg["reliability_signals"]["split_conformal"]["alpha"]
    qidx = min(len(nonconf), int(np.ceil((len(nonconf) + 1) * (1 - alpha)))) - 1
    q = float(np.partition(nonconf, qidx)[qidx])
    class_prob = np.column_stack((probability, 1 - probability))
    class_nonconf = 1 - class_prob
    prediction_set = (class_nonconf <= q)
    conformal_score = ((prediction_set.sum(axis=1).astype(np.float32) - 1) / 1.0).astype(np.float32)

    ifcfg = cfg["reliability_signals"]["isolation_forest"]
    with threadpool_limits(limits=THREADS):
        iso = IsolationForest(n_estimators=ifcfg["n_estimators"], max_samples=ifcfg["max_samples"], max_features=ifcfg["max_features"], contamination=ifcfg["contamination"], bootstrap=ifcfg["bootstrap"], random_state=seed, n_jobs=1)
        iso.fit(xtr)
        isolation = (-iso.score_samples(xte)).astype(np.float32)

    confidence = (1 - np.maximum(probability, 1 - probability)).astype(np.float32)
    if smoke:
        scaler = StandardScaler().fit(xtr)
        ref = scaler.transform(xtr)
        qry = scaler.transform(xte)
        nn = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30, metric="euclidean", n_jobs=1).fit(ref)
        distance = nn.kneighbors(qry, return_distance=True)[0].mean(axis=1).astype(np.float32)
    else:
        distance_path = COMMON / "feature_space_distance.npy"
        distance_meta = json.loads((COMMON / "feature_space_distance.json").read_text(encoding="utf-8"))
        if distance_meta.get("score_sha256") != sha256(distance_path):
            raise RuntimeError("Completed source-only distance artifact failed its integrity check")
        distance = np.load(distance_path, mmap_mode="r")

    scores = {"confidence": confidence, "random_forest_disagreement": disagreement, "feature_space_distance": distance, "split_conformal": conformal_score, "isolation_forest": isolation}
    if not all(np.isfinite(v).all() for v in scores.values()):
        raise RuntimeError(f"Non-finite reliability score for seed {seed}")
    if smoke:
        if any(v.shape != yte.shape for v in scores.values()):
            raise RuntimeError("Smoke output shape mismatch")
        return {"direction": DIRECTION, "seed": seed, "rows": len(yte), "features": int(xtr.shape[1]), "fit_seconds": fit_seconds, "conformal_quantile": q, "score_shapes": {k: list(v.shape) for k, v in scores.items()}, "all_finite": True, "target_access": False, "metrics": metric_bundle(yte, pred, probability, scores)}

    final_dir = (RUNS / "repeats" / f"seed-{seed}-repeat-1") if repeat else (RUNS / f"seed-{seed}")
    partial_dir = final_dir.with_name(final_dir.name + ".partial")
    if final_dir.exists() or partial_dir.exists():
        raise RuntimeError(f"Refusing to overwrite or resume unreviewed output for seed {seed}")
    partial_dir.mkdir(parents=True)
    np.save(partial_dir / "prediction.npy", pred)
    np.save(partial_dir / "calibrated_probability.npy", probability)
    for name, values in scores.items():
        np.save(partial_dir / f"{name}.npy", np.asarray(values, dtype=np.float32))
    report = {
        "run_id": f"source-e1-{DIRECTION}-seed-{seed}-full" + ("-repeat-1" if repeat else ""),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "direction": DIRECTION,
        "same_seed_repeat": repeat,
        "configuration_id": cfg["configuration_id"], "config_sha256": sha256(CONFIG_PATH),
        "experiment_manifest_sha256": manifest_sha256, "manifest_lock_commit": manifest_lock_commit,
        "stage_manifest_sha256": sha256(DATA / "stage_manifest.json"), "source_sha256": cfg["source_dataset"]["sha256"],
        "target_file_read": False, "target_labels_read": False, "seed": seed,
        "train_rows": len(ytr), "calibration_probability_rows": int(mask.sum()), "conformal_calibration_rows": len(yconf),
        "source_test_rows": len(yte), "feature_count": int(xtr.shape[1]), "feature_order": cfg["features"]["columns"],
        "rf_parameters": {**cfg["random_forest"]["parameters"], "random_state": seed},
        "worker_count": WORKERS,
        "thread_limits": {"OpenMP": THREADS, "BLAS": THREADS, "RF_n_jobs": 1, "IsolationForest_n_jobs": 1},
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "fit_seconds": fit_seconds, "calibration": {"method": "Platt sigmoid", "conformal_quantile": q, "alpha": alpha, "quantile_index_zero_based": qidx},
        "source_test_results": metric_bundle(yte, pred, probability, scores),
        "signal_dependencies": {"confidence": "RF seed + calibrator", "random_forest_disagreement": "RF seed", "feature_space_distance": "shared source-train scaler/reference; seed-independent", "split_conformal": "RF seed + source calibration predictions", "isolation_forest": f"source train; random_state={seed}; independent of RF predictions but seed-varied by frozen config"},
        "recovered_partial_artifacts": recovered,
        "provenance": "complete five-signal source-only E1; full-run outputs are separate from recovered pilot artifacts",
    }
    report["artifact_sha256"] = {p.name: sha256(p) for p in sorted(partial_dir.glob("*.npy"))}
    (partial_dir / "metrics.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    os.replace(partial_dir, final_dir)
    event(f"seed {seed}: complete; RF fit {fit_seconds:.1f}s; attack misses={report['source_test_results']['detector']['attack_miss_rows']}")
    return report


def verify_seed_repeat(seed: int) -> dict:
    primary = RUNS / f"seed-{seed}"
    repeat = RUNS / "repeats" / f"seed-{seed}-repeat-1"
    if not (primary / "metrics.json").exists() or not (repeat / "metrics.json").exists():
        raise RuntimeError("Both primary and repeat seed artifacts must exist")
    files = ["prediction.npy", "calibrated_probability.npy", "confidence.npy",
             "random_forest_disagreement.npy", "feature_space_distance.npy",
             "split_conformal.npy", "isolation_forest.npy"]
    compared = {}
    for name in files:
        left, right = primary / name, repeat / name
        if not left.exists() or not right.exists():
            raise RuntimeError(f"Repeat comparison is missing {name}")
        a, b = np.load(left, mmap_mode="r"), np.load(right, mmap_mode="r")
        same_shape = a.shape == b.shape
        equal = bool(same_shape and np.array_equal(a, b))
        finite = bool(np.isfinite(a).all() and np.isfinite(b).all())
        compared[name] = {"shape": list(a.shape), "shape_match": same_shape,
                          "exact_array_match": equal, "both_finite": finite,
                          "primary_sha256": sha256(left), "repeat_sha256": sha256(right)}
        if not (same_shape and equal and finite):
            raise RuntimeError(f"Same-seed repeat mismatch: {name}")
    manifest_path = ROOT / "reports/nf_v3_audit/source_e1_cic_experiment_manifest.json"
    result = {
        "report_id": f"source-e1-{DIRECTION}-same-seed-repeat-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "direction": DIRECTION, "seed": seed, "files": compared,
        "experiment_manifest_sha256": sha256(manifest_path) if manifest_path.exists() else None,
        "target_file_read": False, "target_labels_read": False,
        "conclusion": "All saved source-test signal arrays, calibrated probabilities, and predictions exactly match the independent repeat.",
    }
    path = ROOT / "reports/nf_v3_audit" / f"{DIRECTION.replace('-', '_')}_same_seed_repeat.json"
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite repeat evidence: {path}")
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", choices=("unsw-to-cic", "cic-to-unsw"), default="unsw-to-cic")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--distance", action="store_true")
    group.add_argument("--smoke", action="store_true")
    group.add_argument("--seeds", nargs="+", type=int)
    group.add_argument("--repeat-seed", type=int)
    group.add_argument("--verify-repeat-seed", type=int)
    args = ap.parse_args()
    configure_direction(args.direction)
    if args.distance:
        distance_full()
        return
    if args.smoke:
        result = run_seed(0, smoke=True)
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        result["report_id"] = "source-e1-full-pipeline-smoke-1"
        result["generated_utc"] = datetime.now(timezone.utc).isoformat()
        result["configuration_id"] = cfg["configuration_id"]
        result["config_sha256"] = sha256(CONFIG_PATH)
        result["stage_manifest_sha256"] = sha256(DATA / "stage_manifest.json")
        result["target_file_read"] = False
        result["target_labels_read"] = False
        result["software"] = {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__}
        result["thread_limits"] = {"OpenMP": THREADS, "BLAS": THREADS, "RF_n_jobs": 1, "IsolationForest_n_jobs": 1}
        result["worker_count"] = WORKERS
        result["note"] = "Plumbing-only deterministic class-present source subset; metrics are not final E1 results. No full-run outputs were written."
        smoke_name = ("source_e1_smoke_cic-to-unsw_chunked_5signal.json"
                      if DIRECTION == "cic-to-unsw" else "source_e1_smoke_test.json")
        smoke_path = ROOT / "reports/nf_v3_audit" / smoke_name
        if smoke_path.exists():
            raise RuntimeError(f"Refusing to overwrite existing smoke evidence: {smoke_path}")
        smoke_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return
    if args.repeat_seed is not None:
        if args.repeat_seed not in range(10):
            raise SystemExit("Repeat seed must be in 0..9")
        RUNS.mkdir(parents=True, exist_ok=True)
        result = run_seed(args.repeat_seed, repeat=True)
        print(json.dumps({"repeat_seed_completed": args.repeat_seed, "report": result}, indent=2))
        return
    if args.verify_repeat_seed is not None:
        if args.verify_repeat_seed not in range(10):
            raise SystemExit("Repeat seed must be in 0..9")
        print(json.dumps(verify_seed_repeat(args.verify_repeat_seed), indent=2))
        return
    seeds = args.seeds
    if len(seeds) != len(set(seeds)) or any(s not in range(10) for s in seeds):
        raise SystemExit("Seeds must be unique values in 0..9")
    RUNS.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=THREADS):
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = [pool.submit(run_seed, seed) for seed in seeds]
            results = [f.result() for f in futures]
    print(json.dumps({"completed_seeds": [r["seed"] for r in results], "worker_count": WORKERS}, indent=2))


if __name__ == "__main__":
    main()
