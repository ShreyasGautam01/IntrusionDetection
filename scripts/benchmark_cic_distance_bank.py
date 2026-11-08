"""Feature-only deterministic CIC distance-bank comparison against bounded exact 2.4M 5-NN."""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import os
import platform
import sys
import tempfile
import time
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
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from benchmark_source_e1_cic import CORES, process_memory, sha256, system_memory, timed

DATA = ROOT / "data/processed/source-e1-cic-lock-1"
CONFIG = ROOT / "reports/nf_v3_audit/source_e1_cic_config.json"
OUT = ROOT / "reports/nf_v3_audit/cic_distance_bank_benchmark.json"
WORK = DATA / "distance-bank-benchmark-v1"
DOMAIN = b"source-e1-cic-distance-bank-v1\x00"
BANK_SIZES = (100_000, 250_000, 500_000)
EXACT_REFERENCE_ROWS = 2_400_000
QUERY_ROWS = 4_096


def verify_feature_inputs() -> tuple[dict, dict]:
    stage_path = DATA / "stage_manifest.json"
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if sha256(CONFIG) != stage["configuration_sha256"]:
        raise RuntimeError("Source config hash differs from staged source manifest")
    if stage["configuration_id"] != cfg["configuration_id"]:
        raise RuntimeError("Stage/config identity mismatch")
    if stage["feature_order"] != cfg["features"]["columns"] or len(stage["feature_order"]) != 46:
        raise RuntimeError("Stage feature order differs from the 46-feature config")
    if stage["target_file_read"] or stage["target_labels_read"]:
        raise RuntimeError("Stage metadata reports target access")
    for filename in ("train_X.npy", "source_test_X.npy"):
        meta = stage["files"][filename]
        path = DATA / filename
        if path.stat().st_size != meta["bytes"] or sha256(path) != meta["sha256"]:
            raise RuntimeError(f"Feature array integrity mismatch: {filename}")
    train = np.load(DATA / "train_X.npy", mmap_mode="r")
    query = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    if train.shape != (stage["partition_rows"]["train"], 46) or query.shape != (stage["partition_rows"]["source_test"], 46):
        raise RuntimeError("Feature array shape mismatch")
    if train.dtype != np.float32 or query.dtype != np.float32:
        raise RuntimeError("Feature array dtype mismatch")
    for name, arr in (("train_X", train), ("source_test_X", query)):
        for start in range(0, len(arr), 100_000):
            if not np.isfinite(arr[start:start + 100_000]).all():
                raise RuntimeError(f"Non-finite values in {name}")
    return stage, cfg


def priority_pair(offset: int) -> tuple[int, int]:
    digest = hashlib.sha256(DOMAIN + int(offset).to_bytes(8, "big", signed=False)).digest()
    return int.from_bytes(digest, "big"), int(offset)


def select_hash_bank(row_count: int, bank_size: int) -> np.ndarray:
    """Return offsets with the lowest (SHA256 priority, offset) pairs, bounded in RAM."""
    heap: list[tuple[int, int]] = []
    for offset in range(row_count):
        digest_int = int.from_bytes(hashlib.sha256(DOMAIN + offset.to_bytes(8, "big", signed=False)).digest(), "big")
        entry = (-digest_int, -offset)
        if len(heap) < bank_size:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)
        if (offset + 1) % 1_000_000 == 0:
            print(f"bank selection scanned {offset+1:,}/{row_count:,} source-train offsets", flush=True)
    selected = sorted((-neg_digest, -neg_offset) for neg_digest, neg_offset in heap)
    return np.fromiter((offset for _, offset in selected), dtype=np.uint64, count=bank_size)


def offsets_sha256(offsets: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(offsets, dtype=">u8").tobytes()).hexdigest()


def score_sha256(scores: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(scores, dtype="<f8").tobytes()).hexdigest()


def scaler_full_train(train: np.ndarray) -> tuple[StandardScaler, dict]:
    scaler = StandardScaler(copy=True)
    def fit_all():
        for start in range(0, len(train), 100_000):
            scaler.partial_fit(train[start:min(start + 100_000, len(train))])
        return scaler
    with threadpool_limits(limits=1):
        _, timing = timed(fit_all)
    if not (np.isfinite(scaler.mean_).all() and np.isfinite(scaler.var_).all() and np.isfinite(scaler.scale_).all()):
        raise RuntimeError("Full-source scaler parameters are non-finite")
    timing["scaler_parameters_sha256"] = hashlib.sha256(
        b"".join(np.asarray(a, dtype="<f8").tobytes() for a in (scaler.mean_, scaler.var_, scaler.scale_))
    ).hexdigest()
    timing.update({"rows": len(train), "block_rows": 100_000,
                   "definition": "StandardScaler statistics over every CIC source-train feature row; partial_fit blocks"})
    return scaler, timing


