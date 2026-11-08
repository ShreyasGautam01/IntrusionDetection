"""Bounded, source-only CIC E1 resource benchmark; never opens UNSW target data."""
from __future__ import annotations

import argparse
import ctypes
import gc
import hashlib
import json
import math
import os
import platform
import threading
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from ctypes import wintypes

import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed/source-e1-cic-lock-1"
CONFIG = ROOT / "reports/nf_v3_audit/source_e1_cic_config.json"
OUT = ROOT / "reports/nf_v3_audit/cic_source_e1_benchmark.json"
CORES = os.cpu_count() or 1


class PMC_EX(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t)]


def process_memory() -> int:
    if os.name != "nt":
        raise RuntimeError("Peak-RAM measurement requires Windows process counters")
    pmc = PMC_EX(); pmc.cb = ctypes.sizeof(pmc)
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.restype = wintypes.HANDLE
    get_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC_EX), wintypes.DWORD]
    get_info.restype = wintypes.BOOL
    if not get_info(get_process(), ctypes.byref(pmc), pmc.cb):
        raise ctypes.WinError()
    return int(pmc.WorkingSetSize)


def system_memory() -> dict:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    status = MEMORYSTATUSEX(); status.dwLength = ctypes.sizeof(status)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise ctypes.WinError()
    return {"total_physical_bytes": int(status.ullTotalPhys), "available_physical_bytes": int(status.ullAvailPhys),
            "memory_load_pct": int(status.dwMemoryLoad)}


class Monitor:
    def __init__(self):
        self.stop = threading.Event(); self.samples = []
        self.thread = threading.Thread(target=self._sample, daemon=True)
    def _sample(self):
        while not self.stop.is_set():
            try: self.samples.append(process_memory())
            except Exception: pass
            self.stop.wait(.05)
    def __enter__(self): self.thread.start(); return self
    def __exit__(self, *_): self.stop.set(); self.thread.join()
    @property
    def peak(self): return max(self.samples, default=process_memory())


