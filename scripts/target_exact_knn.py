"""Exact, resumable target-side mean 5-NN distance using duplicate multiplicities."""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from benchmark_source_e1_cic import system_memory, timed

NEIGHBORS = 5
LEAF_SIZE = 30
THREADS = 1
DEFAULT_REFERENCE_CHUNK_ROWS = 500_000
DEFAULT_QUERY_BATCH_ROWS = 2_048


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def merge_top_five(d_current: np.ndarray, c_current: np.ndarray,
                   d_chunk: np.ndarray, c_chunk: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    candidates_d = np.concatenate((d_current, d_chunk), axis=1)
    candidates_c = np.concatenate((c_current, c_chunk), axis=1)
    order = np.argsort(candidates_d, axis=1, kind="stable")[:, :NEIGHBORS]
    best_d = np.take_along_axis(candidates_d, order, axis=1)
    best_c = np.take_along_axis(candidates_c, order, axis=1)
    return best_d, np.minimum(best_c, NEIGHBORS).astype(np.int32, copy=False)


def score_top_five(distances: np.ndarray, multiplicities: np.ndarray) -> np.ndarray:
    if not np.isfinite(distances).all() or np.any(multiplicities < 0):
        raise RuntimeError("Invalid merged top-five candidates")
    if np.any(np.sum(multiplicities, axis=1, dtype=np.int64) < NEIGHBORS):
        raise RuntimeError("Merged candidates contain fewer than five original references")
    before = np.cumsum(multiplicities, axis=1, dtype=np.int64) - multiplicities
    take = np.minimum(multiplicities, np.maximum(NEIGHBORS - before, 0))
    return np.sum(distances * take, axis=1, dtype=np.float64) / NEIGHBORS


def scaler_parameter_hash(scaler: StandardScaler) -> str:
    return hashlib.sha256(b"".join(
        np.asarray(array, dtype="<f8").tobytes()
        for array in (scaler.mean_, scaler.var_, scaler.scale_)
    )).hexdigest()


def benchmark_exact_case(
    source_train: np.ndarray,
    target_queries: np.ndarray,
    scaler: StandardScaler,
    *,
    reference_rows: int,
    query_rows: int,
    chunk_rows: int = DEFAULT_REFERENCE_CHUNK_ROWS,
    query_batch_rows: int = DEFAULT_QUERY_BATCH_ROWS,
    return_scores: bool = False,
) -> dict:
    """Measure the production exact chunk/merge procedure on bounded arrays."""
    if not 1 <= reference_rows <= len(source_train):
        raise ValueError("reference_rows is outside the actual source-train array")
    if not 1 <= query_rows <= len(target_queries):
        raise ValueError("query_rows is outside the bounded target feature sample")
    if chunk_rows < NEIGHBORS or query_batch_rows < 1:
        raise ValueError("Invalid exact-distance chunk/batch size")
    current_d = np.full((query_rows, NEIGHBORS), np.inf, dtype=np.float64)
    current_c = np.zeros((query_rows, NEIGHBORS), dtype=np.int32)
    pieces = []
    total_wall = total_cpu = total_unique_wall = total_fit_wall = total_query_wall = 0.0
    peak_bytes = 0
    reference_chunk_count = 0
    for start in range(0, reference_rows, chunk_rows):
        end = min(start + chunk_rows, reference_rows)
        raw_chunk = np.asarray(source_train[start:end], dtype=np.float32)
        if not np.isfinite(raw_chunk).all():
            raise ValueError("Source-training reference subset contains non-finite values")
        (unique_rows, multiplicity), unique_timing = timed(
            lambda: np.unique(raw_chunk, axis=0, return_counts=True))
        if len(unique_rows) < 1:
            raise ValueError("Reference chunk is empty")
        unique_rows = np.ascontiguousarray(unique_rows, dtype=np.float32)
        z_reference, scale_timing = timed(
            lambda: scaler.transform(unique_rows).astype(np.float64, copy=False))
        index = NearestNeighbors(
            n_neighbors=min(NEIGHBORS, len(unique_rows)), algorithm="kd_tree",
            leaf_size=LEAF_SIZE, metric="euclidean", n_jobs=THREADS,
        )
        with threadpool_limits(limits=THREADS):
            _, fit_timing = timed(lambda: index.fit(z_reference))
        query_wall = query_cpu = 0.0
        for qstart in range(0, query_rows, query_batch_rows):
            qend = min(qstart + query_batch_rows, query_rows)
            q_raw = np.asarray(target_queries[qstart:qend], dtype=np.float32)
            if not np.isfinite(q_raw).all():
                raise ValueError("Target query subset contains non-finite values")

            def query_and_merge():
                q = scaler.transform(q_raw).astype(np.float64, copy=False)
                distances, indices = index.kneighbors(q, return_distance=True)
                counts = multiplicity[indices].astype(np.int32, copy=False)
                merged_d, merged_c = merge_top_five(
                    current_d[qstart:qend], current_c[qstart:qend], distances, counts)
                current_d[qstart:qend] = merged_d
                current_c[qstart:qend] = merged_c
                return len(q_raw)

            _, query_timing = timed(query_and_merge)
            query_wall += query_timing["wall_seconds"]
            query_cpu += query_timing["process_cpu_seconds"]
            peak_bytes = max(peak_bytes, query_timing["peak_working_set_bytes"])
        total_unique_wall += unique_timing["wall_seconds"]
        total_fit_wall += scale_timing["wall_seconds"] + fit_timing["wall_seconds"]
        total_query_wall += query_wall
        total_wall += unique_timing["wall_seconds"] + scale_timing["wall_seconds"] + fit_timing["wall_seconds"] + query_wall
        total_cpu += (unique_timing["process_cpu_seconds"] + scale_timing["process_cpu_seconds"]
                      + fit_timing["process_cpu_seconds"] + query_cpu)
        peak_bytes = max(peak_bytes, unique_timing["peak_working_set_bytes"],
                         scale_timing["peak_working_set_bytes"], fit_timing["peak_working_set_bytes"])
        pieces.append({"start": start, "end_exclusive": end,
                       "unique_reference_rows": len(unique_rows),
                       "duplicate_compression_ratio": (end - start) / len(unique_rows),
                       "unique_seconds": unique_timing["wall_seconds"],
                       "scale_seconds": scale_timing["wall_seconds"],
                       "index_fit_seconds": fit_timing["wall_seconds"],
                       "query_seconds": query_wall})
        reference_chunk_count += 1
        del raw_chunk, unique_rows, multiplicity, z_reference, index
    scores = score_top_five(current_d, current_c).astype(np.float32)
    if not np.isfinite(scores).all():
        raise RuntimeError("Exact chunk-merged query scores are non-finite")
    result = {
        "reference_rows": int(reference_rows), "query_rows": int(query_rows),
        "reference_chunk_rows": int(chunk_rows), "reference_chunk_count": reference_chunk_count,
        "reference_chunks": pieces, "unique_extraction_seconds": total_unique_wall,
        "scaler_and_index_seconds": total_fit_wall, "query_seconds": total_query_wall,
        "wall_seconds": total_wall, "process_cpu_seconds": total_cpu,
        "cpu_core_equivalents": total_cpu / max(total_wall, 1e-12),
        "cpu_utilization_of_logical_capacity_pct": 100 * total_cpu / max(total_wall * (os.cpu_count() or 1), 1e-12),
        "query_rows_per_second": query_rows / max(total_query_wall, 1e-12),
        "peak_working_set_bytes": peak_bytes,
        "all_finite": True,
    }
    if return_scores:
        result["scores"] = scores
    return result


def _atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def compute_exact_target_distance(
    source_train: np.ndarray,
    target_features: np.ndarray,
    scaler: StandardScaler,
    output_dir: Path,
    *,
    identity: dict,
    chunk_rows: int = DEFAULT_REFERENCE_CHUNK_ROWS,
    query_batch_rows: int = DEFAULT_QUERY_BATCH_ROWS,
) -> dict:
    """Compute all target distances exactly, checkpointed by source-reference chunk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / "feature_space_distance.npy"
    metadata_path = output_dir / "feature_space_distance.json"
    checkpoint_path = output_dir / "feature_space_distance.checkpoint.json"
    partial = output_dir / "feature_space_distance.partial.npy"
    d_paths = [output_dir / f"top5_distances_state_{i}.npy" for i in range(2)]
    c_paths = [output_dir / f"top5_counts_state_{i}.npy" for i in range(2)]
    required_identity = {
        **identity,
        "source_train_rows": int(len(source_train)),
        "target_feature_rows": int(len(target_features)),
        "feature_count": int(source_train.shape[1]),
        "feature_distance": "mean Euclidean distance to five nearest original source-training rows after source-training StandardScaler",
        "reference_compression": "per-reference-chunk exact duplicate compression with integer multiplicity",
        "chunk_rows": int(chunk_rows), "query_batch_rows": int(query_batch_rows),
        "neighbors": NEIGHBORS, "metric": "euclidean", "algorithm": "sklearn KDTree",
        "leaf_size": LEAF_SIZE, "n_jobs": THREADS,
        "scaler_parameters_sha256": scaler_parameter_hash(scaler),
    }
    if final.exists() or metadata_path.exists():
        if not (final.exists() and metadata_path.exists()):
            raise RuntimeError("Incomplete final target-distance pair exists; preserving it")
        old = json.loads(metadata_path.read_text(encoding="utf-8"))
        if all(old.get(k) == v for k, v in required_identity.items()) and old.get("score_sha256") == sha256_file(final):
            return {"status": "reused_verified", **old}
        raise RuntimeError("Existing target-distance result conflicts with current lock; preserving it")
    if target_features.ndim != 2 or target_features.shape[1] != source_train.shape[1]:
        raise ValueError("Source and target feature matrix schemas differ")
    if source_train.dtype != np.float32 or target_features.dtype != np.float32:
        raise ValueError("Exact distance arrays must be float32 as staged by the frozen source protocol")

    total_chunks = math.ceil(len(source_train) / chunk_rows)
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if any(checkpoint.get(k) != v for k, v in required_identity.items()):
            raise RuntimeError("Target-distance checkpoint belongs to a different frozen identity")
        completed = int(checkpoint.get("completed_chunks", -1))
        active_slot = int(checkpoint.get("active_slot", -1))
        records = list(checkpoint.get("chunk_records", []))
        if not (0 <= completed <= total_chunks and active_slot in (0, 1) and len(records) == completed):
            raise RuntimeError("Target-distance checkpoint is inconsistent; preserving it")
        if not all(p.exists() for p in (*d_paths, *c_paths)):
            raise RuntimeError("Target-distance checkpoint state is incomplete; preserving it")
    elif any(p.exists() for p in (*d_paths, *c_paths, partial)):
        raise RuntimeError("Unpaired target-distance partial files exist; inspect and preserve them")
    else:
        for path in d_paths:
            a = np.lib.format.open_memmap(path, mode="w+", dtype=np.float64,
                                          shape=(len(target_features), NEIGHBORS))
            for start in range(0, len(a), 100_000):
                a[start:min(start + 100_000, len(a))] = np.inf
            a.flush(); del a
        for path in c_paths:
            a = np.lib.format.open_memmap(path, mode="w+", dtype=np.int32,
                                          shape=(len(target_features), NEIGHBORS))
            a[:] = 0; a.flush(); del a
        completed, active_slot, records = 0, 0, []
        _atomic_json(checkpoint_path, {**required_identity, "completed_chunks": 0,
                                       "active_slot": 0, "chunk_records": [],
                                       "created_utc": datetime.now(timezone.utc).isoformat()})

    for chunk_id in range(completed, total_chunks):
        start = chunk_id * chunk_rows
        end = min(start + chunk_rows, len(source_train))
        raw = np.asarray(source_train[start:end], dtype=np.float32)
        if not np.isfinite(raw).all():
            raise RuntimeError(f"Non-finite source-training reference rows in chunk {chunk_id}")
        (unique_rows, multiplicity), unique_timing = timed(
            lambda: np.unique(raw, axis=0, return_counts=True))
        if len(unique_rows) < NEIGHBORS:
            raise RuntimeError(f"Reference chunk {chunk_id} has fewer than five unique rows")
        unique_rows = np.ascontiguousarray(unique_rows, dtype=np.float32)
        unique_z, scale_timing = timed(lambda: scaler.transform(unique_rows).astype(np.float64, copy=False))
        index = NearestNeighbors(n_neighbors=NEIGHBORS, algorithm="kd_tree", leaf_size=LEAF_SIZE,
                                 metric="euclidean", n_jobs=THREADS)
        with threadpool_limits(limits=THREADS):
            _, fit_timing = timed(lambda: index.fit(unique_z))
        next_slot = 1 - active_slot
        current_d = np.load(d_paths[active_slot], mmap_mode="r")
        current_c = np.load(c_paths[active_slot], mmap_mode="r")
        next_d = np.load(d_paths[next_slot], mmap_mode="r+")
        next_c = np.load(c_paths[next_slot], mmap_mode="r+")
        query_wall = query_cpu = 0.0
        peak = max(unique_timing["peak_working_set_bytes"], scale_timing["peak_working_set_bytes"],
                   fit_timing["peak_working_set_bytes"])
        for qstart in range(0, len(target_features), query_batch_rows):
            qend = min(qstart + query_batch_rows, len(target_features))
            q_raw = np.asarray(target_features[qstart:qend], dtype=np.float32)

            def query_and_merge():
                q = scaler.transform(q_raw).astype(np.float64, copy=False)
                if not np.isfinite(q).all():
                    raise RuntimeError("Non-finite target query after source-fitted scaling")
                distances, indices = index.kneighbors(q, return_distance=True)
                counts = multiplicity[indices].astype(np.int32, copy=False)
                merged_d, merged_c = merge_top_five(
                    current_d[qstart:qend], current_c[qstart:qend], distances, counts)
                next_d[qstart:qend] = merged_d
                next_c[qstart:qend] = merged_c
            _, timing = timed(query_and_merge)
            query_wall += timing["wall_seconds"]
            query_cpu += timing["process_cpu_seconds"]
            peak = max(peak, timing["peak_working_set_bytes"])
        next_d.flush(); next_c.flush()
        current_d._mmap.close(); current_c._mmap.close()
        next_d._mmap.close(); next_c._mmap.close()
        active_slot = next_slot
        record = {
            "chunk_id": chunk_id, "row_start": start, "row_end_exclusive": end,
            "raw_reference_rows": end - start, "unique_reference_rows": len(unique_rows),
            "unique_rows_sha256": hashlib.sha256(unique_rows.tobytes()).hexdigest(),
            "multiplicity_sha256": hashlib.sha256(np.asarray(multiplicity, dtype="<u8").tobytes()).hexdigest(),
            "unique_seconds": unique_timing["wall_seconds"],
            "scaling_seconds": scale_timing["wall_seconds"],
            "index_fit_seconds": fit_timing["wall_seconds"],
            "query_wall_seconds": query_wall, "query_process_cpu_seconds": query_cpu,
            "query_rows_per_second": len(target_features) / max(query_wall, 1e-12),
            "peak_working_set_bytes": peak,
        }
        records.append(record)
        _atomic_json(checkpoint_path, {**required_identity, "completed_chunks": chunk_id + 1,
                                       "active_slot": active_slot, "chunk_records": records,
                                       "updated_utc": datetime.now(timezone.utc).isoformat()})
        print(f"target exact distance chunk {chunk_id + 1}/{total_chunks}; "
              f"query_s={query_wall:.1f}; peak_ws={peak}", flush=True)
        del raw, unique_rows, unique_z, multiplicity, index

    active_d = np.load(d_paths[active_slot], mmap_mode="r")
    active_c = np.load(c_paths[active_slot], mmap_mode="r")
    output = np.lib.format.open_memmap(partial, mode="w+", dtype=np.float32,
                                       shape=(len(target_features),))
    for start in range(0, len(target_features), 100_000):
        end = min(start + 100_000, len(target_features))
        scores = score_top_five(active_d[start:end], active_c[start:end]).astype(np.float32)
        if not np.isfinite(scores).all():
            raise RuntimeError("Non-finite exact target distance result")
        output[start:end] = scores
    output.flush(); del output
    active_d._mmap.close(); active_c._mmap.close()
    os.replace(partial, final)
    metadata = {
        **required_identity, "completed": True, "score_sha256": sha256_file(final),
        "dtype": "float32", "completed_utc": datetime.now(timezone.utc).isoformat(),
        "chunk_records": records,
        "query_merge_equivalence": "each reference chunk contributes its exact local top five distinct vectors with multiplicities; merging these candidates reproduces the five nearest original source rows including duplicate ties",
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit_learn": sklearn.__version__},
        "thread_limits": {"BLAS": THREADS, "OpenMP": THREADS, "KDTree_n_jobs": THREADS},
        "system_memory_after_run": system_memory(), "target_labels_read": False,
    }
    _atomic_json(metadata_path, metadata)
    return {"status": "completed", **metadata}
