"""Bounded target inference benchmark with source-E1-verified seed models."""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/nf_v3_audit"
DATA = ROOT / "data/processed/target-transfer-v1"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_source_e1_cic import system_memory, timed  # noqa: E402
import run_source_e1_complete as e1  # noqa: E402
from run_source_e1_direction import DIRECTIONS  # noqa: E402
from target_transfer_common import (  # noqa: E402
    parse_source_preprocessed_batch,
    resolve_direction,
    sha256_file,
    source_replacements,
    target_feature_batches,
)

THREADS = 1


def source_identity(ctx, seed: int, metrics: dict) -> dict:
    stage = json.loads(ctx.stage_manifest.read_text(encoding="utf-8"))
    seed_dir = ctx.source_e1_seed_root / f"seed-{seed}"
    expected_names = (
        "prediction.npy", "calibrated_probability.npy",
        "random_forest_disagreement.npy", "isolation_forest.npy",
    )
    recorded = metrics.get("artifact_sha256", {})
    artifact_hashes = {}
    for name in expected_names:
        path = seed_dir / name
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if recorded.get(name) != actual:
            raise ValueError(f"Source E1 artifact hash mismatch: {name}")
        artifact_hashes[name] = actual
    if (metrics.get("configuration_id") != ctx.config["configuration_id"]
            or metrics.get("config_sha256") != sha256_file(ctx.config_path)
            or metrics.get("stage_manifest_sha256") != sha256_file(ctx.stage_manifest)
            or metrics.get("source_sha256") != ctx.config["source_dataset"]["sha256"]
            or int(metrics.get("seed", -1)) != seed
            or int(metrics.get("source_test_rows", -1)) != int(stage["partition_rows"]["source_test"])):
        raise ValueError("Source E1 seed metrics do not bind the current direction and source stage")
    return {
        "direction": ctx.direction,
        "seed": seed,
        "configuration_id": ctx.config["configuration_id"],
        "config_sha256": sha256_file(ctx.config_path),
        "stage_manifest_sha256": sha256_file(ctx.stage_manifest),
        "source_dataset_sha256": ctx.config["source_dataset"]["sha256"],
        "source_train_sha256": stage["files"]["train_X.npy"]["sha256"],
        "source_calibration_sha256": stage["files"]["calibration_X.npy"]["sha256"],
        "source_test_sha256": stage["files"]["source_test_X.npy"]["sha256"],
        "source_e1_metrics_sha256": sha256_file(ctx.source_e1_seed_root / f"seed-{seed}" / "metrics.json"),
        "source_e1_artifact_sha256": artifact_hashes,
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit_learn": sklearn.__version__, "joblib": joblib.__version__},
        "rf_parameters": {**ctx.config["random_forest"]["parameters"], "random_state": seed},
        "thread_limits": {"RF_n_jobs": 1, "IsolationForest_n_jobs": 1,
                          "BLAS": THREADS, "OpenMP": THREADS},
    }


def compare_source_outputs(ctx, seed: int, model, calibrator, isolation,
                           source_test: np.ndarray, seed_dir: Path,
                           batch_rows: int) -> dict:
    names = ("prediction.npy", "calibrated_probability.npy",
             "random_forest_disagreement.npy", "isolation_forest.npy")
    expected = {name: np.load(seed_dir / name, mmap_mode="r") for name in names}
    if any(array.shape != (len(source_test),) for array in expected.values()):
        raise ValueError("Source-E1 expected output shapes do not match source-test rows")
    match = {name: True for name in names}
    timing_parts = []
    for start in range(0, len(source_test), batch_rows):
        end = min(start + batch_rows, len(source_test))
        x = np.asarray(source_test[start:end], dtype=np.float32)
        with threadpool_limits(limits=THREADS):
            raw = np.clip(model.predict_proba(x)[:, 1], 1e-7, 1 - 1e-7)
            logits = np.log(raw / (1 - raw)).reshape(-1, 1)
            probability = calibrator.predict_proba(logits)[:, 1].astype(np.float32)
            prediction = (probability >= .5).astype(np.uint8)
            votes = np.zeros((len(x), 2), dtype=np.uint8)
            rows = np.arange(len(x))
            for tree in model.estimators_:
                tree_prediction = tree.predict(x).astype(np.uint8, copy=False)
                votes[rows, tree_prediction] += 1
            disagreement = (1 - votes.max(axis=1).astype(np.float32)
                            / len(model.estimators_)).astype(np.float32)
            iso_score = (-isolation.score_samples(x)).astype(np.float32)
        outputs = {
            "prediction.npy": prediction,
            "calibrated_probability.npy": probability,
            "random_forest_disagreement.npy": disagreement,
            "isolation_forest.npy": iso_score,
        }
        for name, values in outputs.items():
            if not np.isfinite(values).all() or not np.array_equal(values, expected[name][start:end]):
                match[name] = False
        timing_parts.append(end - start)
    if not all(match.values()):
        raise RuntimeError(f"Refit failed exact source-E1 verification: {match}")
    return {"exact_match": match, "rows_verified": len(source_test),
            "batch_rows": batch_rows, "row_blocks": len(timing_parts)}