def transform_reference(scaler: StandardScaler, train: np.ndarray, offsets: np.ndarray, path: Path) -> tuple[np.memmap, dict]:
    out = np.lib.format.open_memmap(path, mode="w+", dtype=np.float64, shape=(len(offsets), train.shape[1]))
    def transform():
        for start in range(0, len(offsets), 20_000):
            end = min(start + 20_000, len(offsets))
            out[start:end] = scaler.transform(train[offsets[start:end].astype(np.int64)])
        out.flush()
    with threadpool_limits(limits=1):
        _, timing = timed(transform)
    out._mmap.close()
    mapped = np.load(path, mmap_mode="r")
    return mapped, timing


def exact_scores(scaler: StandardScaler, train: np.ndarray, query: np.ndarray, qidx: np.ndarray, workdir: Path) -> tuple[np.ndarray, dict]:
    nref = min(EXACT_REFERENCE_ROWS, len(train))
    ridx = np.linspace(0, len(train) - 1, nref, dtype=np.int64)
    xq, qtransform = timed(lambda: scaler.transform(query[qidx]).astype(np.float64, copy=False))
    with tempfile.TemporaryDirectory(prefix="cic-bank-exact-", dir=str(DATA)) as temp:
        ref_path = Path(temp) / "exact_reference.npy"
        ref, reftransform = transform_reference(scaler, train, ridx.astype(np.uint64), ref_path)
        index = None
        def fit():
            nonlocal index
            index = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30, metric="euclidean", n_jobs=1).fit(ref)
            return index
        _, fit_timing = timed(fit)
        with threadpool_limits(limits=1):
            distances, query_timing = timed(lambda: index.kneighbors(xq, return_distance=True)[0])
        scores = distances.mean(axis=1, dtype=np.float64)
        if not np.isfinite(scores).all():
            raise RuntimeError("Bounded exact distance scores are non-finite")
        result = {"reference_rows": nref,
                  "reference_indices_sha256": hashlib.sha256(ridx.tobytes()).hexdigest(),
                  "query_rows": len(qidx),
                  "query_indices_sha256": hashlib.sha256(qidx.tobytes()).hexdigest(),
                  "reference_transform": reftransform, "query_transform": qtransform,
                  "index_fit": fit_timing, "query": query_timing,
                  "query_rows_per_second": len(qidx) / query_timing["wall_seconds"],
                  "score_sha256": score_sha256(scores)}
        del distances, index
        ref._mmap.close()
    del xq
    return scores, result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite benchmark evidence: {args.output}")
    if WORK.exists():
        raise SystemExit(f"Refusing to overwrite local bank candidate directory: {WORK}")
    stage, cfg = verify_feature_inputs()
    if len(np.load(DATA / "train_X.npy", mmap_mode="r")) < EXACT_REFERENCE_ROWS:
        raise RuntimeError("Source train is smaller than the bounded exact comparison reference")
    train = np.load(DATA / "train_X.npy", mmap_mode="r")
    query = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    system_before = system_memory()
    selfcheck_rows = 64
    toy = select_hash_bank(selfcheck_rows, 10)
    brute = np.asarray([i for _, i in sorted(priority_pair(i) for i in range(selfcheck_rows))[:10]], dtype=np.uint64)
    if not np.array_equal(toy, brute):
        raise RuntimeError("Hash-priority selector failed the bounded brute-force self-check")

    started = time.perf_counter()
    bank1, select_timing1 = timed(lambda: select_hash_bank(len(train), max(BANK_SIZES)))
    bank2, select_timing2 = timed(lambda: select_hash_bank(len(train), max(BANK_SIZES)))
    select_repeat_equal = bool(np.array_equal(bank1, bank2))
    bank_hash_1, bank_hash_2 = offsets_sha256(bank1), offsets_sha256(bank2)
    if not select_repeat_equal or bank_hash_1 != bank_hash_2:
        raise RuntimeError("Repeated bank selection was not identical")

    WORK.mkdir(parents=True)
    bank_meta = {}
    for k in BANK_SIZES:
        offsets = bank1[:k].copy()
        path = WORK / f"bank_offsets_k{k}.npy"
        np.save(path, offsets, allow_pickle=False)
        bank_meta[str(k)] = {"rows": k, "offsets_sha256": offsets_sha256(offsets),
                             "file_sha256": sha256(path), "bytes": path.stat().st_size,
                             "selection": "lowest SHA256(domain || uint64_be(train_row_offset)), tie by row offset"}

    scaler, scaler_timing = scaler_full_train(train)
    qidx = np.linspace(0, len(query) - 1, min(QUERY_ROWS, len(query)), dtype=np.int64)
    exact, exact_report = exact_scores(scaler, train, query, qidx, WORK)
    xq, qtransform = timed(lambda: scaler.transform(query[qidx]).astype(np.float64, copy=False))
    ref_path = WORK / "standardized_bank_k500000.tmp.npy"
    ref, bank_transform_timing = transform_reference(scaler, train, bank1, ref_path)

    comparisons = {}
    repeated_500k = None
    for k in BANK_SIZES:
        index = None
        def fit_bank():
            nonlocal index
            index = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30, metric="euclidean", n_jobs=1).fit(ref[:k])
            return index
        with threadpool_limits(limits=1):
            _, fit_timing = timed(fit_bank)
            distances, query_timing = timed(lambda: index.kneighbors(xq, return_distance=True)[0])
        scores = distances.mean(axis=1, dtype=np.float64)
        if not np.isfinite(scores).all():
            raise RuntimeError(f"Non-finite candidate distance scores for K={k}")
        absolute_error = np.abs(scores - exact)
        median_exact = float(np.median(exact))
        rank = float(spearmanr(exact, scores).statistic)
        score_hash = score_sha256(scores)
        repeated = None
        if k == max(BANK_SIZES):
            repeat_distances, repeat_query_timing = timed(lambda: index.kneighbors(xq, return_distance=True)[0])
            repeat_scores = repeat_distances.mean(axis=1, dtype=np.float64)
            if not np.isfinite(repeat_scores).all():
                raise RuntimeError("Repeated 500k bank scores are non-finite")
            repeated = {"exact_array_match": bool(np.array_equal(scores, repeat_scores)),
                        "first_sha256": score_hash, "repeat_sha256": score_sha256(repeat_scores),
                        "repeat_query_timing": repeat_query_timing}
            if not repeated["exact_array_match"]:
                raise RuntimeError("Repeated 500k bank distance scores differ")
            del repeat_distances, repeat_scores
        comparisons[str(k)] = {
            **bank_meta[str(k)], "query_rows": len(qidx),
            "index_fit": fit_timing, "query": query_timing,
            "query_rows_per_second": len(qidx) / query_timing["wall_seconds"],
            "distance_score_sha256": score_hash,
            "absolute_error_to_bounded_exact_2p4m": {
                "median": float(np.median(absolute_error)), "p95": float(np.quantile(absolute_error, .95)),
                "mean": float(np.mean(absolute_error)), "maximum": float(np.max(absolute_error)),
                "median_absolute_error_divided_by_exact_score_median": (
                    float(np.median(absolute_error) / median_exact) if median_exact > 0 else None),
                "exact_zero_count": int(np.count_nonzero(exact == 0)),
                "score_zero_count": int(np.count_nonzero(scores == 0)),
                "scope_note": "Absolute error is used because per-row relative error is undefined or unstable at exact zero and near-zero scores."},
            "score_summary": {"finite": True, "exact_score_p50": median_exact,
                              "exact_score_p95": float(np.quantile(exact, .95)),
                              "bank_score_p50": float(np.median(scores)),
                              "bank_score_p95": float(np.quantile(scores, .95))},
            "spearman_rank_correlation_to_bounded_exact_2p4m": rank,
            "distance_repeat": repeated,
        }
        if repeated is not None:
            repeated_500k = repeated
        del distances, scores, absolute_error, index

    ref._mmap.close()
    ref_path.unlink()
    del ref, xq, scaler
    total_elapsed = time.perf_counter() - started
    system_after = system_memory()
    full_test_rows = len(query)
    max_timed_peak = max(
        exact_report[part].get("peak_working_set_bytes", 0)
        for part in ("reference_transform", "query_transform", "index_fit", "query")
    )
    max_timed_peak = max(max_timed_peak, scaler_timing.get("peak_working_set_bytes", 0),
                         select_timing1.get("peak_working_set_bytes", 0),
                         select_timing2.get("peak_working_set_bytes", 0),
                         bank_transform_timing.get("peak_working_set_bytes", 0),
                         qtransform.get("peak_working_set_bytes", 0))
    for result in comparisons.values():
        max_timed_peak = max(max_timed_peak, result["index_fit"].get("peak_working_set_bytes", 0),
                             result["query"].get("peak_working_set_bytes", 0))
        result["projected_full_source_test_distance"] = {
            "rows": full_test_rows,
            "query_seconds_at_measured_throughput": full_test_rows / result["query_rows_per_second"],
            "index_fit_seconds": result["index_fit"]["wall_seconds"],
            "projected_total_seconds_excluding_scaler_bank_selection_and_transform": (
                full_test_rows / result["query_rows_per_second"] + result["index_fit"]["wall_seconds"]
            ),
            "scope_note": "Linear extrapolation from the 4,096-row feature-only query sample; excludes one-time full-train scaler fit, deterministic bank selection, and bank transform."
        }
    report = {
        "report_id": "cic-source-e1-deterministic-distance-bank-benchmark-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
        "owner_approved": True, "owner_approval_date": "2026-11-09",
        "configuration_id": cfg["configuration_id"], "config_sha256": sha256(CONFIG),
        "stage_manifest_sha256": sha256(DATA / "stage_manifest.json"),
        "source_sha256": cfg["source_dataset"]["sha256"],
        "feature_hashes": {name: stage["files"][name]["sha256"] for name in ("train_X.npy", "source_test_X.npy")},
        "feature_order": cfg["features"]["columns"], "features": 46,
        "source_train_rows": len(train), "source_test_rows": len(query),
        "labels_read": False, "target_file_read": False, "target_labels_read": False,
        "definition": "Source-train StandardScaler statistics; deterministic hash-priority row bank; exact Euclidean mean 5-NN within each bank.",
        "bank_selection": {
            "domain_separator_hex": DOMAIN.hex(), "priority": "(SHA256(domain || uint64_be(zero_based_train_row_offset)), offset)",
            "bank_sizes": list(BANK_SIZES), "selection_repeated_twice": select_repeat_equal,
            "selection_1_offsets_sha256_k500000": bank_hash_1, "selection_2_offsets_sha256_k500000": bank_hash_2,
            "selection_pass_1": select_timing1, "selection_pass_2": select_timing2,
            "banks": bank_meta, "bounded_bruteforce_selfcheck": {"rows": selfcheck_rows, "K": 10, "passed": True}},
        "scaler_fit_all_source_train": scaler_timing,
        "bounded_exact_baseline": exact_report,
        "query_transform": qtransform,
        "standardized_bank_transform_k500000": bank_transform_timing,
        "comparisons": comparisons,
        "system_memory_before": system_before, "system_memory_after": system_after,
        "maximum_observed_timed_phase_peak_working_set_bytes": max_timed_peak,
        "logical_cpu_count": CORES, "thread_limits": {"OpenMP": 1, "BLAS": 1, "KDTree_n_jobs": 1},
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                      "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
        "benchmark_elapsed_seconds": total_elapsed,
        "method_change": "No CIC E1 config or final experiment manifest was modified. This report measures feature-only bank approximations against a bounded exact subset, not against the full 12.07M-reference exact result.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "bank_sizes": list(BANK_SIZES),
                      "selection_repeated": select_repeat_equal, "500k_score_repeat_equal": repeated_500k["exact_array_match"],
                      "comparisons": {k: {"median_absolute_error": v["absolute_error_to_bounded_exact_2p4m"]["median"],
                                           "p95_absolute_error": v["absolute_error_to_bounded_exact_2p4m"]["p95"],
                                           "spearman": v["spearman_rank_correlation_to_bounded_exact_2p4m"],
                                           "query_rows_per_second": v["query_rows_per_second"]}
                                      for k,v in comparisons.items()},
                      "labels_read": False, "target_file_read": False, "target_labels_read": False}, indent=2))


if __name__ == "__main__": main()
