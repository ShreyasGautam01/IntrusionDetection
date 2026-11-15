"""Manifest-gated, disk-backed scoring of the five transfer reliability signals."""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/nf_v3_audit"
DATA_ROOT = ROOT / "data/processed/target-transfer-v1"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_source_e1_cic import timed  # noqa: E402
from benchmark_target_distance import load_source_scaler  # noqa: E402
from benchmark_target_inference import fit_or_load_seed  # noqa: E402
from run_source_e1_direction import DIRECTIONS  # noqa: E402
from target_exact_knn import (  # noqa: E402
    benchmark_exact_case, compute_exact_target_distance, sha256_file,
)
from target_transfer_common import (  # noqa: E402
    FAMILY_MATRIX, FAMILY_REGISTRY, REGISTRY, parse_source_preprocessed_batch,
    resolve_direction, source_replacements, target_feature_batches,
)
from ids_research.target_lockbox import validate_both_transfer_manifests  # noqa: E402
from ids_research.transfer_scoring import reliability_score_batch  # noqa: E402

MANIFESTS = {
    "unsw-to-cic": REPORTS / "target_transfer_manifest_unsw_to_cic.json",
    "cic-to-unsw": REPORTS / "target_transfer_manifest_cic_to_unsw.json",
}
GATE_INTERPRETATIONS = {
    "unsw-to-cic": REPORTS / "SOURCE_E1_GATE_INTERPRETATION.md",
    "cic-to-unsw": REPORTS / "cic_source_e1_gate_interpretation.md",
}
THREAD_LIMIT = 1
DISTANCE_QUERY_BATCH_ROWS = 2048
SIGNALS = ("confidence", "random_forest_disagreement", "feature_space_distance",
           "split_conformal", "isolation_forest")
SCORE_FILES = ("calibrated_probability.npy", "confidence.npy",
               "random_forest_disagreement.npy", "split_conformal.npy",
               "isolation_forest.npy")


def event(message: str) -> None:
    print(f"{datetime.now(timezone.utc).isoformat()} {message}", flush=True)


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def lock_specs() -> dict[str, dict]:
    result = {}
    for direction in sorted(MANIFESTS):
        ctx = resolve_direction(direction)
        result[direction] = {
            "manifest_path": MANIFESTS[direction],
            "source_file": ctx.source_file,
            "target_file": ctx.target_file,
            "config_file": ctx.config_path,
            "source_stage_manifest": ctx.stage_manifest,
            "source_e1_manifest": ctx.source_e1_manifest,
            "source_e1_results": ctx.source_e1_results,
            "source_gate_interpretation": GATE_INTERPRETATIONS[direction],
            "feature_registry": REGISTRY,
            "family_registry": FAMILY_REGISTRY,
            "family_pair_matrix": FAMILY_MATRIX,
        }
    return result


def capacity_requirements(target_rows: int, seed_count: int, seed0_model_cache_bytes: int,
                          missing_model_cache_seeds: int, *, extra_headroom_bytes: int = 2_000_000_000,
                          model_cache_safety_factor: float = 1.25) -> dict:
    # target matrix + exact 5-NN two-slot distance/count states + result + five scores per seed
    bytes_per_row = 46 * 4 + 5 * (2 * 8 + 2 * 4) + 4 + len(SCORE_FILES) * 4 * seed_count
    estimated = target_rows * bytes_per_row
    model_reserve = math.ceil(seed0_model_cache_bytes * missing_model_cache_seeds
                              * model_cache_safety_factor)
    required = math.ceil(estimated * 1.2) + model_reserve + extra_headroom_bytes
    return {"estimated_bytes": estimated, "headroom_bytes": required,
            "model_cache_reserve_bytes": model_reserve,
            "model_cache_reference_bytes": seed0_model_cache_bytes,
            "model_cache_safety_factor": model_cache_safety_factor,
            "missing_model_cache_seeds": missing_model_cache_seeds,
            "extra_headroom_bytes": extra_headroom_bytes,
            "bytes_per_target_row": bytes_per_row}