def fit_or_load_seed(ctx, seed: int, batch_rows: int) -> tuple[object, object, object, dict]:
    e1.configure_direction(ctx.direction)
    cfg = ctx.config
    source_train = np.load(ctx.data_dir / "train_X.npy", mmap_mode="r")
    source_y = np.load(ctx.data_dir / "train_y.npy", mmap_mode="r")
    calibration_x = np.load(ctx.data_dir / "calibration_X.npy", mmap_mode="r")
    calibration_y = np.load(ctx.data_dir / "calibration_y.npy", mmap_mode="r")
    source_test = np.load(ctx.data_dir / "source_test_X.npy", mmap_mode="r")
    seed_dir = ctx.source_e1_seed_root / f"seed-{seed}"
    metrics_path = seed_dir / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    identity = source_identity(ctx, seed, metrics)
    model_dir = DATA / ctx.direction / "verified_models" / f"seed-{seed}"
    model_path = model_dir / "random_forest.joblib"
    calibrator_path = model_dir / "calibrator.joblib"
    isolation_path = model_dir / "isolation_forest.joblib"
    metadata_path = model_dir / "verified_models.json"
    existing = [p.exists() for p in (model_path, calibrator_path, isolation_path, metadata_path)]
    if any(existing) and not all(existing):
        raise RuntimeError(f"Partial verified model cache exists; preserving {model_dir}")
    if all(existing):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("identity") != identity:
            raise ValueError("Cached source models belong to different frozen inputs/configuration")
        expected_hashes = metadata.get("model_sha256", {})
        for name, path in (("random_forest", model_path), ("calibrator", calibrator_path),
                           ("isolation_forest", isolation_path)):
            if expected_hashes.get(name) != sha256_file(path):
                raise ValueError(f"Cached {name} model hash failed")
        model, calibrator, isolation = (joblib.load(model_path), joblib.load(calibrator_path),
                                         joblib.load(isolation_path))
        source_check = compare_source_outputs(ctx, seed, model, calibrator, isolation,
                                             source_test, seed_dir, batch_rows)
        metadata["cache_reused"] = True
        metadata["source_test_verification"] = source_check
        return model, calibrator, isolation, metadata

    if model_dir.exists():
        raise RuntimeError(f"Model cache path exists without a complete cache; preserving {model_dir}")
    model_dir.mkdir(parents=True)
    mask = e1.cal_mask(calibration_x)
    if int(mask.sum()) != int(metrics["calibration_probability_rows"]):
        raise ValueError("Source calibration hash split differs from the saved E1 result")
    model = e1.rf_config(cfg, seed)
    with threadpool_limits(limits=THREADS):
        model_fit, timing = timed(lambda: model.fit(source_train, source_y))
        del model_fit
        raw_cal = np.clip(model.predict_proba(calibration_x[mask])[:, 1], 1e-7, 1 - 1e-7)
        logits_cal = np.log(raw_cal / (1 - raw_cal)).reshape(-1, 1)
        calibrator = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=seed)
        calibrator_fit, calibration_timing = timed(lambda: calibrator.fit(logits_cal, calibration_y[mask]))
        del calibrator_fit
    rf_meta = {"identity": identity, "RF_fit_timing": timing,
               "calibrator_fit_timing": calibration_timing,
               "created_utc": datetime.now(timezone.utc).isoformat()}
    rf_tmp = model_path.with_suffix(".joblib.tmp")
    cal_tmp = calibrator_path.with_suffix(".joblib.tmp")
    joblib.dump(model, rf_tmp, compress=0)
    joblib.dump(calibrator, cal_tmp, compress=0)
    os.replace(rf_tmp, model_path)
    os.replace(cal_tmp, calibrator_path)

    ifcfg = cfg["reliability_signals"]["isolation_forest"]
    isolation = IsolationForest(
        n_estimators=ifcfg["n_estimators"], max_samples=ifcfg["max_samples"],
        max_features=ifcfg["max_features"], contamination=ifcfg["contamination"],
        bootstrap=ifcfg["bootstrap"], random_state=seed, n_jobs=1,
    )
    with threadpool_limits(limits=THREADS):
        isolation_fit, iso_timing = timed(lambda: isolation.fit(source_train))
        del isolation_fit
    iso_tmp = isolation_path.with_suffix(".joblib.tmp")
    joblib.dump(isolation, iso_tmp, compress=0)
    os.replace(iso_tmp, isolation_path)

    source_check = compare_source_outputs(ctx, seed, model, calibrator, isolation,
                                         source_test, seed_dir, batch_rows)
    metadata = {
        "identity": identity,
        "model_sha256": {"random_forest": sha256_file(model_path),
                         "calibrator": sha256_file(calibrator_path),
                         "isolation_forest": sha256_file(isolation_path)},
        "RF_fit_timing": timing, "calibrator_fit_timing": calibration_timing,
        "IsolationForest_fit_timing": iso_timing,
        "source_test_verification": source_check,
        "cache_reused": False,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return model, calibrator, isolation, metadata


def run_benchmark(direction: str, seed: int, query_rows: int, batch_rows: int) -> dict:
    ctx = resolve_direction(direction)
    if seed not in ctx.config["random_forest"]["seeds"]:
        raise ValueError("Seed is not declared in the frozen direction configuration")
    memory_before = system_memory()
    model, calibrator, isolation, model_meta = fit_or_load_seed(ctx, seed, batch_rows)
    sample = np.empty((query_rows, len(ctx.feature_order)), dtype=np.float32)
    written = 0
    replacements = source_replacements(ctx)
    def parse_sample() -> None:
        nonlocal written
        for _, raw_rows in target_feature_batches(ctx, batch_size=batch_rows):
            values = parse_source_preprocessed_batch(raw_rows, ctx.feature_order, replacements)
            take = min(len(values), query_rows - written)
            if take:
                sample[written:written + take] = values[:take]
                written += take
            if written == query_rows:
                break
        if written != query_rows:
            raise ValueError(f"Target feature iterator produced {written} rows; expected {query_rows}")
    _, parse_timing = timed(parse_sample)

    timings = {"rf_probability_wall_seconds": 0.0, "rf_disagreement_wall_seconds": 0.0,
               "isolation_forest_wall_seconds": 0.0}
    all_finite = True
    def infer_sample() -> bool:
        finite = True
        for start in range(0, len(sample), batch_rows):
            end = min(start + batch_rows, len(sample))
            x = sample[start:end]
            with threadpool_limits(limits=THREADS):
                t0 = time.perf_counter()
                raw = np.clip(model.predict_proba(x)[:, 1], 1e-7, 1 - 1e-7)
                logits = np.log(raw / (1 - raw)).reshape(-1, 1)
                probability = calibrator.predict_proba(logits)[:, 1].astype(np.float32)
                confidence = (1 - np.maximum(probability, 1 - probability)).astype(np.float32)
                timings["rf_probability_wall_seconds"] += time.perf_counter() - t0

                t0 = time.perf_counter()
                votes = np.zeros((len(x), 2), dtype=np.uint8)
                rows = np.arange(len(x))
                for tree in model.estimators_:
                    prediction = tree.predict(x).astype(np.uint8, copy=False)
                    votes[rows, prediction] += 1
                disagreement = (1 - votes.max(axis=1).astype(np.float32)
                                / len(model.estimators_)).astype(np.float32)
                timings["rf_disagreement_wall_seconds"] += time.perf_counter() - t0

                t0 = time.perf_counter()
                iso_score = (-isolation.score_samples(x)).astype(np.float32)
                timings["isolation_forest_wall_seconds"] += time.perf_counter() - t0
            finite = finite and all(np.isfinite(v).all()
                                    for v in (probability, confidence, disagreement, iso_score))
        return finite
    all_finite, inference_measure = timed(infer_sample)
    if not all_finite:
        raise RuntimeError("Target feature inference produced non-finite outputs")
    target_rows = int(ctx.target_record["row_count_excluding_header"])
    inference_total = sum(timings.values())
    code_paths = {
        "benchmark_script": ROOT / "scripts/benchmark_target_inference.py",
        "source_e1_runner": ROOT / "scripts/run_source_e1_complete.py",
        "target_transfer_common": ROOT / "scripts/target_transfer_common.py",
        "target_lockbox": ROOT / "src/ids_research/target_lockbox.py",
    }
    return {
        "report_id": f"target-inference-benchmark-{direction}-seed-{seed}-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "direction": direction, "seed": seed,
        "source_dataset_sha256": ctx.config["source_dataset"]["sha256"],
        "target_dataset_sha256": ctx.target_record["sha256"],
        "source_e1_metrics_sha256": model_meta["identity"]["source_e1_metrics_sha256"],
        "config_sha256": sha256_file(ctx.config_path),
        "stage_manifest_sha256": sha256_file(ctx.stage_manifest),
        "feature_registry_sha256": sha256_file(REPORTS / "transfer_feature_registry.csv"),
        "feature_order": list(ctx.feature_order),
        "target_sample": {"row_offsets": [0, query_rows - 1], "rows": query_rows,
                          "batch_rows": batch_rows, "feature_columns_only": True,
                          "parse_timing": parse_timing, "labels_selected_or_used": False},
        "model_cache": {"path": str((DATA / direction / "verified_models" / f"seed-{seed}").relative_to(ROOT)),
                        "verified_models": model_meta["model_sha256"],
                        "source_test_verification": model_meta["source_test_verification"],
                        "cache_reused": model_meta["cache_reused"],
                        "RF_fit_timing": model_meta.get("RF_fit_timing"),
                        "calibrator_fit_timing": model_meta.get("calibrator_fit_timing"),
                        "IsolationForest_fit_timing": model_meta.get("IsolationForest_fit_timing")},
        "target_inference": {
            "timing": timings,
            "overall_timing": inference_measure,
            "rows_per_second": {key.removesuffix("_wall_seconds"): query_rows / max(value, 1e-12)
                                for key, value in timings.items()},
            "combined_rows_per_second": query_rows / max(inference_total, 1e-12),
            "full_target_one_seed_seconds": {key.removesuffix("_wall_seconds"): value * target_rows / query_rows
                                              for key, value in timings.items()},
            "full_target_all_10_seeds_seconds": {key.removesuffix("_wall_seconds"): 10 * value * target_rows / query_rows
                                                 for key, value in timings.items()},
            "projection_formula": "bounded target feature inference wall time × (full target row count / bounded rows); all-seed projection multiplies one-seed estimate by ten",
        },
        "system_memory_before_run": memory_before,
        "system_memory_after_run": system_memory(),
        "logical_cpu_count": os.cpu_count(), "thread_limits": {"BLAS": THREADS,
                                                                   "OpenMP": THREADS,
                                                                   "RF_n_jobs": 1,
                                                                   "IsolationForest_n_jobs": 1},
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit_learn": sklearn.__version__, "joblib": joblib.__version__},
        "code_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "code_sha256": {name: sha256_file(path) for name, path in code_paths.items()},
        "all_finite": all_finite, "target_labels_read": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--direction", required=True, choices=sorted(DIRECTIONS))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--query-rows", type=int, default=40_000)
    parser.add_argument("--batch-rows", type=int, default=2048)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.query_rows < 1 or args.batch_rows < 1:
        raise SystemExit("query rows and batch rows must be positive")
    result = run_benchmark(args.direction, args.seed, args.query_rows, args.batch_rows)
    out = args.output or REPORTS / f"target_inference_benchmark_{args.direction.replace('-', '_')}_seed{args.seed}.json"
    if out.exists():
        raise SystemExit(f"Refusing to overwrite inference benchmark evidence: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "direction": args.direction, "seed": args.seed,
                      "source_test_exact_match": result["model_cache"]["source_test_verification"]["exact_match"],
                      "target_rows": result["target_sample"]["rows"],
                      "target_labels_read": False}, indent=2))


if __name__ == "__main__":
    main()
