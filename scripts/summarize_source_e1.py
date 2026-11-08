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
                capture = float(misses[order[:n]].sum() / max(1, int(misses.sum())))
                key_values[f"{name}.capture_{budget}"] = capture
            stored = source_results["reliability"][name]
            if abs(key_values[f"{name}.attack_miss_auprc"] - float(stored["attack_miss_auprc"])) > 1e-12:
                ok = valid = False
        for k, v in key_values.items():
            metric_arrays.setdefault(k, []).append(float(v))
        per_seed[str(seed)] = {
            "integrity_verified": bool(ok),
            "file_hashes_match_metrics": bool(hash_match),
            "all_shapes_correct": all(checks.values()),
            "all_scores_finite": all(finite.values()),
            "target_access_reported": False,
            "fit_seconds": float(m["fit_seconds"]),
            "recovered_outputs": m.get("recovered_partial_artifacts"),
            "detector": detector,
            "signals": {name: source_results["reliability"][name] for name in SIGNALS},
            "artifact_sha256": hashes,
        }

    rank_agreement = {}
    top_set_stability = {}
    n = len(y)
    pair_ix = list(combinations(range(10), 2))
    for name, seed_scores in score_arrays.items():
        with threadpool_limits(limits=1):
            ranks = np.stack([rankdata(a, method="average") for a in seed_scores]).astype(np.float64, copy=False)
            corr = np.corrcoef(ranks)
        pair_corr = [float(corr[i, j]) for i, j in pair_ix]
        rank_agreement[name] = {**stats(pair_corr), "pair_count": len(pair_corr), "pairwise_spearman": pair_corr}
        budget_stability = {}
        for budget in (.01, .05, .10):
            k = max(1, int(np.ceil(n * budget)))
            selected = []
            for a in seed_scores:
                order = np.argsort(-a, kind="mergesort")
                mask = np.zeros(n, dtype=np.bool_)
                mask[order[:k]] = True
                selected.append(mask)
            jac = []
            for i, j in pair_ix:
                intersection = int(np.count_nonzero(selected[i] & selected[j]))
                jac.append(intersection / max(1, 2 * k - intersection))
            budget_stability[str(budget)] = {**stats(jac), "selected_rows": k, "interpretation": "Jaccard overlap of top review-budget rows across seeds; ties use stable source-test row order"}
        top_set_stability[name] = budget_stability

    summaries = {key: stats(values) for key, values in metric_arrays.items()}
    repeat_folder = RUNS / "repro" / "seed-0"
    repeat_metrics = json.loads((repeat_folder / "metrics.json").read_text(encoding="utf-8"))
    original_metrics = json.loads((RUNS / "seed-0" / "metrics.json").read_text(encoding="utf-8"))
    repeat_hashes = {}
    for filename in FILES.values():
        left, right = RUNS / "seed-0" / filename, repeat_folder / filename
        repeat_hashes[filename] = {"original_sha256": sha256(left), "repeat_sha256": sha256(right), "exact_match": sha256(left) == sha256(right)}
    repeat_exact = all(v["exact_match"] for v in repeat_hashes.values()) and original_metrics["source_test_results"] == repeat_metrics["source_test_results"]
    return {
        "report_id": "source-e1-final-results-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_id": "source-e1-lock-1",
        "manifest_sha256": sha256(REPORTS / "source_e1_manifest.json"),
        "source_dataset_sha256": "4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5",
        "source_test_rows": n,
        "source_test_attack_rows": miss_counts,
        "complete_seed_count": len(per_seed),
        "all_per_seed_outputs_integrity_verified": bool(valid),
        "same_seed_reproducibility": {"seed": 0, "exact_all_score_prediction_arrays_and_metrics": bool(repeat_exact), "per_array": repeat_hashes, "repeat_fit_seconds": repeat_metrics["fit_seconds"]},
        "per_seed": per_seed,
        "metric_summaries_median_iqr_min_max": summaries,
        "pairwise_rank_agreement": rank_agreement,
        "review_set_overlap": top_set_stability,
        "software": {"numpy": np.__version__, "scipy": scipy.__version__},
        "target_data_or_labels_accessed": False,
        "target_transfer_ready": False,
        "stability_interpretation_status": "Computed summaries; numeric acceptance tolerance is not defined by the frozen source config and requires explicit project-level interpretation before target evaluation.",
    }


def main() -> None:
    result = summarize()
    out = REPORTS / "source_e1_final_results.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out), "seeds": result["complete_seed_count"], "integrity": result["all_per_seed_outputs_integrity_verified"], "repeat_exact": result["same_seed_reproducibility"]["exact_all_score_prediction_arrays_and_metrics"], "target_transfer_ready": False}, indent=2))


if __name__ == "__main__":
    main()