def check_output_capacity(root: Path, target_rows: int, model_cache_root: Path,
                          seed_count: int = 10) -> dict:
    required_files = ("random_forest.joblib", "calibrator.joblib", "isolation_forest.joblib",
                      "verified_models.json")
    seed0_dir = model_cache_root / "seed-0"
    seed0_files = [seed0_dir / name for name in required_files]
    if not all(path.is_file() for path in seed0_files):
        raise RuntimeError(f"A complete verified seed-0 model cache is required for disk planning: {seed0_dir}")
    seed0_bytes = sum(path.stat().st_size for path in seed0_files)
    complete_cache_seeds = set()
    for seed in range(seed_count):
        seed_dir = model_cache_root / f"seed-{seed}"
        files = [seed_dir / name for name in required_files]
        present = [path.is_file() for path in files]
        if any(present) and not all(present):
            raise RuntimeError(f"Partial model cache blocks resource planning; preserving {seed_dir}")
        if all(present):
            complete_cache_seeds.add(seed)
    plan = capacity_requirements(
        target_rows, seed_count, seed0_bytes,
        seed_count - len(complete_cache_seeds),
    )
    disk = shutil.disk_usage(root)
    plan["available_bytes"] = disk.free
    if disk.free < plan["headroom_bytes"]:
        raise OSError(
            f"Insufficient output disk space: need at least {plan['headroom_bytes']} bytes "
            f"including 20% output headroom, {plan['model_cache_reserve_bytes']} bytes for "
            f"remaining model caches, and {plan['extra_headroom_bytes']} bytes extra; available {disk.free}"
        )
    return plan


def verify_source_stage_arrays(ctx) -> dict[str, str]:
    """Check every staged source array against the committed stage manifest once per direction run."""
    stage = json.loads(ctx.stage_manifest.read_text(encoding="utf-8"))
    verified = {}
    for name, metadata in stage["files"].items():
        path = ctx.data_dir / name
        if path.stat().st_size != int(metadata["bytes"]):
            raise ValueError(f"Source stage array byte count changed: {name}")
        actual = sha256_file(path)
        if actual != metadata["sha256"]:
            raise ValueError(f"Source stage array hash differs from its manifest: {name}")
        verified[name] = actual
    return verified


