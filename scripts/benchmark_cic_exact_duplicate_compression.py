"""Bounded test of exact weighted duplicate compression for CIC 5-NN distance."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
import sklearn
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_source_e1_cic import CORES, process_memory, sha256, system_memory, timed

DATA = ROOT / "data/processed/source-e1-cic-lock-1"
WORK = DATA / "distance-bank-benchmark-v1"
CONFIG = ROOT / "reports/nf_v3_audit/source_e1_cic_config.json"
BANK_REPORT = ROOT / "reports/nf_v3_audit/cic_distance_bank_benchmark.json"
OUTPUT = ROOT / "reports/nf_v3_audit/cic_exact_duplicate_compression_benchmark.json"
BANK_SIZES = (100_000, 250_000, 500_000)
QUERY_ROWS = 1_024


def fit_scaler(train: np.ndarray) -> tuple[StandardScaler, dict]:
    scaler = StandardScaler(copy=True)

    def fit():
        for start in range(0, len(train), 100_000):
            scaler.partial_fit(train[start:min(start + 100_000, len(train))])
        return scaler

    with threadpool_limits(limits=1):
        _, timing = timed(fit)
    if not (np.isfinite(scaler.mean_).all() and np.isfinite(scaler.var_).all() and np.isfinite(scaler.scale_).all()):
        raise RuntimeError("Source-train scaler parameters are non-finite")
    timing["rows"] = len(train)
    timing["parameters_sha256"] = hashlib.sha256(
        b"".join(np.asarray(a, dtype="<f8").tobytes() for a in (scaler.mean_, scaler.var_, scaler.scale_))
    ).hexdigest()
    return scaler, timing


def weighted_five_nearest(distances: np.ndarray, indices: np.ndarray, multiplicity: np.ndarray) -> np.ndarray:
    counts = multiplicity[indices].astype(np.int64, copy=False)
    cumulative_before = np.cumsum(counts, axis=1, dtype=np.int64) - counts
    take = np.minimum(counts, np.maximum(5 - cumulative_before, 0))
    return np.sum(distances * take, axis=1, dtype=np.float64) / 5.0


def fit_query(reference: np.ndarray, queries: np.ndarray, n_neighbors: int = 5) -> tuple[np.ndarray, np.ndarray, dict, dict]:
    index = None

    def fit():
        nonlocal index
        index = NearestNeighbors(n_neighbors=n_neighbors, algorithm="kd_tree", leaf_size=30,
                                 metric="euclidean", n_jobs=1).fit(reference)
        return index

    with threadpool_limits(limits=1):
        _, fit_timing = timed(fit)
        (distances, indices), query_timing = timed(lambda: index.kneighbors(queries, return_distance=True))
    return distances, indices, fit_timing, query_timing


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite benchmark evidence: {OUTPUT}")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    source_manifest = json.loads((DATA / "stage_manifest.json").read_text(encoding="utf-8"))
    bank_report = json.loads(BANK_REPORT.read_text(encoding="utf-8"))
    if source_manifest["target_file_read"] or source_manifest["target_labels_read"]:
        raise RuntimeError("Source stage reports target access")
    train_path, query_path = DATA / "train_X.npy", DATA / "source_test_X.npy"
    train = np.load(train_path, mmap_mode="r")
    query = np.load(query_path, mmap_mode="r")
    if train.dtype != np.float32 or query.dtype != np.float32 or train.shape[1] != 46 or query.shape[1] != 46:
        raise RuntimeError("Unexpected staged feature schema")
    if sha256(train_path) != source_manifest["files"]["train_X.npy"]["sha256"]:
        raise RuntimeError("Source-train feature hash mismatch")
    if sha256(query_path) != source_manifest["files"]["source_test_X.npy"]["sha256"]:
        raise RuntimeError("Source-test feature hash mismatch")

    memory_before = system_memory()
    scaler, scaler_timing = fit_scaler(train)
    qidx = np.linspace(0, len(query) - 1, min(QUERY_ROWS, len(query)), dtype=np.int64)
    with threadpool_limits(limits=1):
        xq, query_transform = timed(lambda: scaler.transform(query[qidx]).astype(np.float64, copy=False))
    if not np.isfinite(xq).all():
        raise RuntimeError("Non-finite source-test queries after scaling")

    samples = {}
    results = {}
    max_peak = max(scaler_timing["peak_working_set_bytes"], query_transform["peak_working_set_bytes"])
    for k in BANK_SIZES:
        offsets_path = WORK / f"bank_offsets_k{k}.npy"
        offsets = np.load(offsets_path, allow_pickle=False)
        bank_meta = bank_report["bank_selection"]["banks"][str(k)]
        if len(offsets) != k or sha256(offsets_path) != bank_meta["file_sha256"]:
            raise RuntimeError(f"Deterministic feature bank hash mismatch for K={k}")

        def unique_sample():
            rows = np.asarray(train[offsets], dtype=np.float32)
            return np.unique(rows, axis=0, return_counts=True)

        (unique_rows, counts), unique_timing = timed(unique_sample)
        if int(np.sum(counts, dtype=np.int64)) != k:
            raise RuntimeError("Duplicate multiplicities do not sum to the sample size")
        unique_rows = np.ascontiguousarray(unique_rows, dtype=np.float32)
        row_hash = hashlib.sha256(unique_rows.tobytes()).hexdigest()
        count_hash = hashlib.sha256(np.asarray(counts, dtype="<u8").tobytes()).hexdigest()
        with threadpool_limits(limits=1):
            unique_z, unique_transform = timed(lambda: scaler.transform(unique_rows).astype(np.float64, copy=False))
        if not np.isfinite(unique_z).all():
            raise RuntimeError("Non-finite compressed reference rows")

        n_unique = len(unique_rows)
        n_neighbors = min(5, n_unique)
        distances, indices, fit_timing, query_timing = fit_query(unique_z, xq, n_neighbors=n_neighbors)
        weighted = weighted_five_nearest(distances, indices, counts)
        if not np.isfinite(weighted).all():
            raise RuntimeError("Compressed distance scores are non-finite")

        row = {
            "sample_rows": k, "unique_rows": n_unique,
            "unique_fraction": n_unique / k, "duplicate_row_fraction": 1 - n_unique / k,
            "sample_offsets_sha256": bank_meta["offsets_sha256"],
            "unique_rows_sha256": row_hash, "multiplicity_sha256": count_hash,
            "unique_extraction": unique_timing, "unique_scaling": unique_transform,
            "kd_tree_fit_unique_rows": fit_timing, "kd_tree_query_weighted_scores": query_timing,
            "weighted_query_rows_per_second": len(qidx) / query_timing["wall_seconds"],
            "projected_full_source_test_query_seconds": len(query) / (len(qidx) / query_timing["wall_seconds"]),
            "weighted_score_zero_count": int(np.count_nonzero(weighted == 0)),
            "weighted_score_p50": float(np.quantile(weighted, .50)),
            "weighted_score_p95": float(np.quantile(weighted, .95)),
        }
        results[str(k)] = row
        max_peak = max(max_peak, unique_timing["peak_working_set_bytes"],
                       unique_transform["peak_working_set_bytes"], fit_timing["peak_working_set_bytes"],
                       query_timing["peak_working_set_bytes"])

        if k == max(BANK_SIZES):
            sample = np.asarray(train[offsets], dtype=np.float32)
            with threadpool_limits(limits=1):
                sample_z, sample_transform = timed(lambda: scaler.transform(sample).astype(np.float64, copy=False))
            raw_distances, _, raw_fit, raw_query = fit_query(sample_z, xq, n_neighbors=5)
            raw_exact = raw_distances.mean(axis=1, dtype=np.float64)
            compressed_exact = weighted
            difference = np.abs(raw_exact - compressed_exact)
            equivalent = bool(np.allclose(raw_exact, compressed_exact, rtol=1e-12, atol=1e-12))
            row["bounded_equivalence_check"] = {
                "reference_rows": k, "unique_reference_rows": n_unique, "query_rows": len(qidx),
                "raw_exact_fit": raw_fit, "raw_exact_query": raw_query,
                "raw_reference_transform": sample_transform,
                "raw_score_sha256": hashlib.sha256(np.asarray(raw_exact, dtype="<f8").tobytes()).hexdigest(),
                "weighted_score_sha256": hashlib.sha256(np.asarray(compressed_exact, dtype="<f8").tobytes()).hexdigest(),
                "allclose_rtol_1e-12_atol_1e-12": equivalent,
                "maximum_absolute_difference": float(np.max(difference)),
                "exact_zero_count": int(np.count_nonzero(raw_exact == 0)),
                "weighted_zero_count": int(np.count_nonzero(compressed_exact == 0)),
                "scores_bitwise_equal": bool(np.array_equal(raw_exact, compressed_exact)),
            }
            if not equivalent:
                raise RuntimeError("Multiplicity-weighted compressed 5-NN differs from raw 5-NN")
            del sample_z, raw_distances

        del distances, indices, unique_rows, unique_z
        if k != max(BANK_SIZES):
            del counts

    peak = max(max_peak, process_memory())
    report = {
        "report_id": "cic-exact-duplicate-compression-bounded-benchmark-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
        "benchmark_script_sha256": sha256(Path(__file__)),
        "configuration_id": config["configuration_id"], "config_sha256": sha256(CONFIG),
        "stage_manifest_sha256": sha256(DATA / "stage_manifest.json"),
        "source_feature_hashes": {"train_X.npy": sha256(train_path), "source_test_X.npy": sha256(query_path)},
        "feature_order": config["features"]["columns"], "features": 46,
        "source_train_rows": len(train), "source_test_rows": len(query),
        "labels_read": False, "target_file_read": False, "target_labels_read": False,
        "definition": "Exact equivalence by collapsing bitwise-identical finite float32 source-train feature rows and retaining integer multiplicity. For each query, retrieve the five nearest distinct rows and expand each distance by its source multiplicity until five reference rows are represented; this equals the original all-row 5-NN mean whenever at least five distinct rows exist.",
        "implementation_note": "Scaler remains fitted on all original CIC source-train rows. Compression is applied to reference rows after the frozen finite-value preprocessing. No approximation is introduced; duplicated reference vectors are represented by exact integer counts.",
        "scaler_fit_all_source_train": scaler_timing,
        "query_sample": {"rows": len(qidx), "indices_sha256": hashlib.sha256(qidx.tobytes()).hexdigest(),
                         "transform": query_transform},
        "sample_results": results,
        "maximum_observed_timed_phase_peak_working_set_bytes": max_peak,
        "process_working_set_at_end_bytes": peak,
        "system_memory_before": memory_before, "system_memory_after": system_memory(),
        "logical_cpu_count": CORES, "thread_limits": {"BLAS": 1, "OpenMP": 1, "KDTree_n_jobs": 1},
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
        "scope_note": "Bounded feature-only benchmark on deterministic hash-priority subsets of the staged CIC source-train arrays. Full source unique-row count and full indexed run have not been measured. No final CIC manifest or E1 seed run is authorized by this benchmark alone.",
    }
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "unique_fraction": {k: v["unique_fraction"] for k, v in results.items()},
                      "equivalence": results["500000"]["bounded_equivalence_check"],
                      "maximum_peak_bytes": max_peak, "labels_read": False,
                      "target_file_read": False, "target_labels_read": False}, indent=2))


if __name__ == "__main__":
    main()