def timed(fn) -> tuple[object, dict]:
    base = process_memory(); cpu0 = time.process_time(); wall0 = time.perf_counter()
    with Monitor() as monitor:
        result = fn()
    wall = time.perf_counter() - wall0; cpu = time.process_time() - cpu0
    peak = max(monitor.peak, process_memory())
    return result, {"wall_seconds": wall, "process_cpu_seconds": cpu,
                    "cpu_core_equivalents": cpu / max(wall, 1e-12),
                    "cpu_utilization_of_logical_capacity_pct": 100 * cpu / max(wall * CORES, 1e-12),
                    "baseline_working_set_bytes": base, "peak_working_set_bytes": peak,
                    "peak_increment_bytes": max(0, peak - base)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def verify_stage() -> dict:
    manifest_path = DATA / "stage_manifest.json"
    stage = json.loads(manifest_path.read_text(encoding="utf-8"))
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if sha256(CONFIG) != stage["configuration_sha256"]:
        raise RuntimeError("CIC staged config hash mismatch")
    replacement_path = ROOT / cfg["preprocessing"]["replacement_values_file"]
    if sha256(replacement_path) != cfg["preprocessing"]["replacement_values_sha256"]:
        raise RuntimeError("CIC source-train finite replacement record hash mismatch")
    if stage["configuration_id"] != cfg["configuration_id"]:
        raise RuntimeError("CIC config/stage identity mismatch")
    if stage["source_dataset"]["sha256"] != cfg["source_dataset"]["sha256"]:
        raise RuntimeError("CIC source dataset hash mismatch")
    if stage["feature_order"] != cfg["features"]["columns"] or len(stage["feature_order"]) != 46:
        raise RuntimeError("CIC stage feature order does not match the frozen 46-feature config")
    if stage["target_file_read"] or stage["target_labels_read"]:
        raise RuntimeError("CIC source gate stage claims target access")
    expected_parts = {"train": ("train_X.npy", "train_y.npy"),
                      "calibration": ("calibration_X.npy", "calibration_y.npy"),
                      "source_test": ("source_test_X.npy", "source_test_y.npy")}
    for part, (x_name, y_name) in expected_parts.items():
        xp, yp = DATA / x_name, DATA / y_name
        x_meta, y_meta = stage["files"][x_name], stage["files"][y_name]
        if xp.stat().st_size != x_meta["bytes"] or sha256(xp) != x_meta["sha256"]:
            raise RuntimeError(f"Staged CIC array integrity mismatch: {x_name}")
        if yp.stat().st_size != y_meta["bytes"] or sha256(yp) != y_meta["sha256"]:
            raise RuntimeError(f"Staged CIC array integrity mismatch: {y_name}")
        x = np.load(xp, mmap_mode="r"); y = np.load(yp, mmap_mode="r")
        if x.shape != (stage["partition_rows"][part], 46) or x.dtype != np.float32:
            raise RuntimeError(f"CIC {part} feature array shape/dtype mismatch")
        if y.shape != (len(x),) or y.dtype != np.int8:
            raise RuntimeError(f"CIC {part} label array shape/dtype mismatch")
        if not set(np.unique(y)).issubset({0, 1}):
            raise RuntimeError(f"CIC {part} labels are not binary")
        for start in range(0, len(x), 100_000):
            if not np.isfinite(x[start:start + 100_000]).all():
                raise RuntimeError(f"CIC {part} features contain non-finite values")
        observed = {str(int(k)): int(v) for k, v in zip(*np.unique(y, return_counts=True))}
        if observed != stage["class_counts"][part]:
            raise RuntimeError(f"CIC {part} label counts differ from the stage manifest")
    if sum(stage["partition_rows"].values()) != cfg["source_dataset"]["row_count"]:
        raise RuntimeError("CIC source partitions do not sum to audited row count")
    return stage


def fit_full_streaming_scaler(xtr: np.ndarray) -> tuple[StandardScaler, dict]:
    scaler = StandardScaler(copy=True)
    def fit():
        for start in range(0, len(xtr), 100_000):
            scaler.partial_fit(xtr[start:min(start + 100_000, len(xtr))])
        return scaler
    with threadpool_limits(limits=1):
        _, timing = timed(fit)
    timing["rows"] = len(xtr); timing["block_rows"] = 100_000
    timing["definition"] = "StandardScaler mean/variance fitted over every CIC source-train row using deterministic partial_fit blocks"
    return scaler, timing


def distance_benchmark(xtr: np.ndarray, xte: np.ndarray, max_refs: int, query_count: int) -> dict:
    scaler, scaler_timing = fit_full_streaming_scaler(xtr)
    counts = sorted(set(min(n, max_refs, len(xtr)) for n in (100_000, 250_000, 500_000, 800_000, 1_200_000, 1_600_000, 2_000_000, 2_400_000) if n <= max_refs))
    if not counts: raise ValueError("No allowed distance reference size")
    rows = []; scaling = []
    qidx = np.linspace(0, len(xte) - 1, min(query_count, len(xte)), dtype=np.int64)
    xquery, query_transform_timing = timed(lambda: scaler.transform(xte[qidx]).astype(np.float64, copy=False))
    query_transform_timing["query_rows"] = len(qidx)
    for nref in counts:
        ridx = np.linspace(0, len(xtr) - 1, nref, dtype=np.int64)
        with tempfile.TemporaryDirectory(prefix=f"cic-e1-distance-{nref}-", dir=str(DATA)) as tmpdir:
            ref_path = Path(tmpdir) / "standardized_reference.npy"
            xref_out = np.lib.format.open_memmap(ref_path, mode="w+", dtype=np.float64,
                                                  shape=(nref, xtr.shape[1]))
            def transform_reference():
                for start in range(0, nref, 20_000):
                    end = min(start + 20_000, nref)
                    xref_out[start:end] = scaler.transform(xtr[ridx[start:end]])
                xref_out.flush()
            _, transform_timing = timed(transform_reference)
            transform_timing["reference_rows"] = nref
            transform_timing["rows_per_second"] = nref / max(transform_timing["wall_seconds"], 1e-12)
            xref_out._mmap.close()
            xref = np.load(ref_path, mmap_mode="r")
            index = None
            def fit_index():
                nonlocal index
                index = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30,
                                         metric="euclidean", n_jobs=1).fit(xref)
                return index
            _, fit_timing = timed(fit_index)
            def query(): return index.kneighbors(xquery, return_distance=True)[0]
            distances, query_timing = timed(query)
            row = {"reference_rows": int(nref), "query_rows": int(len(qidx)), "feature_count": int(xtr.shape[1]),
                   "reference_dtype": str(xref.dtype), "query_dtype": str(xquery.dtype),
                   "reference_indices_sha256": hashlib.sha256(ridx.tobytes()).hexdigest(),
                   "query_indices_sha256": hashlib.sha256(qidx.tobytes()).hexdigest(),
                   "reference_transform": transform_timing, "index_fit": fit_timing,
                   "query_transform": query_transform_timing, "query": query_timing,
                   "query_rows_per_second": len(qidx) / max(query_timing["wall_seconds"], 1e-12),
                   "mean_5nn_distance": float(distances.mean()),
                   "definition": "exact sklearn KDTree Euclidean 5-NN over this deterministic subset of actual source-train rows"}
            rows.append(row)
            if nref == counts[-1]:
                for nq in (128, 512, 2048, 4096):
                    qidx_s = np.linspace(0, len(xte) - 1, min(nq, len(xte)), dtype=np.int64)
                    xq, xq_transform_timing = timed(lambda: scaler.transform(xte[qidx_s]).astype(np.float64, copy=False))
                    d, timing = timed(lambda: index.kneighbors(xq, return_distance=True)[0])
                    scaling.append({"reference_rows": counts[-1], "query_rows": len(qidx_s),
                                    "query_transform": xq_transform_timing, "timing": timing,
                                    "query_rows_per_second": len(qidx_s) / timing["wall_seconds"],
                                    "query_indices_sha256": hashlib.sha256(qidx_s.tobytes()).hexdigest(),
                                    "mean_5nn_distance": float(d.mean())})
                    del d, xq; gc.collect()
            del distances, index
            xref._mmap.close()
        gc.collect()
        print(f"distance benchmark refs={nref:,} transform_s={transform_timing['wall_seconds']:.2f} index_s={fit_timing['wall_seconds']:.2f} query_s={query_timing['wall_seconds']:.3f} peak_MB={max(transform_timing['peak_working_set_bytes'],fit_timing['peak_working_set_bytes'],query_timing['peak_working_set_bytes'])/1e6:.1f}", flush=True)

    gc.collect()
    return {"scaler_fit_all_source_train": scaler_timing,
            "reference_scaling": rows, "query_scaling_at_max_reference": scaling,
            "full_reference_float64_bytes_lower_bound": int(len(xtr) * xtr.shape[1] * 8),
            "source_train_rows": int(len(xtr)), "source_test_rows": int(len(xte)),
            "reference_transform_block_rows": 20_000,
            "full_exact_definition": "all CIC source-train rows standardized by source-train-only StandardScaler; exact Euclidean distance to the five nearest rows; mean of five distances"}

