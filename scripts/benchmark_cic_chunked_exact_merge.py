"""Verify exact 5-NN merge across independently deduplicated CIC reference chunks."""
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
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_cic_exact_duplicate_compression import fit_query, fit_scaler
from benchmark_source_e1_cic import CORES, process_memory, sha256, system_memory, timed

DATA = ROOT / "data/processed/source-e1-cic-lock-1"
WORK = DATA / "distance-bank-benchmark-v1"
BANK_REPORT = ROOT / "reports/nf_v3_audit/cic_distance_bank_benchmark.json"
OUTPUT = ROOT / "reports/nf_v3_audit/cic_chunked_exact_merge_benchmark.json"
CHUNK_ROWS = 250_000
QUERY_ROWS = 1_024


def merge_top5(d1: np.ndarray, c1: np.ndarray, d2: np.ndarray, c2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    candidates_d = np.concatenate((d1, d2), axis=1)
    candidates_c = np.concatenate((c1, c2), axis=1)
    order = np.argsort(candidates_d, axis=1, kind="stable")[:, :5]
    best_d = np.take_along_axis(candidates_d, order, axis=1)
    best_c = np.take_along_axis(candidates_c, order, axis=1)
    return best_d, np.minimum(best_c, 5).astype(np.int32, copy=False)


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"Refusing to overwrite benchmark evidence: {OUTPUT}")
    report = json.loads(BANK_REPORT.read_text(encoding="utf-8"))
    train = np.load(DATA / "train_X.npy", mmap_mode="r")
    query = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    offsets = np.load(WORK / "bank_offsets_k500000.npy", allow_pickle=False)
    expected = report["bank_selection"]["banks"]["500000"]
    if len(offsets) != 500_000 or sha256(WORK / "bank_offsets_k500000.npy") != expected["file_sha256"]:
        raise RuntimeError("CIC bounded reference sample hash mismatch")
    qidx = np.linspace(0, len(query) - 1, min(QUERY_ROWS, len(query)), dtype=np.int64)

    memory_before = system_memory()
    scaler, scaler_timing = fit_scaler(train)
    with threadpool_limits(limits=1):
        xq, qtransform = timed(lambda: scaler.transform(query[qidx]).astype(np.float64, copy=False))
    chunk_results = []
    aggregate_d = aggregate_c = None
    max_peak = max(scaler_timing["peak_working_set_bytes"], qtransform["peak_working_set_bytes"])
    for chunk_id in range(2):
        chunk_offsets = offsets[chunk_id * CHUNK_ROWS:(chunk_id + 1) * CHUNK_ROWS]
        rows = np.asarray(train[chunk_offsets], dtype=np.float32)
        (unique_rows, counts), unique_timing = timed(lambda: np.unique(rows, axis=0, return_counts=True))
        unique_rows = np.ascontiguousarray(unique_rows, dtype=np.float32)
        with threadpool_limits(limits=1):
            unique_z, transform_timing = timed(lambda: scaler.transform(unique_rows).astype(np.float64, copy=False))
        distances, indices, fit_timing, query_timing = fit_query(unique_z, xq, n_neighbors=5)
        weighted_d = distances
        weighted_c = counts[indices].astype(np.int32, copy=False)
        if chunk_id == 0:
            aggregate_d, aggregate_c = weighted_d, weighted_c
            merge_timing = {"wall_seconds": 0.0, "process_cpu_seconds": 0.0, "peak_working_set_bytes": process_memory()}
        else:
            (aggregate_d, aggregate_c), merge_timing = timed(
                lambda: merge_top5(aggregate_d, aggregate_c, weighted_d, weighted_c))
        chunk_results.append({
            "chunk_id": chunk_id, "reference_rows": len(chunk_offsets), "unique_rows": len(unique_rows),
            "unique_fraction": len(unique_rows) / len(chunk_offsets),
            "sample_offsets_sha256": hashlib.sha256(np.asarray(chunk_offsets, dtype=">u8").tobytes()).hexdigest(),
            "unique_extraction": unique_timing, "standardize": transform_timing,
            "kd_tree_fit": fit_timing, "query": query_timing,
            "query_rows_per_second": len(qidx) / query_timing["wall_seconds"],
            "merge": merge_timing,
        })
        max_peak = max(max_peak, unique_timing["peak_working_set_bytes"], transform_timing["peak_working_set_bytes"],
                       fit_timing["peak_working_set_bytes"], query_timing["peak_working_set_bytes"],
                       merge_timing["peak_working_set_bytes"])
        del rows, unique_rows, counts, unique_z, distances, indices, weighted_d, weighted_c

    # Apply multiplicity weights to the already ordered five-candidate pool.
    prior = np.cumsum(aggregate_c, axis=1, dtype=np.int64) - aggregate_c
    take = np.minimum(aggregate_c, np.maximum(5 - prior, 0))
    aggregate = np.sum(aggregate_d * take, axis=1, dtype=np.float64) / 5.0

    sample = np.asarray(train[offsets], dtype=np.float32)
    with threadpool_limits(limits=1):
        sample_z, sample_transform = timed(lambda: scaler.transform(sample).astype(np.float64, copy=False))
    raw_distances, _, raw_fit, raw_query = fit_query(sample_z, xq, n_neighbors=5)
    raw_scores = raw_distances.mean(axis=1, dtype=np.float64)
    if not np.isfinite(aggregate).all() or not np.isfinite(raw_scores).all():
        raise RuntimeError("Non-finite exact or merged distance scores")
    difference = np.abs(raw_scores - aggregate)
    equivalent = bool(np.allclose(raw_scores, aggregate, rtol=1e-12, atol=1e-12))
    if not equivalent:
        raise RuntimeError("Chunk-merged distance scores differ from the raw 500k-reference exact baseline")

    report_out = {
        "report_id": "cic-chunked-exact-5nn-merge-benchmark-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
        "benchmark_script_sha256": sha256(Path(__file__)),
        "configuration_id": report["configuration_id"], "config_sha256": report["config_sha256"],
        "stage_manifest_sha256": report["stage_manifest_sha256"],
        "source_train_sha256": report["feature_hashes"]["train_X.npy"],
        "source_test_sha256": report["feature_hashes"]["source_test_X.npy"],
        "labels_read": False, "target_file_read": False, "target_labels_read": False,
        "definition": "Exact mean Euclidean 5-NN over all raw references, represented as per-chunk unique feature rows with exact integer multiplicities. For each chunk keep its five nearest distinct rows; merge distance/count candidates and retain the best five. No approximation is introduced.",
        "chunk_rows": CHUNK_ROWS, "chunks_benchmarked": 2,
        "query_rows": len(qidx), "query_indices_sha256": hashlib.sha256(qidx.tobytes()).hexdigest(),
        "scaler_fit_all_source_train": scaler_timing, "query_transform": qtransform,
        "chunks": chunk_results,
        "raw_exact_reference_check": {
            "reference_rows": len(offsets), "query_rows": len(qidx),
            "reference_fit": raw_fit, "reference_query": raw_query,
            "reference_transform": sample_transform,
            "exact_score_sha256": hashlib.sha256(np.asarray(raw_scores, dtype="<f8").tobytes()).hexdigest(),
            "chunk_merged_score_sha256": hashlib.sha256(np.asarray(aggregate, dtype="<f8").tobytes()).hexdigest(),
            "allclose_rtol_1e-12_atol_1e-12": equivalent,
            "scores_bitwise_equal": bool(np.array_equal(raw_scores, aggregate)),
            "maximum_absolute_difference": float(np.max(difference)),
            "exact_zero_count": int(np.count_nonzero(raw_scores == 0)),
            "merged_zero_count": int(np.count_nonzero(aggregate == 0)),
        },
        "max_timed_phase_peak_working_set_bytes": max_peak,
        "system_memory_before": memory_before, "system_memory_after": system_memory(),
        "logical_cpu_count": CORES, "thread_limits": {"BLAS": 1, "OpenMP": 1, "KDTree_n_jobs": 1},
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
        "full_distance_estimate": {
            "source_train_rows": len(train), "source_test_rows": len(query),
            "chunk_rows": CHUNK_ROWS, "chunks": int(np.ceil(len(train) / CHUNK_ROWS)),
            "query_seconds_per_full_chunk_at_500k_benchmark": report["comparisons"]["500000"]["projected_full_source_test_query_seconds"],
            "projected_query_seconds_for_all_chunks": int(np.ceil(len(train) / CHUNK_ROWS)) * report["comparisons"]["500000"]["projected_full_source_test_query_seconds"],
            "projected_query_hours_for_all_chunks": int(np.ceil(len(train) / CHUNK_ROWS)) * report["comparisons"]["500000"]["projected_full_source_test_query_seconds"] / 3600,
            "scope_note": "Projection uses the measured single 500k unique-reference query rate, multiplied by 25 independent 500k chunks. It excludes per-chunk dedup/fit and merge overhead; query rate may vary between chunks.",
        },
    }
    OUTPUT.write_text(json.dumps(report_out, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "equivalent": equivalent,
                      "maximum_absolute_difference": float(np.max(difference)),
                      "zero_count_exact_vs_chunked": [int(np.count_nonzero(raw_scores == 0)), int(np.count_nonzero(aggregate == 0))],
                      "full_query_estimate_hours": report_out["full_distance_estimate"]["projected_query_hours_for_all_chunks"],
                      "max_peak_bytes": max_peak}, indent=2))


if __name__ == "__main__":
    main()
