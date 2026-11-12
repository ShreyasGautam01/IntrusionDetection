"""Bounded exact target-distance benchmark for the two core transfer directions."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
import joblib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/nf_v3_audit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_source_e1_cic import system_memory, timed  # noqa: E402
from run_source_e1_direction import DIRECTIONS  # noqa: E402
from target_exact_knn import (  # noqa: E402
    DEFAULT_REFERENCE_CHUNK_ROWS, benchmark_exact_case, scaler_parameter_hash,
)
from target_transfer_common import (  # noqa: E402
    REGISTRY, DirectionContext, parse_source_preprocessed_batch,
    resolve_direction, sha256_file, source_replacements, target_feature_batches,
)


def load_source_scaler(ctx: DirectionContext, source_train: np.ndarray) -> tuple[StandardScaler, dict]:
    distance_path = ctx.source_e1_seed_root / "common/feature_space_distance.json"
    distance = json.loads(distance_path.read_text(encoding="utf-8"))
    stage = json.loads(ctx.stage_manifest.read_text(encoding="utf-8"))
    if (distance.get("train_X_sha256") != stage["files"]["train_X.npy"]["sha256"]
            or distance.get("config_sha256") != sha256_file(ctx.config_path)
            or distance.get("neighbors") != 5
            or str(distance.get("metric", "")).lower() != "euclidean"):
        raise ValueError("Source E1 distance provenance does not match current source arrays/config")
    if ctx.direction == "cic-to-unsw":
        from cic_exact_chunked_5nn import fit_source_scaler
        cache_dir = ROOT / "data/processed/target-transfer-v1" / ctx.direction / "cache"
        cache_path = cache_dir / "source_distance_scaler.joblib"
        cache_meta_path = cache_dir / "source_distance_scaler.json"
        cache_identity = {
            "direction": ctx.direction,
            "configuration_id": ctx.config["configuration_id"],
            "config_sha256": sha256_file(ctx.config_path),
            "stage_manifest_sha256": sha256_file(ctx.stage_manifest),
            "train_X_sha256": sha256_file(ctx.data_dir / "train_X.npy"),
            "source_e1_distance_metadata_sha256": sha256_file(distance_path),
            "scaler_parameters_sha256": distance.get("scaler_parameters_sha256"),
            "software": {"python": platform.python_version(), "numpy": np.__version__,
                         "scikit_learn": sklearn.__version__, "joblib": joblib.__version__},
        }
        if cache_path.exists() and cache_meta_path.exists():
            cache_meta = json.loads(cache_meta_path.read_text(encoding="utf-8"))
            if any(cache_meta.get(k) != v for k, v in cache_identity.items()):
                raise ValueError("Cached CIC source scaler belongs to different frozen inputs")
            if cache_meta.get("scaler_cache_sha256") != sha256_file(cache_path):
                raise ValueError("Cached CIC source scaler file hash differs from its metadata")
            scaler = joblib.load(cache_path)
            if scaler_parameter_hash(scaler) != distance.get("scaler_parameters_sha256"):
                raise ValueError("Cached CIC source scaler differs from the exact E1 distance scaler")
            timing = cache_meta.get("fit_timing", {})
            cache_reused = True
        elif cache_path.exists() or cache_meta_path.exists() or (cache_dir / "source_distance_scaler.joblib.tmp").exists():
            raise RuntimeError("Partial CIC scaler cache exists; preserving it for inspection")
        else:
            scaler, timing = fit_source_scaler(source_train)
            if scaler_parameter_hash(scaler) != distance.get("scaler_parameters_sha256"):
                raise ValueError("Refitted CIC source scaler differs from the exact E1 distance scaler")
            cache_dir.mkdir(parents=True, exist_ok=True)
            temporary = cache_dir / "source_distance_scaler.joblib.tmp"
            joblib.dump(scaler, temporary, compress=0)
            os.replace(temporary, cache_path)
            cache_meta = {**cache_identity, "fit_timing": timing,
                          "scaler_cache_sha256": sha256_file(cache_path),
                          "created_utc": datetime.now(timezone.utc).isoformat()}
            cache_meta_path.write_text(json.dumps(cache_meta, indent=2) + "\n", encoding="utf-8")
            cache_reused = False
        provenance = {"method": "StandardScaler.partial_fit over source-train blocks",
                      "timing": timing, "cache_reused": cache_reused,
                      "source_e1_distance_metadata_sha256": sha256_file(distance_path),
                      "scaler_cache_sha256": sha256_file(cache_path)}
    else:
        scaler_path = ctx.source_e1_seed_root / "common/scaler.json"
        info = json.loads(scaler_path.read_text(encoding="utf-8"))
        expected_stage_sha = sha256_file(ctx.stage_manifest)
        expected_train_sha = stage["files"]["train_X.npy"]["sha256"]
        if (info.get("configuration_id") != ctx.config["configuration_id"]
                or info.get("config_sha256") != sha256_file(ctx.config_path)
                or info.get("stage_manifest_sha256") != expected_stage_sha
                or info.get("train_X_sha256") != expected_train_sha):
            raise ValueError("UNSW distance scaler provenance differs from its locked source train")
        mean = np.asarray(info["mean"], dtype=np.float64)
        scale = np.asarray(info["scale"], dtype=np.float64)
        mean_sha = hashlib.sha256(mean.tobytes()).hexdigest()
        scale_sha = hashlib.sha256(scale.tobytes()).hexdigest()
        if mean_sha != info.get("mean_sha256") or scale_sha != info.get("scale_sha256"):
            raise ValueError("Stored UNSW source scaler parameters fail their hashes")
        scaler = StandardScaler(copy=True)
        scaler.mean_, scaler.scale_, scaler.var_ = mean, scale, scale * scale
        scaler.n_features_in_ = len(mean)
        scaler.n_samples_seen_ = int(info["reference_rows"])
        provenance = {"method": "reuse exact source E1 StandardScaler parameters",
                      "parameters_sha256": scaler_parameter_hash(scaler),
                      "source_e1_scaler_json_sha256": sha256_file(scaler_path),
                      "source_e1_distance_metadata_sha256": sha256_file(distance_path)}
    return scaler, {**provenance, "source_e1_distance_sha256": distance.get("score_sha256")}


def sample_target_features(ctx: DirectionContext, n_rows: int, batch_size: int) -> tuple[np.ndarray, dict]:
    replacements = source_replacements(ctx)
    out = np.empty((n_rows, len(ctx.feature_order)), dtype=np.float32)
    written = 0

    def read_sample():
        nonlocal written
        for _, rows in target_feature_batches(ctx, batch_size=batch_size):
            values = parse_source_preprocessed_batch(rows, ctx.feature_order, replacements)
            take = min(len(values), n_rows - written)
            if take:
                out[written:written + take] = values[:take]
                written += take
            if written == n_rows:
                break
        if written != n_rows:
            raise ValueError(f"Target feature stream ended at {written} rows; expected {n_rows}")
        return out

    _, timing = timed(read_sample)
    return out, timing


def build_benchmark(ctx: DirectionContext, max_query_rows: int, batch_size: int) -> dict:
    memory_before = system_memory()
    target_path = ctx.target_file
    actual_target_hash, hash_timing = None, None

    def hash_target():
        nonlocal actual_target_hash
        actual_target_hash = sha256_file(target_path)
        return actual_target_hash

    _, hash_timing = timed(hash_target)
    if actual_target_hash != ctx.target_record["sha256"]:
        raise ValueError("Current target file bytes differ from the audited dataset hash")
    target_rows = int(ctx.target_record["row_count_excluding_header"])
    query_limit = min(max_query_rows, target_rows)
    queries, parse_timing = sample_target_features(ctx, query_limit, batch_size)
    source_train_path = ctx.data_dir / "train_X.npy"
    source_train = np.load(source_train_path, mmap_mode="r")
    stage = json.loads(ctx.stage_manifest.read_text(encoding="utf-8"))
    if sha256_file(source_train_path) != stage["files"]["train_X.npy"]["sha256"]:
        raise ValueError("Source train array hash differs from the frozen stage manifest")
    scaler, scaler_provenance = load_source_scaler(ctx, source_train)

    cases = []
    reference_query_pairs = [
        (100_000, min(2_500, query_limit)),
        (250_000, min(5_000, query_limit)),
        (500_000, min(10_000, query_limit)),
        (500_000, min(20_000, query_limit)),
        (1_000_000, query_limit),
    ]
    seen = set()
    for reference_rows, query_rows in reference_query_pairs:
        pair = (min(reference_rows, len(source_train)), query_rows)
        if pair in seen or query_rows < 1:
            continue
        seen.add(pair)
        result = benchmark_exact_case(
            source_train, queries, scaler,
            reference_rows=pair[0], query_rows=pair[1],
            chunk_rows=DEFAULT_REFERENCE_CHUNK_ROWS,
        )
        cases.append(result)
        gc.collect()

    full_reference_chunks = math.ceil(len(source_train) / DEFAULT_REFERENCE_CHUNK_ROWS)
    projections = []
    for result in cases:
        chunks_in_trial = result["reference_chunk_count"]
        per_chunk = result["wall_seconds"] / chunks_in_trial
        projected = per_chunk * (target_rows / result["query_rows"]) * full_reference_chunks
        projections.append(projected)
    projection = {"low_seconds": min(projections), "high_seconds": max(projections),
                  "full_source_reference_chunks": full_reference_chunks,
                  "target_query_rows": target_rows,
                  "formula": "measured per-reference-chunk wall time × (full target query rows / bounded query rows) × full source reference chunk count",
                  "scope": "exact distance computation only; target feature staging and model inference reported separately"}
    code_files = {
        "benchmark_script": ROOT / "scripts/benchmark_target_distance.py",
        "exact_distance_module": ROOT / "scripts/target_exact_knn.py",
        "target_transfer_common": ROOT / "scripts/target_transfer_common.py",
        "target_lockbox": ROOT / "src/ids_research/target_lockbox.py",
    }
    return {
        "report_id": f"target-exact-distance-benchmark-{ctx.direction}-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "direction": ctx.direction,
        "source_dataset": ctx.config["source_dataset"]["name"],
        "target_dataset": ctx.config["target"]["dataset"],
        "source_dataset_sha256": ctx.config["source_dataset"]["sha256"],
        "target_dataset_sha256": actual_target_hash,
        "target_rows": target_rows,
        "source_train_rows": int(len(source_train)),
        "source_train_sha256": stage["files"]["train_X.npy"]["sha256"],
        "source_stage_manifest_sha256": sha256_file(ctx.stage_manifest),
        "direction_config_sha256": sha256_file(ctx.config_path),
        "source_e1_distance_sha256": scaler_provenance["source_e1_distance_sha256"],
        "feature_registry_sha256": sha256_file(REGISTRY),
        "code_commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "code_sha256": {name: sha256_file(path) for name, path in code_files.items()},
        "feature_order": list(ctx.feature_order),
        "target_feature_sample": {"method": "first contiguous input rows; zero-based stable offsets",
                                  "row_offsets": [0, query_limit - 1], "rows": query_limit,
                                  "batch_size": batch_size, "labels_selected_or_used": False,
                                  "stream_timing": parse_timing},
        "target_file_byte_hash_timing": {**hash_timing, "labels_parsed_or_used": False},
        "distance_definition": "mean Euclidean distance to the five nearest original source-training rows after source-training StandardScaler",
        "implementation": "exact KDTree query over per-chunk unique source rows with integer duplicate multiplicities and exact top-five merge",
        "distance_parameters": {"neighbors": 5, "metric": "euclidean", "leaf_size": 30,
                                 "chunk_rows": DEFAULT_REFERENCE_CHUNK_ROWS, "query_batch_rows": 2048,
                                 "n_jobs": 1, "BLAS_threads": 1, "OpenMP_threads": 1,
                                 "scaler_provenance": scaler_provenance},
        "benchmark_trials": cases,
        "full_runtime_projection": projection,
        "hardware": {"logical_cpu_count": os.cpu_count(),
                     "system_memory_before_run": memory_before,
                     "system_memory_after_run": system_memory()},
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit_learn": sklearn.__version__},
        "target_labels_read": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--direction", required=True, choices=sorted(DIRECTIONS))
    parser.add_argument("--query-rows", type=int, default=40_000)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.query_rows < 1 or args.batch_size < 1:
        raise SystemExit("query rows and batch size must be positive")
    ctx = resolve_direction(args.direction)
    result = build_benchmark(ctx, args.query_rows, args.batch_size)
    output = args.output or REPORTS / f"target_exact_distance_benchmark_{args.direction.replace('-', '_')}.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "direction": args.direction,
                      "distance_trials": len(result["benchmark_trials"]),
                      "full_runtime_projection": result["full_runtime_projection"],
                      "target_labels_read": False}, indent=2))


if __name__ == "__main__":
    main()