def rf_benchmark(x: np.ndarray, y: np.ndarray, cfg: dict, fraction: float) -> dict:
    rng = np.random.default_rng(20261109)
    idx = np.sort(rng.choice(len(y), size=max(1, int(len(y) * fraction)), replace=False))
    xs = np.asarray(x[idx], dtype=np.float32); ys = np.asarray(y[idx], dtype=np.uint8)
    params = dict(cfg["random_forest"]["parameters"]); params["random_state"] = 0
    params["n_jobs"] = 1
    def fit_one(seed: int) -> float:
        model = RandomForestClassifier(**{**params, "random_state": seed})
        start = time.perf_counter(); model.fit(xs, ys); elapsed = time.perf_counter() - start
        del model
        return elapsed
    results = {}
    for workers in (1, 2):
        gc.collect()
        with threadpool_limits(limits=1):
            durations, timing = timed(lambda: list(ThreadPoolExecutor(max_workers=workers).map(fit_one, (0, 1))))
        results[str(workers)] = {"concurrent_workers": workers, "fit_count": 2,
                                 "per_fit_seconds": durations, "worker_sample_rows": len(ys),
                                 "worker_sample_fraction": fraction, "feature_count": int(xs.shape[1]),
                                 "sample_indices_sha256": hashlib.sha256(idx.tobytes()).hexdigest(),
                                 "class_counts": {str(k): int(v) for k, v in zip(*np.unique(ys, return_counts=True))},
                                 "fits_per_second": 2 / timing["wall_seconds"], **timing}
        print(f"RF workers={workers} pair_wall_s={timing['wall_seconds']:.1f} peak_MB={timing['peak_working_set_bytes']/1e6:.1f}", flush=True)
    return results