def stage_target_features(ctx, manifest_sha: str, batch_rows: int) -> tuple[np.ndarray, dict]:
    output = DATA_ROOT / ctx.direction / "target_features.npy"
    metadata_path = DATA_ROOT / ctx.direction / "target_features.json"
    partial = DATA_ROOT / ctx.direction / "target_features.partial.npy"
    checkpoint_path = DATA_ROOT / ctx.direction / "target_features.checkpoint.json"
    target_rows = int(ctx.target_record["row_count_excluding_header"])
    identity = {
        "direction": ctx.direction, "manifest_sha256": manifest_sha,
        "target_dataset_sha256": ctx.target_record["sha256"],
        "config_sha256": sha256_file(ctx.config_path),
        "feature_registry_sha256": sha256_file(REGISTRY),
        "feature_order": list(ctx.feature_order), "target_rows": target_rows,
        "dtype": "float32", "preprocessing": "source-fitted finite replacements only",
    }
    if output.exists() or metadata_path.exists():
        if not (output.exists() and metadata_path.exists()):
            raise RuntimeError("Target feature array/metadata pair is incomplete; preserving it")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if any(metadata.get(k) != v for k, v in identity.items()):
            raise ValueError("Existing target feature array belongs to a different frozen manifest")
        if metadata.get("array_sha256") != sha256_file(output):
            raise ValueError("Existing target feature array hash differs from its metadata")
        features = np.load(output, mmap_mode="r")
        if features.shape != (target_rows, 46) or features.dtype != np.float32:
            raise ValueError("Existing target feature array has an unexpected schema")
        return features, metadata
    if partial.exists() != checkpoint_path.exists():
        raise RuntimeError("Unpaired partial target features/checkpoint found; preserving both")
    output.parent.mkdir(parents=True, exist_ok=True)
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if any(checkpoint.get(k) != v for k, v in identity.items()):
            raise ValueError("Target feature staging checkpoint belongs to different inputs")
        completed = int(checkpoint.get("completed_rows", -1))
        if not 0 <= completed <= target_rows:
            raise ValueError("Target feature staging checkpoint row count is invalid")
        values = np.load(partial, mmap_mode="r+")
        if values.shape != (target_rows, 46) or values.dtype != np.float32:
            raise ValueError("Partial target feature array has an unexpected schema")
    else:
        completed = 0
        values = np.lib.format.open_memmap(partial, mode="w+", dtype=np.float32,
                                           shape=(target_rows, 46))
        atomic_json(checkpoint_path, {**identity, "completed_rows": 0,
                                      "created_utc": datetime.now(timezone.utc).isoformat()})
    replacements = source_replacements(ctx)
    last_checkpoint = completed
    for start, raw_rows in target_feature_batches(ctx, batch_size=batch_rows):
        end = start + len(raw_rows)
        if end <= completed:
            continue
        if start > completed:
            raise RuntimeError("Target feature input offsets skipped rows during resume")
        values_batch = parse_source_preprocessed_batch(raw_rows, ctx.feature_order, replacements)
        write_start = max(start, completed)
        values[write_start:end] = values_batch[write_start - start:]
        completed = end
        if completed - last_checkpoint >= 10 * batch_rows or completed == target_rows:
            values.flush()
            atomic_json(checkpoint_path, {**identity, "completed_rows": completed,
                                          "updated_utc": datetime.now(timezone.utc).isoformat()})
            event(f"{ctx.direction}: staged {completed}/{target_rows} feature rows")
            last_checkpoint = completed
    if completed != target_rows:
        raise RuntimeError(f"Target feature staging ended at {completed}/{target_rows}")
    values.flush(); del values
    os.replace(partial, output)
    metadata = {**identity, "completed": True, "array_sha256": sha256_file(output),
                "completed_utc": datetime.now(timezone.utc).isoformat(),
                "target_labels_read": False}
    atomic_json(metadata_path, metadata)
    checkpoint_path.unlink(missing_ok=True)
    return np.load(output, mmap_mode="r"), metadata


def compute_shared_distance(ctx, manifest_sha: str, target_features: np.ndarray,
                            feature_metadata: dict) -> tuple[np.ndarray, dict]:
    source_train_path = ctx.data_dir / "train_X.npy"
    source_train = np.load(source_train_path, mmap_mode="r")
    stage = json.loads(ctx.stage_manifest.read_text(encoding="utf-8"))
    if sha256_file(source_train_path) != stage["files"]["train_X.npy"]["sha256"]:
        raise ValueError("Source-train array hash differs from its frozen stage manifest")
    scaler, scaler_provenance = load_source_scaler(ctx, source_train)
    output_dir = DATA_ROOT / ctx.direction / "shared_distance"
    identity = {
        "direction": ctx.direction, "manifest_sha256": manifest_sha,
        "source_dataset_sha256": ctx.config["source_dataset"]["sha256"],
        "target_dataset_sha256": ctx.target_record["sha256"],
        "config_sha256": sha256_file(ctx.config_path),
        "source_stage_manifest_sha256": sha256_file(ctx.stage_manifest),
        "source_train_sha256": sha256_file(source_train_path),
        "target_feature_array_sha256": feature_metadata["array_sha256"],
        "feature_registry_sha256": sha256_file(REGISTRY),
        "feature_order": list(ctx.feature_order),
        "source_e1_distance_sha256": scaler_provenance["source_e1_distance_sha256"],
        "target_labels_read": False,
    }
    distance_meta = compute_exact_target_distance(
        source_train, target_features, scaler, output_dir, identity=identity,
        query_batch_rows=DISTANCE_QUERY_BATCH_ROWS,
    )
    distance_path = output_dir / "feature_space_distance.npy"
    distance = np.load(distance_path, mmap_mode="r")
    if distance.shape != (len(target_features),) or distance.dtype != np.float32:
        raise RuntimeError("Shared exact target distance has an invalid shape or dtype")
    for start in range(0, len(distance), 100_000):
        if not np.isfinite(distance[start:start + 100_000]).all():
            raise RuntimeError("Shared exact target distance contains non-finite values")
    if distance_meta.get("score_sha256") != sha256_file(distance_path):
        raise RuntimeError("Shared exact target distance hash does not match its metadata")
    return distance, distance_meta


