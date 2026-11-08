"""Bounded source-only benchmark for exact kNN and RF worker concurrency."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import threading
import time
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
DATA = ROOT / "data/processed/source-e1-lock-1"
OUT = ROOT / "reports/nf_v3_audit/source_e1_benchmark.json"
CORES = os.cpu_count() or 1


class PMC_EX(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def memory_bytes() -> int:
    if os.name != "nt":
        raise RuntimeError("This benchmark's peak-RAM measurement requires Windows process counters")
    pmc = PMC_EX()
    pmc.cb = ctypes.sizeof(pmc)
    get_current_process = ctypes.windll.kernel32.GetCurrentProcess
    get_current_process.restype = wintypes.HANDLE
    get_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory_info.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC_EX), wintypes.DWORD]
    get_memory_info.restype = wintypes.BOOL
    ok = get_memory_info(get_current_process(), ctypes.byref(pmc), pmc.cb)
    if not ok:
        raise ctypes.WinError()
    return int(pmc.WorkingSetSize)


class Monitor:
    def __init__(self) -> None:
        self.stop_event = threading.Event()
        self.samples: list[int] = []
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.samples.append(memory_bytes())
            except Exception:
                pass
            self.stop_event.wait(.05)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop_event.set()
        self.thread.join()

    @property
    def peak(self) -> int:
        return max(self.samples, default=memory_bytes())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def timed(fn):
    base = memory_bytes()
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    with Monitor() as mon:
        result = fn()
    wall = time.perf_counter() - wall0
    cpu = time.process_time() - cpu0
    peak = max(mon.peak, memory_bytes())
    return result, {
        "wall_seconds": wall,
        "process_cpu_seconds": cpu,
        "cpu_utilization_of_logical_capacity_pct": 100 * cpu / max(wall * CORES, 1e-12),
        "cpu_core_equivalents": cpu / max(wall, 1e-12),
        "baseline_working_set_bytes": base,
        "peak_working_set_bytes": peak,
        "peak_increment_bytes": max(0, peak - base),
    }


def distance_benchmark(xtr: np.ndarray, xte: np.ndarray, max_reference_rows: int) -> dict:
    # Fit the intended source-train scaler on the full frozen training partition;
    # only the reference/query counts are bounded for this benchmark.
    with threadpool_limits(limits=1):
        scaler, scaler_timing = timed(lambda: StandardScaler(copy=True).fit(xtr))
    ref_counts = [n for n in (25000, 50000, 100000, 200000, 400000, 600000, 800000) if n <= max_reference_rows]
    query_count = 512
    rows = []
    for nref in ref_counts:
        ridx = np.linspace(0, len(xtr) - 1, nref, dtype=np.int64)
        qidx = np.linspace(0, len(xte) - 1, query_count, dtype=np.int64)
        xref = scaler.transform(xtr[ridx]).astype(np.float64, copy=False)
        xquery = scaler.transform(xte[qidx]).astype(np.float64, copy=False)

        def do_search():
            nn = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30, metric="euclidean", n_jobs=1)
            fit0 = time.perf_counter()
            nn.fit(xref)
            fit_s = time.perf_counter() - fit0
            query0 = time.perf_counter()
            d, _ = nn.kneighbors(xquery, return_distance=True)
            query_s = time.perf_counter() - query0
            return {"fit_seconds": fit_s, "query_seconds": query_s, "mean_5nn_distance": float(d.mean())}

        with threadpool_limits(limits=1):
            measured, timing = timed(do_search)
        rows.append({
            "reference_rows": nref,
            "query_rows": query_count,
            "feature_count": int(xref.shape[1]),
            "reference_dtype": str(xref.dtype),
            "query_dtype": str(xquery.dtype),
            "reference_index_sha256": hashlib.sha256(ridx.tobytes()).hexdigest(),
            "query_index_sha256": hashlib.sha256(qidx.tobytes()).hexdigest(),
            **measured,
            **timing,
            "query_rows_per_second": query_count / max(measured["query_seconds"], 1e-12),
        })

    # At the largest reference, also measure query-count scaling without refit.
    nref = ref_counts[-1]
    ridx = np.linspace(0, len(xtr) - 1, nref, dtype=np.int64)
    xref = scaler.transform(xtr[ridx]).astype(np.float64, copy=False)
    nn = NearestNeighbors(n_neighbors=5, algorithm="kd_tree", leaf_size=30, metric="euclidean", n_jobs=1).fit(xref)
    query_scaling = []
    for nq in (256, 512, 1024, 2048):
        qidx = np.linspace(0, len(xte) - 1, nq, dtype=np.int64)
        xquery = scaler.transform(xte[qidx]).astype(np.float64, copy=False)
        with threadpool_limits(limits=1):
            _, timing = timed(lambda: nn.kneighbors(xquery, return_distance=True))
        query_scaling.append({"reference_rows": nref, "query_rows": nq, **timing, "query_rows_per_second": nq / timing["wall_seconds"]})
    return {"scaler_fit_full_source_train": scaler_timing, "reference_scaling": rows, "query_scaling": query_scaling}


def rf_benchmark(x: np.ndarray, y: np.ndarray, sample_fraction: float) -> dict:
    # Reproducible 10% benchmark sample, not used in E1 results.
    rng = np.random.default_rng(20261108)
    idx = np.sort(rng.choice(len(y), size=max(1, int(len(y) * sample_fraction)), replace=False))
    xs = np.asarray(x[idx], dtype=np.float32)
    ys = np.asarray(y[idx], dtype=np.uint8)

    def fit_one(seed: int) -> float:
        model = RandomForestClassifier(
            n_estimators=200, min_samples_leaf=5, criterion="gini", max_depth=None,
            min_samples_split=2, min_weight_fraction_leaf=0.0, max_features="sqrt",
            max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True,
            oob_score=False, n_jobs=1, random_state=seed, verbose=0,
            warm_start=False, class_weight=None, ccp_alpha=0.0, max_samples=None,
        )
        t0 = time.perf_counter()
        model.fit(xs, ys)
        elapsed = time.perf_counter() - t0
        del model
        return elapsed

    results = {}
    for workers in (1, 2):
        with threadpool_limits(limits=1):
            durations, timing = timed(lambda: list(ThreadPoolExecutor(max_workers=workers).map(fit_one, range(workers))))
        results[str(workers)] = {
            "concurrent_workers": workers,
            "per_worker_fit_seconds": durations,
            "worker_sample_rows": len(ys),
            "worker_sample_fraction": sample_fraction,
            "feature_count": int(xs.shape[1]),
            "sample_sha256": hashlib.sha256(idx.tobytes()).hexdigest(),
            "class_counts": {str(k): int(v) for k, v in zip(*np.unique(ys, return_counts=True))},
            **timing,
        }
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-distance", action="store_true")
    ap.add_argument("--max-reference-rows", type=int, default=200000)
    ap.add_argument("--rf-sample-fraction", type=float, default=.10)
    ap.add_argument("--output", default=str(OUT))
    args = ap.parse_args()
    if args.max_reference_rows < 25000 or args.max_reference_rows > 800000:
        raise SystemExit("--max-reference-rows must be between 25000 and 800000 for bounded benchmarking")
    if not 0 < args.rf_sample_fraction <= .5:
        raise SystemExit("--rf-sample-fraction must be >0 and <=0.5")
    manifest_path = DATA / "stage_manifest.json"
    stage = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, metadata in stage["files"].items():
        p = DATA / name
        if p.stat().st_size != metadata["bytes"] or sha256(p) != metadata["sha256"]:
            raise SystemExit(f"Refusing benchmark: staged source input mismatch: {name}")
    xtr = np.load(DATA / "train_X.npy", mmap_mode="r")
    ytr = np.load(DATA / "train_y.npy", mmap_mode="r")
    xte = np.load(DATA / "source_test_X.npy", mmap_mode="r")
    with threadpool_limits(limits=1):
        distance = None if args.skip_distance else distance_benchmark(xtr, xte, args.max_reference_rows)
        rf = rf_benchmark(xtr, ytr, args.rf_sample_fraction)
    report = {
        "report_id": "source-e1-compute-benchmark-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": os.popen("git rev-parse HEAD").read().strip(),
        "configuration_id": "source-e1-lock-1",
        "source_sha256": "4ebb97bd74412d566137d95a6fc3ffd8f374f1cf8cfe204d007848e7a668f9b5",
        "stage_manifest_sha256": sha256(manifest_path),
        "software": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "logical_cpu_count": CORES,
        "thread_limits": {"OpenMP": 1, "BLAS": 1, "RF_n_jobs": 1},
        "cpu_and_memory_measurement": "Windows GetProcessMemoryInfo working set sampled every 50 ms; CPU time from process_time, normalized by logical CPU count",
        "benchmark_scope": "bounded source-only resource benchmark; no target files opened; no outputs used for study results",
        "distance": distance,
        "random_forest": rf,
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
