#!/usr/bin/env python3
"""
Complete post-transfer analysis for the frozen NF-UNSW/NF-CIC experiment.

This script is intentionally analysis-only:
- It never fits a detector.
- It never scores the transfer target.
- It never recalibrates.
- It never changes thresholds.
- It only evaluates completed transfer score arrays and target labels after
  validating the committed transfer manifests.

Run from D:\IntrusionDetection:

    .venv\Scripts\python.exe scripts\run_complete_transfer_analysis.py --resume

Optional:
    --phase <phase-name>
    --resume
    --no-plots

The script writes a resumable progress file and detailed log under
reports/nf_v3_audit/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "nf_v3_audit"
DATA = ROOT / "data" / "processed" / "target-transfer-v1"

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from score_target_transfer import GATE_INTERPRETATIONS, MANIFESTS, lock_specs  # noqa: E402
from target_exact_knn import sha256_file  # noqa: E402
from target_transfer_common import (  # noqa: E402
    FAMILY_MATRIX,
    FAMILY_REGISTRY,
    REGISTRY,
    expected_raw_header,
    resolve_direction,
)
from ids_research.target_lockbox import (  # noqa: E402
    iter_final_evaluation_label_batches,
    validate_both_transfer_manifests,
)

DIRECTIONS = ("unsw-to-cic", "cic-to-unsw")
SIGNALS = (
    "confidence",
    "random_forest_disagreement",
    "feature_space_distance",
    "split_conformal",
    "isolation_forest",
)
BUDGETS = (0.01, 0.05, 0.10)
SEEDS = tuple(range(10))
PRIMARY_METRICS = ("attack_miss_auprc", "capture_0.05")
PHASES = (
    "inventory",
    "primary_metrics",
    "paired_statistics",
    "direction_shift",
    "family_analysis",
    "generic_error",
    "selective_risk",
    "calibration_conformal",
    "compute_cost",
    "plots",
    "integrated_report",
    "integrity_audit",
    "experiment_decision",
)

PROGRESS_PATH = REPORTS / "analysis_master_progress.json"
LOG_PATH = REPORTS / "analysis_master.log"
PRIMARY_CSV = REPORTS / "analysis_per_seed_all_metrics.csv"
AGGREGATE_CSV = REPORTS / "analysis_aggregate.csv"
PAIRED_CSV = REPORTS / "analysis_paired_statistics.csv"
DIRECTION_CSV = REPORTS / "analysis_direction_shift.csv"
FAMILY_CSV = REPORTS / "analysis_family_results.csv"
GENERIC_CSV = REPORTS / "analysis_generic_error.csv"
SELECTIVE_CSV = REPORTS / "analysis_selective_results.csv"
CALIBRATION_CSV = REPORTS / "analysis_calibration_conformal.csv"
COMPUTE_MD = REPORTS / "analysis_computational_cost.md"
FINAL_REPORT = REPORTS / "FINAL_TRANSFER_ANALYSIS_REPORT.md"
FINAL_AUDIT = REPORTS / "FINAL_ANALYSIS_AUDIT.json"
NEXT_EXPERIMENT = REPORTS / "NEXT_EXPERIMENT_RECOMMENDATION.md"
FIG_DIR = REPORTS / "analysis_figures"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    line = f"{utc_now()} {message}\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="", flush=True)


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def sha256(path: Path) -> str:
    return sha256_file(path)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def progress_default() -> dict:
    return {
        "analysis_version": "v1",
        "created_utc": utc_now(),
        "started_utc": utc_now(),
        "current_phase": None,
        "completed_phases": [],
        "phase_outputs": {},
        "failed_phase": None,
        "failed_error": None,
        "target_labels_used_for_offline_evaluation_only": True,
        "scientific_transfer_rerun": False,
        "rf_fit_rerun": False,
        "distance_rerun": False,
    }


def load_progress() -> dict:
    if PROGRESS_PATH.is_file():
        return load_json(PROGRESS_PATH)
    state = progress_default()
    atomic_write_json(PROGRESS_PATH, state)
    return state


def mark_phase(state: dict, phase: str, outputs: list[Path]) -> None:
    hashes = {}
    for p in outputs:
        if p.is_file():
            hashes[p.relative_to(ROOT).as_posix()] = sha256(p)
    state["current_phase"] = None
    state["completed_phases"] = sorted(set(state["completed_phases"] + [phase]),
                                       key=PHASES.index)
    state["phase_outputs"][phase] = hashes
    state["failed_phase"] = None
    state["failed_error"] = None
    state["updated_utc"] = utc_now()
    atomic_write_json(PROGRESS_PATH, state)


def mark_failure(state: dict, phase: str, exc: Exception) -> None:
    state["current_phase"] = phase
    state["failed_phase"] = phase
    state["failed_error"] = repr(exc)
    state["updated_utc"] = utc_now()
    atomic_write_json(PROGRESS_PATH, state)


def evaluation_report(direction: str) -> Path:
    return REPORTS / f"target_transfer_evaluation_{direction.replace('-', '_')}.json"


def label_array(direction: str) -> Path:
    return DATA / direction / "evaluation" / "target_binary_labels.npy"


def score_path(direction: str, seed: int, signal: str) -> Path:
    if signal == "feature_space_distance":
        return DATA / direction / "shared_distance" / "feature_space_distance.npy"
    return DATA / direction / "scores" / f"seed-{seed}" / f"{signal}.npy"


def probability_path(direction: str, seed: int) -> Path:
    return DATA / direction / "scores" / f"seed-{seed}" / "calibrated_probability.npy"


def verify_evaluation_reports() -> dict[str, dict]:
    reports = {}
    for direction in DIRECTIONS:
        path = evaluation_report(direction)
        if not path.is_file():
            raise FileNotFoundError(
                f"Missing offline evaluation report: {path}\n"
                "Run the repository's existing evaluator first, or restore the committed local analysis artifacts."
            )
        report = load_json(path)
        if report.get("direction") != direction:
            raise ValueError(f"Evaluation direction mismatch in {path}")
        if not report.get("labels_read_after_both_manifests_validated", False):
            raise ValueError(f"Evaluation provenance does not prove lock validation before labels: {path}")
        if report.get("target_labels_read") is not True:
            raise ValueError(f"Evaluation report does not mark offline labels as read: {path}")
        if len(report.get("per_seed", [])) != 10:
            raise ValueError(f"Expected ten seed reports for {direction}")
        for seed_entry in report["per_seed"]:
            if seed_entry["seed"] not in SEEDS:
                raise ValueError(f"Unexpected seed in {direction}: {seed_entry['seed']}")
        reports[direction] = report
    return reports


def phase_inventory(reports: dict[str, dict]) -> list[Path]:
    log("PHASE inventory: verifying manifests, evaluation artifacts, labels, and score arrays")
    specs = lock_specs()
    validated = validate_both_transfer_manifests(specs, repository_root=ROOT)

    rows = []
    for direction in DIRECTIONS:
        ctx = resolve_direction(direction)
        labels_path = label_array(direction)
        if not labels_path.is_file():
            raise FileNotFoundError(labels_path)
        labels = np.load(labels_path, mmap_mode="r")
        target_rows = int(ctx.target_record["row_count_excluding_header"])
        if labels.shape != (target_rows,) or labels.dtype != np.int8:
            raise ValueError(f"Invalid target label array for {direction}")
        if sha256(labels_path) != reports[direction]["target_label_array_sha256"]:
            raise ValueError(f"Target label hash mismatch for {direction}")

        for seed in SEEDS:
            for signal in SIGNALS:
                path = score_path(direction, seed, signal)
                if not path.is_file():
                    raise FileNotFoundError(path)
                arr = np.load(path, mmap_mode="r")
                if arr.shape != (target_rows,) or arr.dtype != np.float32:
                    raise ValueError(f"Invalid score array: {path}")
                # Small chunked finiteness checks avoid a giant RAM copy.
                for start in range(0, target_rows, 1_000_000):
                    if not np.isfinite(arr[start:min(start + 1_000_000, target_rows)]).all():
                        raise ValueError(f"Non-finite score values: {path}")
                rows.append({
                    "direction": direction,
                    "seed": seed,
                    "signal": signal,
                    "rows": target_rows,
                    "score_sha256": sha256(path),
                })
        rows.append({
            "direction": direction,
            "seed": "all",
            "signal": "target_labels",
            "rows": target_rows,
            "score_sha256": sha256(labels_path),
        })

    out = REPORTS / "analysis_artifact_inventory.csv"
    save_csv(out, rows)
    meta = REPORTS / "analysis_lock_validation.json"
    atomic_write_json(meta, {
        "generated_utc": utc_now(),
        "validated_manifest_sha256": validated.manifest_sha256,
        "head_commit": validated.head_commit,
        "target_labels_used_only_for_offline_evaluation": True,
    })
    return [out, meta]


def phase_primary_metrics(reports: dict[str, dict]) -> list[Path]:
    log("PHASE primary_metrics: extracting canonical per-seed metrics from saved evaluation reports")
    rows = []
    for direction in DIRECTIONS:
        for seed_entry in reports[direction]["per_seed"]:
            seed = int(seed_entry["seed"])
            detector = seed_entry["detector"]
            for signal in SIGNALS:
                reliability = seed_entry["reliability"][signal]
                row = {
                    "direction": direction,
                    "seed": seed,
                    "signal": signal,
                    "attack_miss_auprc": reliability.get("attack_miss_auprc"),
                    "generic_error_auprc": reliability.get("generic_error_auprc"),
                    "capture_0.01": reliability["review_budgets"]["0.01"]["attack_miss_capture"],
                    "capture_0.05": reliability["review_budgets"]["0.05"]["attack_miss_capture"],
                    "capture_0.10": reliability["review_budgets"]["0.1"]["attack_miss_capture"],
                    "attack_miss_rows": reliability.get("attack_miss_rows"),
                    "detector_attack_auprc": detector.get("attack_auprc"),
                    "detector_attack_auroc": detector.get("attack_auroc"),
                    "detector_brier": detector.get("brier_score"),
                    "generic_error_rows": detector.get("generic_error_rows"),
                }
                rows.append(row)
    save_csv(PRIMARY_CSV, rows)

    aggregate = []
    for direction in DIRECTIONS:
        for signal in SIGNALS:
            subset = [
                r for r in rows if r["direction"] == direction and r["signal"] == signal
            ]
            for metric in ("attack_miss_auprc", "capture_0.01", "capture_0.05", "capture_0.10",
                           "generic_error_auprc"):
                vals = np.asarray(
                    [float(r[metric]) for r in subset if r[metric] is not None], dtype=float
                )
                aggregate.append({
                    "direction": direction,
                    "signal": signal,
                    "metric": metric,
                    "n": int(vals.size),
                    "mean": float(np.mean(vals)) if vals.size else None,
                    "median": float(np.median(vals)) if vals.size else None,
                    "sd": float(np.std(vals, ddof=1)) if vals.size > 1 else None,
                    "min": float(np.min(vals)) if vals.size else None,
                    "max": float(np.max(vals)) if vals.size else None,
                })
    save_csv(AGGREGATE_CSV, aggregate)
    return [PRIMARY_CSV, AGGREGATE_CSV]


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator,
                 reps: int = 20000, alpha: float = 0.05) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return (math.nan, math.nan)
    draws = rng.choice(values, size=(reps, values.size), replace=True)
    means = draws.mean(axis=1)
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def exact_sign_flip_p(diff: np.ndarray) -> float:
    diff = np.asarray(diff, dtype=float)
    diff = diff[np.isfinite(diff)]
    if diff.size == 0:
        return math.nan
    observed = abs(float(diff.mean()))
    extreme = 0
    total = 0
    for bits in itertools.product((-1.0, 1.0), repeat=diff.size):
        signed = diff * np.asarray(bits)
        if abs(float(signed.mean())) >= observed - 1e-15:
            extreme += 1
        total += 1
    return float(extreme / total)


def phase_paired_statistics(primary_rows: list[dict]) -> list[Path]:
    log("PHASE paired_statistics: exact paired seed comparisons and bootstrap intervals")
    rng = np.random.default_rng(20261117)
    rows = []
    for direction in DIRECTIONS:
        for metric in ("attack_miss_auprc", "capture_0.05"):
            by_signal = {
                signal: {
                    int(r["seed"]): r[metric]
                    for r in primary_rows
                    if r["direction"] == direction and r["signal"] == signal
                }
                for signal in SIGNALS
            }
            for a, b in itertools.combinations(SIGNALS, 2):
                common = sorted(set(by_signal[a]) & set(by_signal[b]))
                av = np.asarray([by_signal[a][s] for s in common], dtype=float)
                bv = np.asarray([by_signal[b][s] for s in common], dtype=float)
                diff = av - bv
                lo, hi = bootstrap_ci(diff, rng)
                rows.append({
                    "direction": direction,
                    "metric": metric,
                    "signal_a": a,
                    "signal_b": b,
                    "n": len(common),
                    "mean_difference_a_minus_b": float(np.mean(diff)),
                    "median_difference": float(np.median(diff)),
                    "bootstrap_ci_low": lo,
                    "bootstrap_ci_high": hi,
                    "exact_sign_flip_p_two_sided": exact_sign_flip_p(diff),
                })
    save_csv(PAIRED_CSV, rows)
    return [PAIRED_CSV]


def phase_direction_shift(primary_rows: list[dict]) -> list[Path]:
    log("PHASE direction_shift: direction-level robustness and semantic inversion diagnostics")
    rows = []
    for signal in SIGNALS:
        for metric in ("attack_miss_auprc", "capture_0.05"):
            summary = {}
            for direction in DIRECTIONS:
                vals = np.asarray([
                    r[metric] for r in primary_rows
                    if r["direction"] == direction and r["signal"] == signal and r[metric] is not None
                ], dtype=float)
                summary[direction] = vals
            u = summary[DIRECTIONS[0]]
            c = summary[DIRECTIONS[1]]
            umean = float(np.mean(u)) if u.size else math.nan
            cmean = float(np.mean(c)) if c.size else math.nan
            rows.append({
                "signal": signal,
                "metric": metric,
                "unsw_to_cic_mean": umean,
                "cic_to_unsw_mean": cmean,
                "absolute_direction_gap": abs(umean - cmean),
                "relative_direction_gap_to_unsw": (
                    abs(umean - cmean) / abs(umean) if np.isfinite(umean) and umean != 0 else math.nan
                ),
            })
    save_csv(DIRECTION_CSV, rows)
    return [DIRECTION_CSV]


def compute_shared_dos_mask(direction: str, validated_locks) -> Path:
    out = DATA / direction / "evaluation" / "target_shared_dos_mask.npy"
    meta = out.with_suffix(".json")
    if out.is_file() and meta.is_file():
        return out

    ctx = resolve_direction(direction)
    specs = lock_specs()
    rows_n = int(ctx.target_record["row_count_excluding_header"])
    mask = np.lib.format.open_memmap(out.with_suffix(".partial.npy"), mode="w+",
                                     dtype=np.bool_, shape=(rows_n,))
    iterator = iter_final_evaluation_label_batches(
        ctx.target_file,
        manifest_path=MANIFESTS[direction],
        repository_root=ROOT,
        direction=direction,
        source_file=ctx.source_file,
        config_file=ctx.config_path,
        source_stage_manifest=ctx.stage_manifest,
        source_e1_manifest=ctx.source_e1_manifest,
        source_e1_results=ctx.source_e1_results,
        source_gate_interpretation=GATE_INTERPRETATIONS[direction],
        feature_registry=specs[direction]["feature_registry"],
        family_registry=specs[direction]["family_registry"],
        family_pair_matrix=specs[direction]["family_pair_matrix"],
        validated_locks=validated_locks,
        expected_header=expected_raw_header(ctx.config["target"]["dataset"]),
        batch_size=8192,
    )
    completed = 0
    for start, batch in iterator:
        for i, (_label, attack) in enumerate(batch):
            value = (str(attack).strip() == "DoS")
            mask[start + i] = value
        completed = start + len(batch)
        if completed % 1_000_000 == 0:
            mask.flush()
            log(f"{direction}: shared-DoS family mask {completed}/{rows_n}")
    if completed != rows_n:
        raise RuntimeError(f"DoS family mask ended at {completed}/{rows_n}")
    mask.flush()
    del mask
    os.replace(out.with_suffix(".partial.npy"), out)
    atomic_write_json(meta, {
        "direction": direction,
        "family": "DoS",
        "basis": "documented_shared category only",
        "rows": rows_n,
        "mask_sha256": sha256(out),
        "generated_utc": utc_now(),
        "target_labels_used_after_manifest_validation": True,
    })
    return out


def phase_family_analysis() -> list[Path]:
    log("PHASE family_analysis: supported cross-domain family only (shared:DoS)")
    specs = lock_specs()
    validated = validate_both_transfer_manifests(specs, repository_root=ROOT)
    rows = []
    for direction in DIRECTIONS:
        mask_path = compute_shared_dos_mask(direction, validated)
        family_mask = np.load(mask_path, mmap_mode="r")
        labels = np.load(label_array(direction), mmap_mode="r")
        rows_n = len(labels)
        for seed in SEEDS:
            probability = np.load(probability_path(direction, seed), mmap_mode="r")
            actual = labels[family_mask]
            pred = probability[family_mask] >= 0.5
            misses = (actual == 1) & (~pred)
            if int(misses.sum()) == 0:
                detector_family_auprc = None
            else:
                detector_family_auprc = float(average_precision_score(actual, probability[family_mask]))
            for signal in SIGNALS:
                score = np.load(score_path(direction, seed, signal), mmap_mode="r")
                family_score = score[family_mask]
                value = float(average_precision_score(misses.astype(np.uint8), family_score)) \
                    if int(misses.sum()) else None
                rows.append({
                    "direction": direction,
                    "seed": seed,
                    "family": "DoS",
                    "mapping_status": "documented_shared",
                    "family_rows": int(family_mask.sum()),
                    "family_attack_rows": int(actual.sum()),
                    "family_attack_miss_rows": int(misses.sum()),
                    "signal": signal,
                    "attack_miss_auprc": value,
                    "detector_attack_auprc_within_family": detector_family_auprc,
                })
    save_csv(FAMILY_CSV, rows)
    note = REPORTS / "analysis_family_scope.md"
    note.write_text(
        "# Family-analysis scope\n\n"
        "The frozen cross-domain family registry supports a documented shared `DoS` category. "
        "Other target families were not reclassified as unseen because the registry explicitly "
        "withholds semantic equivalence where a documented crosswalk is unavailable or ambiguous. "
        "Therefore this analysis reports the supported shared DoS subset and does not make an "
        "unsupported unseen-family claim.\n",
        encoding="utf-8",
    )
    return [FAMILY_CSV, note]


def ece_score(prob: np.ndarray, labels: np.ndarray, bins: int = 15) -> float:
    prob = np.asarray(prob, dtype=float)
    labels = np.asarray(labels, dtype=np.uint8)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(prob)
    acc = 0.0
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        if i == bins - 1:
            mask = (prob >= lo) & (prob <= hi)
        else:
            mask = (prob >= lo) & (prob < hi)
        n = int(mask.sum())
        if not n:
            continue
        acc += (n / total) * abs(float(prob[mask].mean()) - float(labels[mask].mean()))
    return float(acc)


def find_conformal_quantile(seed: int, direction: str) -> float | None:
    model_dir = DATA / direction / "verified_models" / f"seed-{seed}"
    candidates = [model_dir / "verified_models.json"]
    for path in candidates:
        if not path.is_file():
            continue
        obj = load_json(path)

        def walk(x: Any) -> float | None:
            if isinstance(x, dict):
                for k, v in x.items():
                    kl = str(k).lower()
                    if "conformal" in kl and "quantile" in kl:
                        if isinstance(v, (int, float)) and np.isfinite(v):
                            return float(v)
                    found = walk(v)
                    if found is not None:
                        return found
            elif isinstance(x, list):
                for v in x:
                    found = walk(v)
                    if found is not None:
                        return found
            return None

        value = walk(obj)
        if value is not None and 0 <= value <= 1:
            return value
    return None


def phase_generic_error() -> list[Path]:
    log("PHASE generic_error: generic-error AUROC/AUPRC and attack-miss AUROC")
    generic_rows = []
    for direction in DIRECTIONS:
        labels = np.load(label_array(direction), mmap_mode="r")
        for seed in SEEDS:
            prob = np.load(probability_path(direction, seed), mmap_mode="r")
            actual = np.asarray(labels, dtype=np.uint8)
            prediction = (prob >= 0.5).astype(np.uint8)
            errors = (prediction != actual).astype(np.uint8)
            misses = ((actual == 1) & (prediction == 0)).astype(np.uint8)

            for signal in SIGNALS:
                score = np.load(score_path(direction, seed, signal), mmap_mode="r")
                ge_auprc = (
                    float(average_precision_score(errors, score))
                    if int(errors.sum())
                    else None
                )
                ge_auroc = (
                    float(roc_auc_score(errors, score))
                    if 0 < int(errors.sum()) < len(errors)
                    else None
                )
                miss_auroc = (
                    float(roc_auc_score(misses, score))
                    if 0 < int(misses.sum()) < len(misses)
                    else None
                )
                generic_rows.append({
                    "direction": direction,
                    "seed": seed,
                    "signal": signal,
                    "generic_error_auprc": ge_auprc,
                    "generic_error_auroc": ge_auroc,
                    "attack_miss_auroc": miss_auroc,
                    "attack_miss_prevalence": float(misses.mean()),
                    "semantic_inversion_flag_attack_miss_auroc_lt_0_5": (
                        bool(miss_auroc < 0.5) if miss_auroc is not None else None
                    ),
                    "generic_error_prevalence": float(errors.mean()),
                })
    save_csv(GENERIC_CSV, generic_rows)
    return [GENERIC_CSV]


def phase_calibration_conformal() -> list[Path]:
    log("PHASE calibration_conformal: target calibration and saved conformal diagnostics")
    rows = []
    for direction in DIRECTIONS:
        labels = np.load(label_array(direction), mmap_mode="r")
        for seed in SEEDS:
            prob = np.load(probability_path(direction, seed), mmap_mode="r")
            actual = np.asarray(labels, dtype=np.uint8)

            brier = float(brier_score_loss(actual, prob))
            ece = ece_score(prob, actual)

            conformal = np.load(score_path(direction, seed, "split_conformal"), mmap_mode="r")
            ambiguity_rate = float(np.mean(conformal))
            q = find_conformal_quantile(seed, direction)
            coverage = None
            mean_set_size = 1.0 + ambiguity_rate
            if q is not None:
                in_set_positive = (1.0 - prob) <= q
                in_set_negative = prob <= q
                covered = np.where(actual == 1, in_set_positive, in_set_negative)
                coverage = float(np.mean(covered))

            rows.append({
                "direction": direction,
                "seed": seed,
                "brier_score": brier,
                "ece_15bin": ece,
                "conformal_quantile": q,
                "target_ambiguity_rate": ambiguity_rate,
                "target_mean_prediction_set_size": mean_set_size,
                "target_empirical_coverage": coverage,
                "nominal_coverage": 0.90 if q is not None else None,
            })
    save_csv(CALIBRATION_CSV, rows)
    return [CALIBRATION_CSV]

def phase_selective_risk(primary_rows: list[dict], reports: dict[str, dict]) -> list[Path]:
    log("PHASE selective_risk: deriving residual-risk quantities from frozen review selections")
    rows = []
    for direction in DIRECTIONS:
        labels = np.load(label_array(direction), mmap_mode="r")
        n = len(labels)
        for seed_entry in reports[direction]["per_seed"]:
            seed = int(seed_entry["seed"])
            for signal in SIGNALS:
                selections = seed_entry["reliability"][signal]["review_budgets"]
                total_misses = int(seed_entry["reliability"][signal]["attack_miss_rows"])
                for budget_key, rec in selections.items():
                    selected = int(rec["selected_rows"])
                    captured = int(rec["attack_miss_rows_captured"])
                    remaining = total_misses - captured
                    unreviewed = n - selected
                    rows.append({
                        "direction": direction,
                        "seed": seed,
                        "signal": signal,
                        "review_budget": float(budget_key),
                        "reviewed_rows": selected,
                        "attack_miss_rows_total": total_misses,
                        "attack_miss_rows_captured": captured,
                        "attack_miss_capture": rec["attack_miss_capture"],
                        "residual_attack_miss_rows": remaining,
                        "residual_attack_miss_rate_over_all_rows": remaining / n if n else None,
                        "residual_attack_miss_rate_among_unreviewed": (
                            remaining / unreviewed if unreviewed else None
                        ),
                    })
    save_csv(SELECTIVE_CSV, rows)
    return [SELECTIVE_CSV]


def phase_compute_cost() -> list[Path]:
    log("PHASE compute_cost: recording already-established execution tradeoff")
    text = """# Computational-cost synthesis