def expected_seed_identity(ctx, seed: int, manifest_sha: str, feature_meta: dict,
                           distance_meta: dict) -> dict:
    source_metrics = ctx.source_e1_seed_root / f"seed-{seed}" / "metrics.json"
    if not source_metrics.is_file():
        raise FileNotFoundError(source_metrics)
    return {
        "direction": ctx.direction, "seed": seed, "manifest_sha256": manifest_sha,
        "source_e1_metrics_sha256": sha256_file(source_metrics),
        "target_feature_array_sha256": feature_meta["array_sha256"],
        "shared_distance_sha256": distance_meta["score_sha256"],
        "feature_order": list(ctx.feature_order),
    }


def seed_identity(ctx, seed: int, manifest_sha: str, feature_meta: dict,
                  distance_meta: dict, model_meta: dict) -> dict:
    identity = expected_seed_identity(ctx, seed, manifest_sha, feature_meta, distance_meta)
    if identity["source_e1_metrics_sha256"] != model_meta["identity"]["source_e1_metrics_sha256"]:
        raise ValueError("Verified model cache and current source E1 metrics differ")
    return identity


def summarize_array(path: Path, rows: int, batch_rows: int) -> dict:
    values = np.load(path, mmap_mode="r")
    if values.shape != (rows,) or values.dtype != np.float32:
        raise ValueError(f"Score array has an invalid schema: {path.name}")
    minimum, maximum, total = float("inf"), float("-inf"), 0.0
    finite_count = 0
    for start in range(0, rows, batch_rows):
        batch = np.asarray(values[start:min(start + batch_rows, rows)])
        if not np.isfinite(batch).all():
            raise ValueError(f"Score array contains non-finite values: {path.name}")
        minimum = min(minimum, float(batch.min()))
        maximum = max(maximum, float(batch.max()))
        total += float(batch.sum(dtype=np.float64))
        finite_count += len(batch)
    return {"shape": [rows], "dtype": "float32", "sha256": sha256_file(path),
            "finite_rows": finite_count, "minimum": minimum, "maximum": maximum,
            "mean": total / rows}


def verify_completed_seed(final_dir: Path, identity: dict, rows: int,
                          batch_rows: int) -> dict:
    metrics_path = final_dir / "metrics.json"
    if not metrics_path.is_file():
        raise FileNotFoundError(metrics_path)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    exact_source_check = metrics.get("source_test_verification", {}).get("exact_match", {})
    expected_source_outputs = {
        "prediction.npy", "calibrated_probability.npy",
        "random_forest_disagreement.npy", "isolation_forest.npy",
    }
    if (metrics.get("identity") != identity
            or metrics.get("target_labels_read") is not False
            or metrics.get("target_rows") != rows
            or metrics.get("signals") != list(SIGNALS)
            or set(exact_source_check) != expected_source_outputs
            or not all(exact_source_check.values())):
        raise ValueError("Completed transfer seed is bound to another lock or reports target-label access")
    scores = {}
    for name in SCORE_FILES:
        path = final_dir / name
        metadata = summarize_array(path, rows, batch_rows)
        if metrics.get("score_sha256", {}).get(name) != metadata["sha256"]:
            raise ValueError(f"Completed transfer seed score hash mismatch: {name}")
        scores[name] = metadata
    return {"metrics_sha256": sha256_file(metrics_path), "score_sha256":
            {name: item["sha256"] for name, item in scores.items()},
            "rows": rows, "target_labels_read": False}


