"""Evaluate completed transfer scores after both committed direction locks validate."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             roc_auc_score)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/nf_v3_audit"
DATA = ROOT / "data/processed/target-transfer-v1"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from score_target_transfer import (  # noqa: E402
    GATE_INTERPRETATIONS, MANIFESTS, SCORE_FILES, atomic_json, event,
    lock_specs, verify_completed_seed,
)
from target_exact_knn import sha256_file  # noqa: E402
from target_transfer_common import resolve_direction  # noqa: E402
from ids_research.review_ranking import ranked_binary_event_metrics  # noqa: E402
from ids_research.target_lockbox import (  # noqa: E402
    iter_final_evaluation_label_batches, validate_both_transfer_manifests,
)

SIGNALS = ("confidence", "random_forest_disagreement", "feature_space_distance",
           "split_conformal", "isolation_forest")
BUDGETS = (0.01, 0.05, 0.10)


def label_paths(direction: str) -> tuple[Path, Path, Path]:
    directory = DATA / direction / "evaluation"
    return (directory / "target_binary_labels.npy",
            directory / "target_binary_labels.json",
            directory / "target_binary_labels.partial.npy")


def load_or_stage_labels(direction: str, validated_locks, batch_rows: int) -> tuple[np.ndarray, dict]:
    specs = lock_specs()
    ctx = resolve_direction(direction)
    manifest_path = MANIFESTS[direction]
    manifest_sha = sha256_file(manifest_path)
    target_rows = int(ctx.target_record["row_count_excluding_header"])
    output, metadata_path, partial = label_paths(direction)
    checkpoint_path = partial.with_suffix(".checkpoint.json")
    identity = {
        "direction": direction, "target_dataset_sha256": ctx.target_record["sha256"],
        "manifest_sha256": manifest_sha,
        "both_manifest_sha256": dict(validated_locks.manifest_sha256),
        "target_rows": target_rows, "dtype": "int8",
        "mapping": "raw Label values parsed as binary 0/1 after both transfer manifests validate",
    }
    if output.exists() or metadata_path.exists():
        if not (output.exists() and metadata_path.exists()):
            raise RuntimeError("Target evaluation label array/metadata pair is incomplete")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if any(metadata.get(k) != v for k, v in identity.items()):
            raise ValueError("Cached target label array belongs to different manifests or dataset")
        if metadata.get("label_array_sha256") != sha256_file(output):
            raise ValueError("Cached target label array hash does not match its metadata")
        labels = np.load(output, mmap_mode="r")
        if labels.shape != (target_rows,) or labels.dtype != np.int8:
            raise ValueError("Cached target label array has an invalid shape or dtype")
        return labels, metadata
    if partial.exists() != checkpoint_path.exists():
        raise RuntimeError("Unpaired target label partial/checkpoint exists; preserving both")
    output.parent.mkdir(parents=True, exist_ok=True)
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if checkpoint.get("identity") != identity:
            raise ValueError("Target label staging checkpoint belongs to another lock")
        completed = int(checkpoint.get("completed_rows", -1))
        if not 0 <= completed <= target_rows:
            raise ValueError("Target label checkpoint row count is invalid")
        labels = np.load(partial, mmap_mode="r+")
        if labels.shape != (target_rows,) or labels.dtype != np.int8:
            raise ValueError("Target label partial array has an invalid shape or dtype")
    else:
        completed = 0
        labels = np.lib.format.open_memmap(partial, mode="w+", dtype=np.int8,
                                           shape=(target_rows,))
        atomic_json(checkpoint_path, {"identity": identity, "completed_rows": 0,
                                      "created_utc": datetime.now(timezone.utc).isoformat()})
    iterator = iter_final_evaluation_label_batches(
        ctx.target_file, manifest_path=manifest_path, repository_root=ROOT,
        direction=direction, source_file=ctx.source_file, config_file=ctx.config_path,
        source_stage_manifest=ctx.stage_manifest,
        source_e1_manifest=ctx.source_e1_manifest, source_e1_results=ctx.source_e1_results,
        source_gate_interpretation=GATE_INTERPRETATIONS[direction],
        feature_registry=specs[direction]["feature_registry"],
        family_registry=specs[direction]["family_registry"],
        family_pair_matrix=specs[direction]["family_pair_matrix"],
        validated_locks=validated_locks,
        expected_header=__import__("target_transfer_common").expected_raw_header(
            ctx.config["target"]["dataset"]),
        batch_size=batch_rows,
    )
    last_checkpoint = completed
    for start, batch in iterator:
        end = start + len(batch)
        if end <= completed:
            continue
        if start > completed:
            raise RuntimeError("Target label reader skipped rows while resuming")
        write_start = max(start, completed)
        for offset, (raw_label, _attack) in enumerate(batch[write_start - start:], start=write_start):
            try:
                label = int(raw_label.strip())
            except ValueError as exc:
                raise ValueError(f"Target binary label is not an integer at row {offset}") from exc
            if label not in (0, 1):
                raise ValueError(f"Target binary label is outside {{0,1}} at row {offset}")
            labels[offset] = label
        completed = end
        if completed - last_checkpoint >= 10 * batch_rows or completed == target_rows:
            labels.flush()
            atomic_json(checkpoint_path, {"identity": identity, "completed_rows": completed,
                                          "updated_utc": datetime.now(timezone.utc).isoformat()})
            event(f"{direction}: evaluation labels staged {completed}/{target_rows} after lock validation")
            last_checkpoint = completed
    if completed != target_rows:
        raise RuntimeError(f"Target label staging ended at {completed}/{target_rows}")
    labels.flush(); del labels
    os.replace(partial, output)
    metadata = {**identity, "completed": True,
                "label_array_sha256": sha256_file(output),
                "labels_read_after_both_manifests_validated": True,
                "validation_head_commit": validated_locks.head_commit,
                "completed_utc": datetime.now(timezone.utc).isoformat()}
    atomic_json(metadata_path, metadata)
    checkpoint_path.unlink(missing_ok=True)
    return np.load(output, mmap_mode="r"), metadata


def evaluate_seed(ctx, seed: int, labels: np.ndarray, batch_rows: int) -> dict:
    rows = len(labels)
    seed_dir = DATA / ctx.direction / "scores" / f"seed-{seed}"
    metrics_path = seed_dir / "metrics.json"
    if not metrics_path.is_file():
        raise FileNotFoundError(f"Target feature-only scores are incomplete for seed {seed}")
    score_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    exact_source = score_metrics.get("source_test_verification", {}).get("exact_match", {})
    if (score_metrics.get("target_labels_read") is not False
            or score_metrics.get("target_rows") != rows
            or not exact_source or not all(exact_source.values())):
        raise ValueError(f"Target score provenance is invalid for seed {seed}")
    if score_metrics.get("identity", {}).get("manifest_sha256") != sha256_file(MANIFESTS[ctx.direction]):
        raise ValueError(f"Target score seed {seed} belongs to another committed manifest")
    verify_completed_seed(seed_dir, score_metrics["identity"], rows, batch_rows)
    probability = np.load(seed_dir / "calibrated_probability.npy", mmap_mode="r")
    if probability.shape != (rows,) or not np.isfinite(probability).all():
        raise ValueError(f"Target probability output is invalid for seed {seed}")
    prediction = np.asarray(probability >= 0.5, dtype=np.uint8)
    actual = np.asarray(labels, dtype=np.uint8)
    errors = (prediction != actual).astype(np.uint8)
    misses = ((actual == 1) & (prediction == 0)).astype(np.uint8)
    if int(actual.sum()) == 0 or int(actual.sum()) == rows:
        auprc = None
        auroc = None
    else:
        auprc = float(average_precision_score(actual, probability))
        auroc = float(roc_auc_score(actual, probability))
    detector = {
        "row_count": rows,
        "attack_rows": int(actual.sum(dtype=np.int64)),
        "benign_rows": int(rows - actual.sum(dtype=np.int64)),
        "prediction_rows": int(prediction.sum(dtype=np.int64)),
        "accuracy": float(accuracy_score(actual, prediction)),
        "attack_auprc": auprc,
        "attack_auroc": auroc,
        "attack_miss_rows": int(misses.sum(dtype=np.int64)),
        "generic_error_rows": int(errors.sum(dtype=np.int64)),
        "brier_score": float(brier_score_loss(actual, probability)),
    }
    reliability = {}
    for signal in SIGNALS:
        if signal == "feature_space_distance":
            score_path = DATA / ctx.direction / "shared_distance" / "feature_space_distance.npy"
        else:
            score_path = seed_dir / f"{signal}.npy"
        score = np.load(score_path, mmap_mode="r")
        if score.shape != (rows,) or score.dtype != np.float32:
            raise ValueError(f"Target {signal} output has an invalid shape or dtype")
        for start in range(0, rows, batch_rows):
            if not np.isfinite(score[start:min(start + batch_rows, rows)]).all():
                raise ValueError(f"Target {signal} output contains non-finite values")
        reliability[signal] = ranked_binary_event_metrics(score, errors, misses, BUDGETS)
    return {
        "seed": seed,
        "source_e1_metrics_sha256": score_metrics["identity"]["source_e1_metrics_sha256"],
        "score_metrics_sha256": sha256_file(metrics_path),
        "detector": detector,
        "reliability": reliability,
        "target_labels_read_after_both_manifests_validated": True,
    }


def commit_evaluation(path: Path, direction: str) -> None:
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip():
        raise RuntimeError("Tracked worktree must be clean before committing evaluation results")
    relative = path.relative_to(ROOT).as_posix()
    subprocess.run(["git", "-C", str(ROOT), "add", "--", relative], check=True)
    staged = subprocess.check_output(
        ["git", "-C", str(ROOT), "diff", "--cached", "--name-only"], text=True
    ).splitlines()
    if staged != [relative]:
        raise RuntimeError(f"Refusing to commit unrelated staged paths: {staged}")
    subprocess.run(["git", "-C", str(ROOT), "commit", "-m",
                    f"Record {direction} transfer evaluation"], check=True)


def evaluate_direction(direction: str, batch_rows: int) -> dict:
    specs = lock_specs()
    validated_locks = validate_both_transfer_manifests(specs, repository_root=ROOT)
    ctx = resolve_direction(direction)
    labels, label_metadata = load_or_stage_labels(direction, validated_locks, batch_rows)
    seeds = list(ctx.config["random_forest"]["seeds"])
    seed_results = [evaluate_seed(ctx, seed, labels, batch_rows) for seed in seeds]
    report = {
        "report_id": f"target-transfer-evaluation-{direction}-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "direction": direction,
        "manifest_sha256": sha256_file(MANIFESTS[direction]),
        "both_manifest_sha256": dict(validated_locks.manifest_sha256),
        "target_label_array_sha256": label_metadata["label_array_sha256"],
        "source_dataset_sha256": ctx.config["source_dataset"]["sha256"],
        "target_dataset_sha256": ctx.target_record["sha256"],
        "feature_order": list(ctx.feature_order), "seeds": seeds,
        "review_budgets": list(BUDGETS),
        "budget_rule": "exact floor(budget × N); equal scores retain ascending input row offset; cutoff tie count reports all rows tied at cutoff",
        "family_scope": "binary endpoints only; target Attack strings were not used to infer cross-domain unseen families",
        "labels_read_after_both_manifests_validated": True,
        "label_validation_head_commit": label_metadata["validation_head_commit"],
        "target_labels_read": True,
        "per_seed": seed_results,
    }
    out = REPORTS / f"target_transfer_evaluation_{direction.replace('-', '_')}.json"
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite target evaluation summary: {out}")
    atomic_json(out, report)
    commit_evaluation(out, direction)
    event(f"{direction}: committed target-label evaluation summary")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--direction", choices=sorted(MANIFESTS), default=None)
    args = parser.parse_args()
    directions = [args.direction] if args.direction else sorted(MANIFESTS)
    for direction in directions:
        evaluate_direction(direction, args.batch_size)


if __name__ == "__main__":
    main()