## Production RF execution decision

The frozen scientific model remains unchanged. RF `n_jobs` was treated as an
execution parameter and benchmarked for deterministic equivalence.

Measured bounded CIC RF benchmark:

| n_jobs | Fit time | Min free RAM | Mean CPU | Peak CPU |
|---:|---:|---:|---:|---:|
| 10 | 17.64 s | 2.87 GB | 69.8% | 84.5% |
| 12 | 17.52 s | 3.14 GB | 83.3% | 97.9% |
| 14 | 17.24 s | 3.13 GB | 97.0% | 100% |
| 16 | 16.50 s | 2.71 GB | 97.6% | 100% |

All tested settings were exactly equivalent to the `n_jobs=1` reference on
tree structure, RF probabilities, and RF disagreement. `n_jobs=10` was selected
because higher values offered only marginal additional speed while materially
increasing system CPU saturation.

## Additional transfer computation

No new training, transfer scoring, or distance computation is performed by
this analysis pipeline. This report is therefore a synthesis of the already
completed computational experiment rather than a new benchmark.
"""
    COMPUTE_MD.write_text(text, encoding="utf-8")
    return [COMPUTE_MD]


def make_plot(path: Path, x_labels: list[str], values: list[float],
              title: str, ylabel: str) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x_labels, values)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def phase_plots(primary_rows: list[dict]) -> list[Path]:
    log("PHASE plots: generating compact paper-oriented figures")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []

    for direction in DIRECTIONS:
        values = []
        for signal in SIGNALS:
            vals = [
                r["attack_miss_auprc"] for r in primary_rows
                if r["direction"] == direction and r["signal"] == signal
            ]
            values.append(float(np.mean(vals)))
        path = FIG_DIR / f"attack_miss_auprc_{direction}.png"
        make_plot(path, list(SIGNALS), values,
                  f"Attack-miss AUPRC — {direction}", "Attack-miss AUPRC")
        outputs.append(path)

        values = []
        for signal in SIGNALS:
            vals = [
                r["capture_0.05"] for r in primary_rows
                if r["direction"] == direction and r["signal"] == signal
            ]
            values.append(float(np.mean(vals)))
        path = FIG_DIR / f"attack_miss_capture_5pct_{direction}.png"
        make_plot(path, list(SIGNALS), values,
                  f"Attack-miss capture at 5% review — {direction}", "Capture")
        outputs.append(path)

    # Direction asymmetry for the primary endpoint.
    direction_values = []
    labels = []
    for signal in SIGNALS:
        for direction in DIRECTIONS:
            vals = [
                r["attack_miss_auprc"] for r in primary_rows
                if r["direction"] == direction and r["signal"] == signal
            ]
            labels.append(f"{signal}\n{direction}")
            direction_values.append(float(np.mean(vals)))
    path = FIG_DIR / "direction_signal_attack_miss_auprc.png"
    make_plot(path, labels, direction_values,
              "Attack-miss AUPRC by direction and signal", "Attack-miss AUPRC")
    outputs.append(path)

    return outputs


def phase_integrated_report(primary_rows: list[dict]) -> list[Path]:
    log("PHASE integrated_report: assembling machine-readable and human-readable results")
    aggregate = load_csv(AGGREGATE_CSV)
    generic = load_csv(GENERIC_CSV)
    family = load_csv(FAMILY_CSV) if FAMILY_CSV.is_file() else []
    selective = load_csv(SELECTIVE_CSV)
    calibration = load_csv(CALIBRATION_CSV)

    lines = [
        "# Final Transfer Analysis Report",
        "",
        "## 1. Scope",
        "",
        "This report analyzes the completed source-only transfer artifacts for "
        "UNSW→CIC and CIC→UNSW across seeds 0–9. No RF fitting, target transfer "
        "scoring, or exact-distance computation is performed by this analysis stage.",
        "",
        "Target labels are used only for offline evaluation after the frozen transfer "
        "manifests are validated.",
        "",
        "## 2. Primary endpoint",
        "",
        "The primary endpoint is target attack-miss AUPRC. The primary operational "
        "endpoint is attack-miss capture at a 5% analyst-review budget.",
        "",
        "## 3. Primary results",
        "",
        "| Direction | Signal | Mean attack-miss AUPRC | Mean 5% capture |",
        "|---|---|---:|---:|",
    ]
    for direction in DIRECTIONS:
        for signal in SIGNALS:
            a = [r["attack_miss_auprc"] for r in primary_rows
                 if r["direction"] == direction and r["signal"] == signal]
            c = [r["capture_0.05"] for r in primary_rows
                 if r["direction"] == direction and r["signal"] == signal]
            lines.append(
                f"| {direction} | {signal} | {np.mean(a):.6f} | {np.mean(c):.6f} |"
            )

    lines += [
        "",
        "## 4. Seed variability",
        "",
        "All primary comparisons preserve the ten matched seeds. Paired analyses "
        "use exact sign-flip permutation testing and seed-level bootstrap intervals.",
        "",
        "See `analysis_paired_statistics.csv`.",
        "",
        "## 5. Directional robustness",
        "",
        "Direction-specific summaries are in `analysis_direction_shift.csv`. "
        "A score is flagged as semantically inverted only when its attack-miss AUROC "
        "falls below 0.5; performance is also interpreted relative to the attack-miss prevalence.",
        "",
        "## 6. Family analysis",
        "",
        "The frozen family registry supports a documented shared `DoS` category. "
        "Other cross-domain family equivalences are withheld where the registry lacks "
        "a defensible semantic crosswalk. Therefore this report does not claim unsupported "
        "unseen-family equivalence.",
        "",
        "See `analysis_family_results.csv`.",
        "",
        "## 7. Generic error versus attack-miss",
        "",
        "Generic error AUPRC and AUROC, plus attack-miss AUROC, are reported in "
        "`analysis_generic_error.csv`. This separates ordinary error detection from "
        "the security-critical false-negative task.",
        "",
        "## 8. Selective operational behavior",
        "",
        "Residual attack-miss rates at 1%, 5%, and 10% review are in "
        "`analysis_selective_results.csv`.",
        "",
        "## 9. Calibration and conformal diagnostics",
        "",
        "Target calibration diagnostics are reported descriptively from the frozen "
        "source-calibrated probability outputs. No target recalibration is performed. "
        "Conformal analysis reports target ambiguity/set-size behavior and empirical "
        "coverage only when the source conformal quantile can be recovered from the "
        "saved provenance metadata.",
        "",
        "## 10. Computational practicality",
        "",
        "See `analysis_computational_cost.md`. The established production execution "
        "setting is RF fit `n_jobs=10`.",
        "",
        "## 11. Limitations",
        "",
        "- Only ten repeated seeds are available.",
        "- The family registry intentionally withholds ambiguous semantic crosswalks.",
        "- Unsupported unseen-family claims are not inferred from dataset-local attack names.",
        "- Target labels are used only after source-only transfer scoring for evaluation.",
        "",
        "## 12. Main findings",
        "",
    ]

    for direction in DIRECTIONS:
        ranked = []
        for signal in SIGNALS:
            vals = [r["attack_miss_auprc"] for r in primary_rows
                    if r["direction"] == direction and r["signal"] == signal]
            ranked.append((signal, float(np.mean(vals))))
        ranked.sort(key=lambda x: x[1], reverse=True)
        lines.append(
            f"- **{direction}**: highest mean attack-miss AUPRC was "
            f"`{ranked[0][0]}` ({ranked[0][1]:.6f}); the remaining ranking should be "
            f"interpreted with the paired seed analysis rather than by mean alone."
        )

    lines += [
        "",
        "No claim of universal robustness or novelty is made from these descriptive "
        "results alone.",
        "",
    ]
    FINAL_REPORT.write_text("\n".join(lines), encoding="utf-8")
    return [FINAL_REPORT]


def load_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def phase_integrity_audit(reports: dict[str, dict]) -> list[Path]:
    log("PHASE integrity_audit: rechecking primary artifacts against checkpoints")
    issues = []

    for direction in DIRECTIONS:
        report = reports[direction]
        progress_path = REPORTS / f"target_transfer_progress_{direction.replace('-', '_')}.json"
        if not progress_path.is_file():
            issues.append(f"{direction}: missing transfer progress checkpoint")
            continue
        progress = load_json(progress_path)
        expected_by_seed = {int(e["seed"]): e for e in progress.get("completed_seeds", [])}

        expected_rows = int(resolve_direction(direction).target_record["row_count_excluding_header"])
        labels = np.load(label_array(direction), mmap_mode="r")
        if len(labels) != expected_rows:
            issues.append(f"{direction}: target label rows mismatch")
        if sha256(label_array(direction)) != report["target_label_array_sha256"]:
            issues.append(f"{direction}: target label hash mismatch")

        for seed_entry in report["per_seed"]:
            seed = int(seed_entry["seed"])
            metrics_path = DATA / direction / "scores" / f"seed-{seed}" / "metrics.json"
            if not metrics_path.is_file():
                issues.append(f"{direction} seed {seed}: missing metrics.json")
            else:
                actual_metrics_hash = sha256(metrics_path)
                if actual_metrics_hash != seed_entry["score_metrics_sha256"]:
                    issues.append(f"{direction} seed {seed}: metrics hash mismatch")
                metrics = load_json(metrics_path)
                if metrics.get("target_labels_read") is not False:
                    issues.append(f"{direction} seed {seed}: transfer metrics target-label firewall is not false")
                if metrics.get("target_rows") != expected_rows:
                    issues.append(f"{direction} seed {seed}: target row count mismatch")

            checkpoint = expected_by_seed.get(seed)
            if checkpoint is None:
                issues.append(f"{direction} seed {seed}: missing from transfer checkpoint")
            else:
                if checkpoint.get("target_labels_read") is not False:
                    issues.append(f"{direction} seed {seed}: checkpoint target-label firewall is not false")
                for signal_file in (
                    "calibrated_probability.npy",
                    "confidence.npy",
                    "random_forest_disagreement.npy",
                    "split_conformal.npy",
                    "isolation_forest.npy",
                ):
                    path = DATA / direction / "scores" / f"seed-{seed}" / signal_file
                    if not path.is_file():
                        issues.append(f"{direction} seed {seed}: missing {signal_file}")
                        continue
                    expected_hash = (checkpoint.get("score_sha256") or {}).get(signal_file)
                    if expected_hash and sha256(path) != expected_hash:
                        issues.append(f"{direction} seed {seed}: checkpoint hash mismatch for {signal_file}")

            for signal in SIGNALS:
                path = score_path(direction, seed, signal)
                if not path.is_file():
                    issues.append(str(path))
                else:
                    arr = np.load(path, mmap_mode="r")
                    if arr.shape != (expected_rows,) or arr.dtype != np.float32:
                        issues.append(f"invalid shape/dtype: {path}")

    audit = {
        "generated_utc": utc_now(),
        "issues": issues,
        "pass": not issues,
        "transfer_rerun": False,
        "target_labels_used_for_fitting": False,
        "target_labels_used_for_tuning": False,
        "target_labels_used_for_recalibration": False,
        "target_labels_used_for_score_construction": False,
        "all_primary_transfer_artifacts_checked": not issues,
    }
    atomic_write_json(FINAL_AUDIT, audit)
    if issues:
        raise RuntimeError("Integrity audit found issues: " + "; ".join(issues))
    return [FINAL_AUDIT]



def phase_experiment_decision(primary_rows: list[dict]) -> list[Path]:
    log("PHASE experiment_decision: evidence-based next-experiment recommendation")
    lines = [
        "# Next Experiment Recommendation",
        "",
        "## Current decision",
        "",
        "Do not automatically add another dataset, detector, target adaptation, or "
        "target recalibration experiment. The bidirectional RF transfer experiment is "
        "complete and should remain frozen.",
        "",
        "## What the completed analysis can establish",
        "",
        "The completed results directly evaluate whether the five lightweight reliability "
        "signals retain useful attack-miss prioritization across the two strict source-only "
        "domain-transfer directions.",
        "",
        "## Candidate targeted follow-up",
        "",
        "The pre-specified compact 8-feature sensitivity analysis remains the most defensible "
        "follow-up only if the 46-feature results suggest that the conclusions could be "
        "representation-sensitive. It should not be run merely because another experiment "
        "is available.",
        "",
        "Any future experiment must state the unresolved question first and must not use "
        "target labels for model fitting, tuning, threshold selection, or recalibration.",
        "",
        "## Family limitation",
        "",
        "The current family registry supports a documented shared DoS category but withholds "
        "unsupported semantic crosswalks. Therefore the present study should not claim a "
        "comprehensive unseen-attack-family result unless a separately justified frozen "
        "family mapping is established before any further target evaluation.",
        "",
    ]
    NEXT_EXPERIMENT.write_text("\n".join(lines), encoding="utf-8")
    return [NEXT_EXPERIMENT]


def run_phase(phase: str, state: dict, reports: dict[str, dict], primary_rows: list[dict]) -> list[Path]:
    if phase == "inventory":
        return phase_inventory(reports)
    if phase == "primary_metrics":
        return phase_primary_metrics(reports)
    if phase == "paired_statistics":
        return phase_paired_statistics(primary_rows)
    if phase == "direction_shift":
        return phase_direction_shift(primary_rows)
    if phase == "family_analysis":
        return phase_family_analysis()
    if phase == "generic_error":
        return phase_generic_error()
    if phase == "calibration_conformal":
        return phase_calibration_conformal()
    if phase == "selective_risk":
        return phase_selective_risk(primary_rows, reports)
    if phase == "compute_cost":
        return phase_compute_cost()
    if phase == "plots":
        if args_global.no_plots:
            marker = REPORTS / "analysis_figures_skipped.txt"
            marker.write_text("Plots skipped by --no-plots.\n", encoding="utf-8")
            return [marker]
        return phase_plots(primary_rows)
    if phase == "integrated_report":
        return phase_integrated_report(primary_rows)
    if phase == "integrity_audit":
        return phase_integrity_audit(reports)
    if phase == "experiment_decision":
        return phase_experiment_decision(primary_rows)
    raise ValueError(phase)


def main() -> None:
    global args_global
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--no-plots", action="store_true")
    args_global = parser.parse_args()

    state = load_progress()
    state["updated_utc"] = utc_now()
    atomic_write_json(PROGRESS_PATH, state)

    log("Starting complete transfer analysis")
    log("Scientific transfer rerun disabled; target labels restricted to offline evaluation")

    reports = verify_evaluation_reports()

    completed = set(state.get("completed_phases", [])) if args_global.resume else set()
    requested = [args_global.phase] if args_global.phase else list(PHASES)

    primary_rows = []
    if PRIMARY_CSV.is_file():
        primary_rows = load_csv(PRIMARY_CSV)
        for row in primary_rows:
            for key in ("seed",):
                row[key] = int(row[key])
            for key in ("attack_miss_auprc", "capture_0.01", "capture_0.05", "capture_0.10", "generic_error_auprc"):
                if row.get(key) in ("", None):
                    row[key] = None
                else:
                    row[key] = float(row[key])

    # If a phase depends on the primary table and it is absent, run primary first.
    dependency_order = {p: i for i, p in enumerate(PHASES)}
    expanded = []
    for p in requested:
        if p in ("paired_statistics", "direction_shift", "selective_risk", "plots",
                 "integrated_report", "experiment_decision"):
            for dep in ("primary_metrics",):
                if dep not in expanded and dep not in completed:
                    expanded.append(dep)
        if p == "integrated_report":
            for dep in ("generic_error", "calibration_conformal", "selective_risk",
                        "family_analysis", "compute_cost", "plots"):
                if dep not in expanded and dep not in completed:
                    expanded.append(dep)
        if p == "integrity_audit" and "inventory" not in completed and "inventory" not in expanded:
            expanded.append("inventory")
        if p not in expanded:
            expanded.append(p)

    # Respect global phase ordering.
    ordered = sorted(expanded, key=lambda x: dependency_order[x])

    for phase in ordered:
        if phase in completed and args_global.resume:
            log(f"Skipping already-completed phase: {phase}")
            continue
        state["current_phase"] = phase
        state["failed_phase"] = None
        state["failed_error"] = None
        atomic_write_json(PROGRESS_PATH, state)
        log(f"START phase={phase}")
        try:
            # Re-read primary rows after its creation.
            if phase != "primary_metrics" and PRIMARY_CSV.is_file():
                primary_rows = load_csv(PRIMARY_CSV)
                for row in primary_rows:
                    row["seed"] = int(row["seed"])
                    for key in ("attack_miss_auprc", "capture_0.01", "capture_0.05",
                                "capture_0.10", "generic_error_auprc"):
                        row[key] = float(row[key]) if row.get(key) not in ("", None) else None

            outputs = run_phase(phase, state, reports, primary_rows)
            mark_phase(state, phase, outputs)
            completed.add(phase)
            log(f"DONE phase={phase}")
        except Exception as exc:
            mark_failure(state, phase, exc)
            log(f"FAILED phase={phase}: {repr(exc)}")
            raise

    log("COMPLETE: requested analysis phases finished")


if __name__ == "__main__":
    main()