def estimate_full(distance: dict, memory: dict) -> dict:
    points = distance["reference_scaling"]
    points = sorted(points, key=lambda x: x["reference_rows"])[-3:]
    nfull = distance["source_train_rows"]; qfull = distance["source_test_rows"]
    def exponents(metric):
        vals = []
        for a, b in zip(points, points[1:]):
            va, vb = metric(a), metric(b)
            if va > 0 and vb > 0 and b["reference_rows"] > a["reference_rows"]:
                vals.append(math.log(vb / va) / math.log(b["reference_rows"] / a["reference_rows"]))
        return vals or [1.0]
    fit_exp = exponents(lambda r: r["index_fit"]["wall_seconds"])
    query_exp = exponents(lambda r: r["query"]["wall_seconds"] / r["query_rows"])
    last = points[-1]; ratio = nfull / last["reference_rows"]
    fit_times = [last["index_fit"]["wall_seconds"] * ratio ** max(0, min(3, a)) for a in fit_exp]
    per_query = [last["query"]["wall_seconds"] / last["query_rows"] * ratio ** max(0, min(3, a)) for a in query_exp]
    reference_transform = last["reference_transform"]["wall_seconds"] / last["reference_rows"] * nfull
    query_transform = last["query_transform"]["wall_seconds"] / last["query_rows"] * qfull
    scaler_fit = distance["scaler_fit_all_source_train"]["wall_seconds"]
    qscale = distance["query_scaling_at_max_reference"]
    qfactors = [x["query_rows_per_second"] for x in qscale]
    estimate = [scaler_fit + reference_transform + query_transform + fit + qfull * qp for fit in fit_times for qp in per_query]
    measured_peak_increment = max(p["index_fit"]["peak_increment_bytes"] for p in points)
    sample_baseline = points[-1]["index_fit"]["baseline_working_set_bytes"]
    projected_increment = int(measured_peak_increment * ratio)
    projected_process_peak = sample_baseline + projected_increment
    return {"method": "Tail-scaling envelope from largest bounded exact KDTree fits and per-query timings; not a guarantee",
            "reference_growth_exponents_measured": {"index_fit": fit_exp, "query_seconds_per_row": query_exp},
            "full_index_fit_seconds_estimate_range": [min(fit_times), max(fit_times)],
            "full_query_seconds_estimate_range": [qfull * min(per_query), qfull * max(per_query)],
            "full_scaler_fit_seconds_measured": scaler_fit,
            "full_reference_transform_seconds_estimated": reference_transform,
            "full_query_transform_seconds_estimated": query_transform,
            "full_total_seconds_estimate_range": [min(estimate), max(estimate)],
            "full_total_hours_estimate_range": [min(estimate) / 3600, max(estimate) / 3600],
            "full_exact_float64_reference_lower_bound_bytes": distance["full_reference_float64_bytes_lower_bound"],
            "available_physical_memory_bytes_at_benchmark": memory["available_physical_bytes"],
            "sample_peak_increment_bytes_at_largest_reference": measured_peak_increment,
            "peak_increment_linear_extrapolation_bytes": projected_increment,
            "sample_baseline_working_set_bytes": sample_baseline,
            "projected_full_process_peak_working_set_bytes": projected_process_peak,
            "projected_headroom_vs_available_bytes_at_benchmark_start": memory["available_physical_bytes"] - projected_process_peak,
            "query_scaling_throughput_rows_per_second": qfactors}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-reference-rows", type=int, default=2_400_000)
    ap.add_argument("--query-rows", type=int, default=512)
    ap.add_argument("--rf-sample-fraction", type=float, default=.02)
    ap.add_argument("--skip-distance", action="store_true")
    ap.add_argument("--skip-rf", action="store_true")
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    if not 100_000 <= args.max_reference_rows <= 2_400_000:
        raise SystemExit("--max-reference-rows must be in 100000..2400000 for bounded safety")
    if not 1 <= args.query_rows <= 4096:
        raise SystemExit("--query-rows must be in 1..4096 for bounded safety")
    if not 0 < args.rf_sample_fraction <= .05:
        raise SystemExit("--rf-sample-fraction must be >0 and <=0.05")
    if args.output.exists(): raise SystemExit(f"Refusing to overwrite benchmark evidence: {args.output}")
    stage = verify_stage(); cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    xtr = np.load(DATA / "train_X.npy", mmap_mode="r"); ytr = np.load(DATA / "train_y.npy", mmap_mode="r")
    xte = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    system_before = system_memory()
    with threadpool_limits(limits=1):
        distance = None if args.skip_distance else distance_benchmark(xtr, xte, min(args.max_reference_rows, len(xtr)), args.query_rows)
        rf = None if args.skip_rf else rf_benchmark(xtr, ytr, cfg, args.rf_sample_fraction)
    system_after = system_memory()
    report = {"report_id": "cic-source-e1-bounded-benchmark-1", "generated_utc": datetime.now(timezone.utc).isoformat(),
              "git_commit": os.popen("git rev-parse HEAD").read().strip(), "configuration_id": cfg["configuration_id"],
              "config_sha256": sha256(CONFIG), "stage_manifest_sha256": sha256(DATA / "stage_manifest.json"),
              "source_sha256": cfg["source_dataset"]["sha256"],
              "software": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
              "logical_cpu_count": CORES, "thread_limits": {"OpenMP": 1, "BLAS": 1, "RF_n_jobs": 1},
              "measurement": "Windows process working set sampled every 50ms; process CPU time normalized by logical CPU count; system physical memory from GlobalMemoryStatusEx",
              "system_memory_before": system_before, "system_memory_after": system_after,
              "benchmark_scope": "Bounded exact distance subsets and deterministic source-only RF sample; target dataset/labels not opened; benchmark outputs are not study results",
              "distance": distance, "random_forest": rf,
              "full_run_estimate": estimate_full(distance, system_before) if distance else None,
              "source_rows": stage["partition_rows"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
