"""Revalidate bounded CIC distance-bank scores without rerunning bank selection."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
import sklearn
from scipy.stats import spearmanr
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_source_e1_cic import CORES, process_memory, sha256, system_memory, timed

DATA = ROOT / "data/processed/source-e1-cic-lock-1"
WORK = DATA / "distance-bank-benchmark-v1"
INPUT = ROOT / "reports/nf_v3_audit/cic_distance_bank_benchmark.json"
OUTPUT = ROOT / "reports/nf_v3_audit/cic_distance_bank_benchmark_validation.json"
EXACT_REFERENCE_ROWS = 2_400_000
BANK_SIZES = (100_000, 250_000, 500_000)


def scaler_fit(train: np.ndarray) -> tuple[StandardScaler, dict]:
    scaler = StandardScaler(copy=True)

    def fit_all():
        for start in range(0, len(train), 100_000):
            scaler.partial_fit(train[start:min(start + 100_000, len(train))])
        return scaler

    with threadpool_limits(limits=1):
        _, timing = timed(fit_all)
    if not (np.isfinite(scaler.mean_).all() and np.isfinite(scaler.var_).all() and np.isfinite(scaler.scale_).all()):
        raise RuntimeError("Full-source scaler parameters are non-finite")
    scaler_hash = hashlib.sha256(
        b"".join(np.asarray(a, dtype="<f8").tobytes() for a in (scaler.mean_, scaler.var_, scaler.scale_))
    ).hexdigest()
    timing.update({"rows": len(train), "scaler_parameters_sha256": scaler_hash,
                   "parameter_order": ["mean_", "var_", "scale_"], "parameter_dtype": "little-endian float64"})
    return scaler, timing


def transform_rows(scaler: StandardScaler, source: np.ndarray, offsets: np.ndarray,
                   path: Path, block_rows: int = 20_000) -> tuple[np.memmap, dict]:
    out = np.lib.format.open_memmap(path, mode="w+", dtype=np.float64,
                                    shape=(len(offsets), source.shape[1]))

    def transform():
        for start in range(0, len(offsets), block_rows):
            end = min(start + block_rows, len(offsets))
            out[start:end] = scaler.transform(source[offsets[start:end].astype(np.int64)])
        out.flush()

    with threadpool_limits(limits=1):
        _, timing = timed(transform)
    out._mmap.close()
    mapped = np.load(path, mmap_mode="r")
    for start in range(0, len(mapped), block_rows):
        if not np.isfinite(mapped[start:start + block_rows]).all():
            mapped._mmap.close()
            raise RuntimeError("Non-finite standardized distance reference")
    return mapped, timing


def fit_score(reference: np.ndarray, queries: np.ndarray) -> tuple[np.ndarray, dict, dict]:
    index = None

    def fit():
        nonlocal index
        index = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30,
                                 metric="euclidean", n_jobs=1).fit(reference)
        return index

    with threadpool_limits(limits=1):
        _, fit_timing = timed(fit)
        distances, query_timing = timed(lambda: index.kneighbors(queries, return_distance=True)[0])
    scores = distances.mean(axis=1, dtype=np.float64)
    del distances, index
    if not np.isfinite(scores).all():
        raise RuntimeError("Distance scores are non-finite")
    return scores, fit_timing, query_timing


def score_summary(scores: np.ndarray) -> dict:
    return {"finite": bool(np.isfinite(scores).all()), "exact_zero_count": int(np.count_nonzero(scores == 0)),
            "min": float(np.min(scores)), "p50": float(np.quantile(scores, .50)),
            "p95": float(np.quantile(scores, .95)), "max": float(np.max(scores))}


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite validation evidence: {OUTPUT}")
    prior = json.loads(INPUT.read_text(encoding="utf-8"))
    stage = json.loads((DATA / "stage_manifest.json").read_text(encoding="utf-8"))
    for filename in ("train_X.npy", "source_test_X.npy"):
        meta = stage["files"][filename]
        path = DATA / filename
        if path.stat().st_size != meta["bytes"] or sha256(path) != meta["sha256"]:
            raise RuntimeError(f"Staged feature integrity mismatch: {filename}")
    if stage["target_file_read"] or stage["target_labels_read"]:
        raise RuntimeError("Source stage reports target data access")

    train = np.load(DATA / "train_X.npy", mmap_mode="r")
    query = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    if train.dtype != np.float32 or train.ndim != 2 or train.shape[1] != 46:
        raise RuntimeError("Unexpected CIC source-train feature schema")
    if query.dtype != np.float32 or query.ndim != 2 or query.shape[1] != 46:
        raise RuntimeError("Unexpected CIC source-test feature schema")
    qidx = np.linspace(0, len(query) - 1, min(4_096, len(query)), dtype=np.int64)
    expected_q_hash = hashlib.sha256(qidx.tobytes()).hexdigest()
    if expected_q_hash != prior["bounded_exact_baseline"]["query_indices_sha256"]:
        raise RuntimeError("Query sample differs from the original bounded benchmark")
    ridx = np.linspace(0, len(train) - 1, min(EXACT_REFERENCE_ROWS, len(train)), dtype=np.int64)
    expected_r_hash = hashlib.sha256(ridx.tobytes()).hexdigest()
    if expected_r_hash != prior["bounded_exact_baseline"]["reference_indices_sha256"]:
        raise RuntimeError("Exact reference sample differs from the original bounded benchmark")

    memory_before = system_memory()
    scaler, scaler_timing = scaler_fit(train)
    xq, query_transform_timing = timed(lambda: scaler.transform(query[qidx]).astype(np.float64, copy=False))
    if not np.isfinite(xq).all():
        raise RuntimeError("Non-finite standardized query rows")
    max_peak = max(scaler_timing["peak_working_set_bytes"], query_transform_timing["peak_working_set_bytes"])
    comparisons = {}
    with tempfile.TemporaryDirectory(prefix="cic-bank-revalidate-", dir=str(DATA)) as tmp:
        ref_path = Path(tmp) / "exact_reference.npy"
        exact_ref, exact_transform_timing = transform_rows(scaler, train, ridx, ref_path)
        exact, exact_fit, exact_query = fit_score(exact_ref, xq)
        exact_ref._mmap.close()
        del exact_ref
        exact_timing = {"reference_rows": len(ridx), "reference_indices_sha256": expected_r_hash,
                        "query_rows": len(qidx), "query_indices_sha256": expected_q_hash,
                        "reference_transform": exact_transform_timing, "index_fit": exact_fit,
                        "query": exact_query, "query_rows_per_second": len(qidx) / exact_query["wall_seconds"],
                        "score_summary": score_summary(exact),
                        "score_sha256": hashlib.sha256(np.asarray(exact, dtype="<f8").tobytes()).hexdigest()}
        max_peak = max(max_peak, exact_transform_timing["peak_working_set_bytes"],
                       exact_fit["peak_working_set_bytes"], exact_query["peak_working_set_bytes"])

        offsets_meta = {}
        for k in BANK_SIZES:
            offsets_path = WORK / f"bank_offsets_k{k}.npy"
            offsets = np.load(offsets_path, allow_pickle=False)
            expected_bank = prior["bank_selection"]["banks"][str(k)]
            offset_bytes = np.asarray(offsets, dtype=">u8").tobytes()
            offsets_hash = hashlib.sha256(offset_bytes).hexdigest()
            if len(offsets) != k or offsets_hash != expected_bank["offsets_sha256"]:
                raise RuntimeError(f"Candidate bank mismatch for K={k}")
            if sha256(offsets_path) != expected_bank["file_sha256"]:
                raise RuntimeError(f"Candidate bank file hash mismatch for K={k}")
            offsets_meta[str(k)] = {"rows": k, "offsets_sha256": offsets_hash,
                                    "file_sha256": sha256(offsets_path)}

        ref_path = Path(tmp) / "largest_bank.npy"
        bank_offsets = np.load(WORK / f"bank_offsets_k{max(BANK_SIZES)}.npy", allow_pickle=False)
        bank_ref, bank_transform_timing = transform_rows(scaler, train, bank_offsets, ref_path)
        max_peak = max(max_peak, bank_transform_timing["peak_working_set_bytes"])
        for k in BANK_SIZES:
            scores, fit_timing, query_timing = fit_score(bank_ref[:k], xq)
            difference = np.abs(scores - exact)
            median_exact = float(np.median(exact))
            normalized_abs = float(np.median(difference) / median_exact) if median_exact > 0 else None
            rank = float(spearmanr(exact, scores).statistic)
            repeat = None
            if k == max(BANK_SIZES):
                repeated, _, repeat_timing = fit_score(bank_ref[:k], xq)
                repeat = {"scores_bitwise_equal": bool(np.array_equal(scores, repeated)),
                          "first_sha256": hashlib.sha256(np.asarray(scores, dtype="<f8").tobytes()).hexdigest(),
                          "repeat_sha256": hashlib.sha256(np.asarray(repeated, dtype="<f8").tobytes()).hexdigest(),
                          "repeat_query": repeat_timing}
                if not repeat["scores_bitwise_equal"]:
                    raise RuntimeError("Repeated 500k bank scores differ")
            comparisons[str(k)] = {
                **offsets_meta[str(k)], "index_fit": fit_timing, "query": query_timing,
                "query_rows_per_second": len(qidx) / query_timing["wall_seconds"],
                "score_summary": score_summary(scores),
                "absolute_error_to_bounded_exact": {
                    "median": float(np.median(difference)), "p95": float(np.quantile(difference, .95)),
                    "mean": float(np.mean(difference)), "maximum": float(np.max(difference)),
                    "median_absolute_error_divided_by_exact_score_median": normalized_abs,
                    "scope_note": "Absolute errors remain defined when the exact score is zero. No per-row relative-error mean is used because zero and near-zero exact scores make it unstable."},
                "spearman_rank_correlation_to_bounded_exact": rank,
                "projected_full_source_test_query_seconds": len(query) / (len(qidx) / query_timing["wall_seconds"]),
                "projected_full_source_test_index_fit_plus_query_seconds": (
                    fit_timing["wall_seconds"] + len(query) / (len(qidx) / query_timing["wall_seconds"])
                ),
                "same_seed_independent_repeat": repeat,
            }
            max_peak = max(max_peak, fit_timing["peak_working_set_bytes"], query_timing["peak_working_set_bytes"])
        bank_ref._mmap.close()

    report = {
        "report_id": "cic-source-e1-distance-bank-benchmark-validation-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
        "prior_benchmark_report_sha256": sha256(INPUT),
        "prior_bank_selection_reused": True,
        "configuration_id": prior["configuration_id"], "config_sha256": prior["config_sha256"],
        "stage_manifest_sha256": prior["stage_manifest_sha256"], "source_sha256": prior["source_sha256"],
        "feature_hashes": prior["feature_hashes"], "feature_order": prior["feature_order"],
        "labels_read": False, "target_file_read": False, "target_labels_read": False,
        "definition": "All-source-train StandardScaler; bounded exact baseline uses 2.4M deterministic evenly spaced source-train references; bank candidates are deterministic hash-priority subsets; each score is mean Euclidean 5-NN distance in standardized 46-feature space.",
        "source_train_rows": len(train), "source_test_rows": len(query),
        "scaler_fit_all_source_train": scaler_timing,
        "scaler_parameter_sha256": scaler_timing["scaler_parameters_sha256"],
        "query_indices_sha256": expected_q_hash, "query_transform": query_transform_timing,
        "bounded_exact_baseline": exact_timing,
        "standardized_bank_transform_k500000": bank_transform_timing,
        "comparisons": comparisons,
        "maximum_observed_timed_phase_peak_working_set_bytes": max_peak,
        "system_memory_before": memory_before, "system_memory_after": system_memory(),
        "logical_cpu_count": CORES, "thread_limits": {"BLAS": 1, "OpenMP": 1, "KDTree_n_jobs": 1},
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
        "interpretation_note": "This validates only a bounded feature-only subset. It is not a comparison to the full 12.07M-reference exact signal, does not select a final K, and does not authorize a CIC E1 manifest or seed run. The first report's mean relative-error aggregation overflowed for zero/near-zero exact scores; this validation uses finite-checked scores, absolute error, and rank correlation instead.",
    }
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "scores_finite": True,
                      "exact_baseline": exact_timing["score_summary"],
                      "max_peak_bytes": max_peak,
                      "comparisons": {k: {"median_absolute_error": v["absolute_error_to_bounded_exact"]["median"],
                                           "p95_absolute_error": v["absolute_error_to_bounded_exact"]["p95"],
                                           "normalized_median_absolute_error": v["absolute_error_to_bounded_exact"]["median_absolute_error_divided_by_exact_score_median"],
                                           "spearman": v["spearman_rank_correlation_to_bounded_exact"],
                                           "query_rows_per_second": v["query_rows_per_second"]}
                                     for k, v in comparisons.items()},
                      "labels_read": False, "target_file_read": False, "target_labels_read": False}, indent=2))


if __name__ == "__main__":
    main()