def score_one_seed(ctx, seed: int, manifest_sha: str, target_features: np.ndarray,
                   feature_meta: dict, distance: np.ndarray, distance_meta: dict,
                   batch_rows: int) -> dict:
    model, calibrator, isolation, model_meta = fit_or_load_seed(ctx, seed, batch_rows)
    identity = seed_identity(ctx, seed, manifest_sha, feature_meta, distance_meta, model_meta)
    score_root = DATA_ROOT / ctx.direction / "scores"
    final_dir = score_root / f"seed-{seed}"
    partial_dir = score_root / f"seed-{seed}.partial"
    if final_dir.exists():
        return verify_completed_seed(final_dir, identity, len(target_features), batch_rows)
    score_root.mkdir(parents=True, exist_ok=True)
    partial_dir.mkdir(exist_ok=True)
    checkpoint_path = partial_dir / "checkpoint.json"
    output_paths = {name: partial_dir / name for name in SCORE_FILES}
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("identity") != identity:
            raise ValueError("Partial score checkpoint belongs to another direction/manifest/seed")
        completed = int(checkpoint.get("completed_rows", -1))
        if not 0 <= completed <= len(target_features):
            raise ValueError("Partial score checkpoint row count is invalid")
        if not all(path.exists() for path in output_paths.values()):
            raise RuntimeError("Partial score arrays are incomplete; preserving them")
        arrays = {name: np.load(path, mmap_mode="r+") for name, path in output_paths.items()}
    else:
        if any(path.exists() for path in output_paths.values()):
            raise RuntimeError("Partial score arrays exist without a checkpoint; preserving them")
        completed = 0
        arrays = {name: np.lib.format.open_memmap(
            path, mode="w+", dtype=np.float32, shape=(len(target_features),))
                  for name, path in output_paths.items()}
        atomic_json(checkpoint_path, {"identity": identity, "completed_rows": 0,
                                      "created_utc": datetime.now(timezone.utc).isoformat()})
    source_metrics = json.loads(
        (ctx.source_e1_seed_root / f"seed-{seed}" / "metrics.json").read_text(encoding="utf-8"))
    conformal_quantile = float(source_metrics["calibration"]["conformal_quantile"])
    last_checkpoint = completed
    last_log = completed

    def score_remaining() -> None:
        nonlocal completed, last_checkpoint, last_log
        for start in range(completed, len(target_features), batch_rows):
            end = min(start + batch_rows, len(target_features))
            features = np.asarray(target_features[start:end], dtype=np.float32)
            score_batch = reliability_score_batch(
                model, calibrator, isolation, features,
                conformal_quantile=conformal_quantile, thread_limit=THREAD_LIMIT,
            )
            for name in ("calibrated_probability.npy", "confidence.npy",
                         "random_forest_disagreement.npy", "split_conformal.npy",
                         "isolation_forest.npy"):
                arrays[name][start:end] = score_batch[name.removesuffix(".npy")]
            completed = end
            if completed - last_checkpoint >= 10 * batch_rows or completed == len(target_features):
                for array in arrays.values():
                    array.flush()
                atomic_json(checkpoint_path, {"identity": identity, "completed_rows": completed,
                                              "updated_utc": datetime.now(timezone.utc).isoformat()})
                last_checkpoint = completed
            if completed - last_log >= 500_000 or completed == len(target_features):
                event(f"{ctx.direction} seed {seed}: scored {completed}/{len(target_features)} target rows")
                last_log = completed

    _, timing = timed(score_remaining)
    for array in arrays.values():
        array.flush()
        # Windows refuses to rename the containing directory while any NPY
        # memory map is open. Explicitly close every mapping before promotion.
        array._mmap.close()
    del array
    arrays.clear()
    del arrays
    score_metadata = {name: summarize_array(path, len(target_features), batch_rows)
                      for name, path in output_paths.items()}
    metrics = {
        "report_id": f"target-transfer-scores-{ctx.direction}-seed-{seed}-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "identity": identity,
        "signal_definitions": ctx.config["reliability_signals"],
        "signals": list(SIGNALS),
        "target_rows": len(target_features), "feature_count": 46,
        "feature_order": list(ctx.feature_order), "score_sha256":
            {name: record["sha256"] for name, record in score_metadata.items()},
        "score_summaries": score_metadata,
        "shared_feature_space_distance_sha256": distance_meta["score_sha256"],
        "model_cache_sha256": model_meta["model_sha256"],
        "source_test_verification": model_meta["source_test_verification"],
        "scoring_timing": timing,
        "thread_limits": {"RF_n_jobs": 1, "IsolationForest_n_jobs": 1,
                          "BLAS": THREAD_LIMIT, "OpenMP": THREAD_LIMIT},
        "target_labels_read": False,
        "provenance": "target features only; source-fit preprocessing, calibration, and conformal quantile",
    }
    metrics_path = partial_dir / "metrics.json"
    atomic_json(metrics_path, metrics)
    checkpoint_path.unlink(missing_ok=True)
    os.replace(partial_dir, final_dir)
    return verify_completed_seed(final_dir, identity, len(target_features), batch_rows)


