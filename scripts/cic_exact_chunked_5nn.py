"""Memory-bounded, exact CIC source-train 5-NN distance with duplicate multiplicities."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from benchmark_source_e1_cic import process_memory, sha256, system_memory, timed


CHUNK_ROWS = 500_000
QUERY_BATCH_ROWS = 2_048
SCALER_BLOCK_ROWS = 100_000
NEIGHBORS = 5
LEAF_SIZE = 30
THREADS = 1


def fit_source_scaler(xtr: np.ndarray) -> tuple[StandardScaler, dict]:
    scaler = StandardScaler(copy=True)

    def fit():
        for start in range(0, len(xtr), SCALER_BLOCK_ROWS):
            scaler.partial_fit(xtr[start:min(start + SCALER_BLOCK_ROWS, len(xtr))])
        return scaler

    with threadpool_limits(limits=THREADS):
        _, timing = timed(fit)
    if not (np.isfinite(scaler.mean_).all() and np.isfinite(scaler.var_).all() and np.isfinite(scaler.scale_).all()):
        raise RuntimeError("Source-train scaler parameters are non-finite")
    timing.update({
        "rows": len(xtr), "block_rows": SCALER_BLOCK_ROWS,
        "definition": "StandardScaler statistics fitted on all original CIC source-train rows with deterministic partial_fit blocks",
        "parameters_sha256": hashlib.sha256(
            b"".join(np.asarray(a, dtype="<f8").tobytes() for a in (scaler.mean_, scaler.var_, scaler.scale_))
        ).hexdigest(),
    })
    return scaler, timing


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
        raise RuntimeError("Merged candidates do not contain five original reference rows")
    before = np.cumsum(multiplicities, axis=1, dtype=np.int64) - multiplicities
    take = np.minimum(multiplicities, np.maximum(NEIGHBORS - before, 0))
    return np.sum(distances * take, axis=1, dtype=np.float64) / NEIGHBORS


def _identity(config: dict, cfg_path: Path, data_dir: Path, chunk_rows: int,
              experiment_manifest_sha256: str, manifest_lock_commit: str) -> dict:
    stage_path = data_dir / "stage_manifest.json"
    return {
        "configuration_id": config["configuration_id"],
        "config_sha256": sha256(cfg_path),
        "experiment_manifest_sha256": experiment_manifest_sha256,
        "manifest_lock_commit": manifest_lock_commit,
        "stage_manifest_sha256": sha256(stage_path),
        "train_X_sha256": sha256(data_dir / "train_X.npy"),
        "source_test_X_sha256": sha256(data_dir / "source_test_X.npy"),
        "train_rows": int(np.load(data_dir / "train_X.npy", mmap_mode="r").shape[0]),
        "query_rows": int(np.load(data_dir / "source_test_X.npy", mmap_mode="r").shape[0]),
        "feature_order": config["features"]["columns"],
        "feature_count": len(config["features"]["columns"]),
        "distance_definition": "exact mean Euclidean distance to the five nearest original source-train rows after source-train StandardScaler",
        "reference_representation": "per-chunk np.unique(axis=0) finite float32 vectors with integer multiplicity; exact duplicate compression",
        "chunk_rows": chunk_rows,
        "query_batch_rows": QUERY_BATCH_ROWS,
        "metric": "Euclidean",
        "neighbors": NEIGHBORS,
        "algorithm": "sklearn KDTree, leaf_size=30, n_jobs=1",
        "thread_limits": {"BLAS": THREADS, "OpenMP": THREADS, "KDTree_n_jobs": THREADS},
    }


def _write_checkpoint(path: Path, state: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def compute_cic_feature_distance(config: dict, config_path: Path, data_dir: Path,
                                 output_dir: Path, experiment_manifest_sha256: str,
                                 manifest_lock_commit: str, chunk_rows: int = CHUNK_ROWS) -> dict:
    """Compute source-test scores once, using exact duplicate compression and disk-backed state."""
    output_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / "feature_space_distance.npy"
    meta_path = output_dir / "feature_space_distance.json"
    partial = output_dir / "feature_space_distance.partial.npy"
    checkpoint_path = output_dir / "feature_space_distance.checkpoint.json"
    d_paths = [output_dir / f"top5_distances_state_{i}.npy" for i in range(2)]
    c_paths = [output_dir / f"top5_counts_state_{i}.npy" for i in range(2)]

    stage = json.loads((data_dir / "stage_manifest.json").read_text(encoding="utf-8"))
    if stage["target_file_read"] or stage["target_labels_read"]:
        raise RuntimeError("Source-stage manifest reports target data access")
    if stage["configuration_sha256"] != sha256(config_path):
        raise RuntimeError("Source stage and CIC config hashes differ")
    for name in ("train_X.npy", "source_test_X.npy"):
        path = data_dir / name
        if sha256(path) != stage["files"][name]["sha256"]:
            raise RuntimeError(f"Staged feature array hash mismatch: {name}")
    xtr = np.load(data_dir / "train_X.npy", mmap_mode="r")
    xte = np.load(data_dir / "source_test_X.npy", mmap_mode="r")
    if xtr.dtype != np.float32 or xte.dtype != np.float32 or xtr.shape[1] != len(config["features"]["columns"]):
        raise RuntimeError("Unexpected staged source feature schema")
    if xte.shape[1] != xtr.shape[1]:
        raise RuntimeError("Source-train/source-test feature widths differ")
    identity = _identity(config, config_path, data_dir, chunk_rows,
                         experiment_manifest_sha256, manifest_lock_commit)

    if final.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if all(meta.get(k) == v for k, v in identity.items()) and meta.get("score_sha256") == sha256(final):
            return {"status": "reused_verified", **meta}
        raise RuntimeError("Existing completed CIC distance does not match current inputs; preserving it")
    if final.exists() or meta_path.exists():
        raise RuntimeError("Incomplete completed distance artifact pair exists; inspect before resuming")

    memory = system_memory()
    minimum_available_bytes = 4_200_000_000
    if memory["available_physical_bytes"] < minimum_available_bytes:
        raise RuntimeError(
            f"Available physical memory {memory['available_physical_bytes']:,} is below the "
            f"chunked-distance safety floor {minimum_available_bytes:,} bytes"
        )

    chunks = int(np.ceil(len(xtr) / chunk_rows))
    state_shape = (len(xte), NEIGHBORS)
    state_files_present = [p.exists() for p in (*d_paths, *c_paths, checkpoint_path)]
    if any(state_files_present) and not all(state_files_present):
        raise RuntimeError("Chunked distance resume files are incomplete; preserving them")
    if partial.exists() and not all(state_files_present):
        raise RuntimeError("Unpaired partial distance output exists; inspect before starting")

    scaler, scaler_timing = fit_source_scaler(xtr)
    if all(state_files_present):
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if not all(checkpoint.get(k) == v for k, v in identity.items()):
            raise RuntimeError("Chunked distance checkpoint does not match frozen inputs/config")
        completed_chunks = int(checkpoint["completed_chunks"])
        active_slot = int(checkpoint["active_slot"])
        if not 0 <= completed_chunks <= chunks or active_slot not in (0, 1):
            raise RuntimeError("Invalid chunked distance checkpoint state")
        chunk_records = list(checkpoint.get("chunk_records", []))
        if len(chunk_records) != completed_chunks:
            raise RuntimeError("Chunk checkpoint record count does not match completed chunks")
        if "scaler_parameters_sha256" in checkpoint and checkpoint["scaler_parameters_sha256"] != scaler_timing["parameters_sha256"]:
            raise RuntimeError("Resumed scaler parameters differ from the checkpoint")
    else:
        completed_chunks, active_slot = 0, 0
        chunk_records = []
        for slot in (0, 1):
            dmap = np.lib.format.open_memmap(d_paths[slot], mode="w+", dtype=np.float64, shape=state_shape)
            cmap = np.lib.format.open_memmap(c_paths[slot], mode="w+", dtype=np.int32, shape=state_shape)
            for start in range(0, len(xte), 100_000):
                end = min(start + 100_000, len(xte))
                dmap[start:end] = np.inf
                cmap[start:end] = 0
            dmap.flush(); cmap.flush()
            dmap._mmap.close(); cmap._mmap.close()
        _write_checkpoint(checkpoint_path, {**identity, "completed_chunks": 0, "active_slot": 0,
                                            "updated_utc": datetime.now(timezone.utc).isoformat()})

    for chunk_id in range(completed_chunks, chunks):
        start = chunk_id * chunk_rows
        end = min(start + chunk_rows, len(xtr))
        raw_chunk = np.asarray(xtr[start:end], dtype=np.float32)
        if not np.isfinite(raw_chunk).all():
            raise RuntimeError(f"Non-finite source-train features in chunk {chunk_id}")
        (unique_rows, multiplicity), unique_timing = timed(
            lambda: np.unique(raw_chunk, axis=0, return_counts=True))
        unique_rows = np.ascontiguousarray(unique_rows, dtype=np.float32)
        unique_rows_sha256 = hashlib.sha256(unique_rows.tobytes()).hexdigest()
        multiplicity_sha256 = hashlib.sha256(np.asarray(multiplicity, dtype="<u8").tobytes()).hexdigest()
        if int(np.sum(multiplicity, dtype=np.int64)) != end - start:
            raise RuntimeError("Source chunk duplicate multiplicities do not sum to its row count")
        with threadpool_limits(limits=THREADS):
            unique_z, transform_timing = timed(lambda: scaler.transform(unique_rows).astype(np.float64, copy=False))
        if not np.isfinite(unique_z).all():
            raise RuntimeError(f"Non-finite standardized unique rows in source chunk {chunk_id}")
        if len(unique_rows) < NEIGHBORS:
            raise RuntimeError(f"Source chunk {chunk_id} has fewer than five distinct reference rows")

        index = None

        def fit_index():
            nonlocal index
            index = NearestNeighbors(n_neighbors=NEIGHBORS, algorithm="kd_tree", leaf_size=LEAF_SIZE,
                                     metric="euclidean", n_jobs=THREADS).fit(unique_z)
            return index

        with threadpool_limits(limits=THREADS):
            _, fit_timing = timed(fit_index)
        unique_count = len(unique_rows)

        next_slot = 1 - active_slot
        current_d = np.load(d_paths[active_slot], mmap_mode="r")
        current_c = np.load(c_paths[active_slot], mmap_mode="r")
        next_d = np.load(d_paths[next_slot], mmap_mode="r+")
        next_c = np.load(c_paths[next_slot], mmap_mode="r+")
        q_start_time = time.perf_counter()
        query_process_cpu = time.process_time()
        for qstart in range(0, len(xte), QUERY_BATCH_ROWS):
            qend = min(qstart + QUERY_BATCH_ROWS, len(xte))
            with threadpool_limits(limits=THREADS):
                q = scaler.transform(xte[qstart:qend])
                if not np.isfinite(q).all():
                    raise RuntimeError("Non-finite standardized source-test query")
                d, idx = index.kneighbors(q, return_distance=True)
            counts = multiplicity[idx].astype(np.int32, copy=False)
            merged_d, merged_c = merge_top_five(current_d[qstart:qend], current_c[qstart:qend], d, counts)
            next_d[qstart:qend] = merged_d
            next_c[qstart:qend] = merged_c
        next_d.flush(); next_c.flush()
        query_wall = time.perf_counter() - q_start_time
        query_cpu = time.process_time() - query_process_cpu
        current_d._mmap.close(); current_c._mmap.close()
        next_d._mmap.close(); next_c._mmap.close()
        index = None
        del raw_chunk, unique_rows, unique_z, multiplicity
        active_slot = next_slot
        completed_chunks = chunk_id + 1
        record = {
            "chunk_id": chunk_id, "row_start": start, "row_end_exclusive": end,
            "raw_rows": end - start, "unique_rows": unique_count,
            "unique_rows_sha256": unique_rows_sha256, "multiplicity_sha256": multiplicity_sha256,
            "unique_extraction": unique_timing, "unique_scaling": transform_timing,
            "index_fit": fit_timing, "query_wall_seconds": query_wall,
            "query_process_cpu_seconds": query_cpu, "query_rows_per_second": len(xte) / query_wall,
            "query_cpu_core_equivalents": query_cpu / max(query_wall, 1e-12),
            "query_cpu_utilization_of_logical_capacity_pct": 100 * query_cpu / max(query_wall * (os.cpu_count() or 1), 1e-12),
            "process_working_set_after_chunk_bytes": process_memory(),
        }
        _write_checkpoint(checkpoint_path, {**identity, "completed_chunks": completed_chunks,
                                            "active_slot": active_slot,
                                            "scaler_parameters_sha256": scaler_timing["parameters_sha256"],
                                            "chunk_records": [*chunk_records, record],
                                            "updated_utc": datetime.now(timezone.utc).isoformat()})
        chunk_records.append(record)
        print(f"distance chunk {completed_chunks}/{chunks}; rows={end-start:,}; unique={record['unique_rows']:,}; "
              f"query_s={query_wall:.1f}; elapsed_peak_ws={record['process_working_set_after_chunk_bytes']:,}", flush=True)

    active_d = np.load(d_paths[active_slot], mmap_mode="r")
    active_c = np.load(c_paths[active_slot], mmap_mode="r")
    values = np.lib.format.open_memmap(partial, mode="w+", dtype=np.float32, shape=(len(xte),))
    for start in range(0, len(xte), 100_000):
        end = min(start + 100_000, len(xte))
        scores = score_top_five(active_d[start:end], active_c[start:end])
        if not np.isfinite(scores).all():
            raise RuntimeError("Non-finite exact chunk-merged feature distance")
        values[start:end] = scores.astype(np.float32)
    values.flush()
    active_d._mmap.close(); active_c._mmap.close()
    del values
    os.replace(partial, final)
    metadata = {
        **identity, "completed": True, "score_sha256": sha256(final), "dtype": "float32",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "scaler_parameters_sha256": scaler_timing["parameters_sha256"],
        "scaler_timing": scaler_timing,
        "implementation": "exact chunked KDTree 5-NN over per-chunk unique rows with source multiplicity-weighted merge",
        "query_and_merge_equivalence": "per chunk, the local top five distinct reference vectors suffice for the global top five; ties at the boundary have identical distances; multiplicities reproduce repeated raw references",
        "chunk_records": chunk_records,
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "system_memory_before_run": memory, "system_memory_after_run": system_memory(),
        "minimum_available_memory_bytes": minimum_available_bytes,
        "top_state_files": [p.name for p in (*d_paths, *c_paths)],
        "target_file_read": False, "target_labels_read": False,
        "labels_read": False,
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return {"status": "computed", **metadata}