def progress_path(direction: str) -> Path:
    return REPORTS / f"target_transfer_progress_{direction.replace('-', '_')}.json"


def commit_seed_progress(path: Path, payload: dict, seed: int, direction: str) -> None:
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Tracked worktree must be clean before writing a seed progress checkpoint")
    atomic_json(path, payload)
    relative = path.relative_to(ROOT).as_posix()
    subprocess.run(["git", "-C", str(ROOT), "add", "--", relative], check=True)
    staged = subprocess.check_output(
        ["git", "-C", str(ROOT), "diff", "--cached", "--name-only"], text=True
    ).splitlines()
    if staged != [relative]:
        raise RuntimeError(f"Refusing to commit unrelated staged paths: {staged}")
    subprocess.run(["git", "-C", str(ROOT), "commit", "-m",
                    f"Checkpoint {direction} target seed {seed}"], check=True)


def run(direction: str, manifest_path: Path, batch_rows: int) -> None:
    if direction not in MANIFESTS or manifest_path.resolve() != MANIFESTS[direction].resolve():
        raise ValueError("Scoring direction and frozen manifest path do not match")
    specs = lock_specs()
    validated_locks = validate_both_transfer_manifests(specs, repository_root=ROOT)
    del validated_locks
    ctx = resolve_direction(direction)
    source_stage_hashes = verify_source_stage_arrays(ctx)
    manifest_sha = sha256_file(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if batch_rows < 1 or batch_rows > int(manifest["max_target_batch_rows"]):
        raise ValueError("Scoring batch size exceeds the bound frozen in the manifest")
    rows = int(ctx.target_record["row_count_excluding_header"])
    disk_need = check_output_capacity(
        ROOT, rows, DATA_ROOT / direction / "verified_models", seed_count=10)
    event(f"{direction}: locks validated; disk plan {disk_need['estimated_bytes']} bytes; staging target predictors")
    target_features, feature_meta = stage_target_features(ctx, manifest_sha, batch_rows)
    distance, distance_meta = compute_shared_distance(ctx, manifest_sha, target_features, feature_meta)
    expected_seeds = list(ctx.config["random_forest"]["seeds"])
    progress = progress_path(direction)
    both_manifest_hashes = {d: sha256_file(specs[d]["manifest_path"]) for d in specs}
    if progress.exists():
        state = json.loads(progress.read_text(encoding="utf-8"))
        if (state.get("direction") != direction
                or state.get("manifest_sha256") != manifest_sha
                or state.get("both_manifest_sha256") != both_manifest_hashes
                or state.get("target_feature_array_sha256") != feature_meta["array_sha256"]
                or state.get("shared_distance_sha256") != distance_meta["score_sha256"]
                or state.get("verified_source_stage_file_sha256") != source_stage_hashes
                or state.get("expected_seeds") != expected_seeds
                or state.get("target_labels_read") is not False):
            raise ValueError("Existing progress checkpoint belongs to another lock or changed inputs")
        completed = {int(record["seed"]): record for record in state.get("completed_seeds", [])}
    else:
        state = {"report_id": f"target-transfer-progress-{direction}-v1",
                 "direction": direction, "manifest_sha256": manifest_sha,
                 "both_manifest_sha256": both_manifest_hashes,
                 "disk_capacity_plan": disk_need,
                 "target_feature_array_sha256": feature_meta["array_sha256"],
                 "shared_distance_sha256": distance_meta["score_sha256"],
                 "verified_source_stage_file_sha256": source_stage_hashes,
                 "expected_seeds": expected_seeds, "completed_seeds": [],
                 "target_labels_read": False}
        completed = {}
    for seed in expected_seeds:
        expected_identity = expected_seed_identity(
            ctx, seed, manifest_sha, feature_meta, distance_meta)
        if seed in completed:
            final_dir = DATA_ROOT / direction / "scores" / f"seed-{seed}"
            identity = json.loads((final_dir / "metrics.json").read_text(encoding="utf-8"))["identity"]
            if identity != expected_identity:
                raise ValueError(f"Saved seed {seed} outputs belong to different transfer inputs")
            record = verify_completed_seed(final_dir, expected_identity, rows, batch_rows)
            if record["metrics_sha256"] != completed[seed]["metrics_sha256"]:
                raise ValueError(f"Saved seed {seed} progress hash no longer matches disk outputs")
            event(f"{direction} seed {seed}: already complete and hash-verified; skipping")
            continue
        final_dir = DATA_ROOT / direction / "scores" / f"seed-{seed}"
        if final_dir.exists():
            metrics = json.loads((final_dir / "metrics.json").read_text(encoding="utf-8"))
            if metrics.get("identity") != expected_identity:
                raise ValueError(f"Existing seed {seed} outputs belong to different transfer inputs")
            record = verify_completed_seed(final_dir, expected_identity, rows, batch_rows)
        else:
            event(f"{direction} seed {seed}: verified source model and scoring target rows")
            record = score_one_seed(ctx, seed, manifest_sha, target_features,
                                    feature_meta, distance, distance_meta, batch_rows)
        completed[seed] = {"seed": seed, **record}
        state["completed_seeds"] = [completed[s] for s in sorted(completed)]
        state["last_completed_seed"] = seed
        state["completed_utc"] = datetime.now(timezone.utc).isoformat()
        state["target_labels_read"] = False
        commit_seed_progress(progress, state, seed, direction)
        event(f"{direction} seed {seed}: checkpoint committed; target_labels_read=false")
    if sorted(completed) != sorted(expected_seeds):
        raise RuntimeError("Target score run did not complete the frozen seed set")
    event(f"{direction}: all target feature-only scores complete; labels remain sealed")


def run_smoke(direction: str, manifest_path: Path | None, batch_rows: int,
              smoke_rows: int, output_path: Path | None) -> None:
    if direction not in MANIFESTS or (manifest_path is not None
            and manifest_path.resolve() != MANIFESTS[direction].resolve()):
        raise ValueError("Smoke direction and frozen manifest path do not match")
    if manifest_path is not None:
        specs = lock_specs()
        validate_both_transfer_manifests(specs, repository_root=ROOT)
    ctx = resolve_direction(direction)
    verified_source_stage_hashes = verify_source_stage_arrays(ctx)
    manifest_sha = sha256_file(manifest_path) if manifest_path is not None else None
    if manifest_path is not None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        max_batch = int(manifest["max_target_batch_rows"])
    else:
        max_batch = 8192
    if batch_rows < 1 or batch_rows > max_batch:
        raise ValueError("Smoke batch size exceeds the configured bound")
    if smoke_rows < 1 or smoke_rows > 4096:
        raise ValueError("Smoke sample must be between one and 4,096 rows")
    model, calibrator, isolation, model_meta = fit_or_load_seed(ctx, 0, batch_rows)
    replacements = source_replacements(ctx)
    sample = None
    written = 0
    for _, raw_rows in target_feature_batches(ctx, batch_size=min(batch_rows, smoke_rows)):
        if sample is None:
            sample = np.empty((smoke_rows, 46), dtype=np.float32)
        values = parse_source_preprocessed_batch(raw_rows, ctx.feature_order, replacements)
        take = min(len(values), smoke_rows - written)
        sample[written:written + take] = values[:take]
        written += take
        if written == smoke_rows:
            break
    if written != smoke_rows or sample is None:
        raise ValueError(f"Target feature smoke produced {written}/{smoke_rows} rows")
    source_metrics = json.loads(
        (ctx.source_e1_seed_root / "seed-0" / "metrics.json").read_text(encoding="utf-8"))
    scores = reliability_score_batch(
        model, calibrator, isolation, sample,
        conformal_quantile=float(source_metrics["calibration"]["conformal_quantile"]),
        thread_limit=THREAD_LIMIT,
    )
    source_train = np.load(ctx.data_dir / "train_X.npy", mmap_mode="r")
    scaler, scaler_provenance = load_source_scaler(ctx, source_train)
    reference_rows = min(100_000, len(source_train))
    exact = benchmark_exact_case(
        source_train, sample, scaler, reference_rows=reference_rows,
        query_rows=smoke_rows, chunk_rows=500_000, query_batch_rows=min(256, batch_rows),
        return_scores=True,
    )
    scores["feature_space_distance"] = exact["scores"]
    if any(values.shape != (smoke_rows,) or not np.isfinite(values).all()
           for values in scores.values()):
        raise RuntimeError("Target five-signal smoke produced malformed/non-finite outputs")
    report = {
        "report_id": f"target-transfer-five-signal-smoke-{direction}-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "direction": direction, "manifest_sha256": manifest_sha,
        "source_dataset_sha256": ctx.config["source_dataset"]["sha256"],
        "target_dataset_sha256": ctx.target_record["sha256"],
        "config_sha256": sha256_file(ctx.config_path),
        "feature_registry_sha256": sha256_file(REGISTRY),
        "target_row_offsets": [0, smoke_rows - 1], "rows": smoke_rows,
        "feature_order": list(ctx.feature_order), "signals": list(SIGNALS),
        "signal_shapes": {name: list(value.shape) for name, value in scores.items()},
        "all_finite": True,
        "distance_reference_rows": reference_rows,
        "distance_benchmark": {k: v for k, v in exact.items() if k != "scores"},
        "source_scaler_provenance": scaler_provenance,
        "verified_source_stage_file_sha256": verified_source_stage_hashes,
        "source_e1_verification": model_meta["source_test_verification"],
        "target_labels_read": False,
        "manifest_status": "validated" if manifest_path is not None else "pre-freeze feature-only smoke",
        "code_commit": __import__("subprocess").check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "code_sha256": {
            "scripts/score_target_transfer.py": sha256_file(ROOT / "scripts/score_target_transfer.py"),
            "scripts/target_exact_knn.py": sha256_file(ROOT / "scripts/target_exact_knn.py"),
            "scripts/target_transfer_common.py": sha256_file(ROOT / "scripts/target_transfer_common.py"),
            "src/ids_research/transfer_scoring.py": sha256_file(ROOT / "src/ids_research/transfer_scoring.py"),
        },
        "selection": "first contiguous target feature rows; no target label or family columns selected",
    }
    out = output_path or REPORTS / f"target_transfer_smoke_{direction.replace('-', '_')}.json"
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite smoke evidence: {out}")
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    event(f"{direction}: five-signal target-feature smoke passed; target_labels_read=false")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--direction", required=True, choices=sorted(MANIFESTS))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--smoke-rows", type=int, default=256)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.smoke_only:
        run_smoke(args.direction, args.manifest, args.batch_size,
                  args.smoke_rows, args.output)
    else:
        if args.manifest is None:
            raise SystemExit("Full scoring requires the committed direction manifest")
        run(args.direction, args.manifest, args.batch_size)


if __name__ == "__main__":
    main()
