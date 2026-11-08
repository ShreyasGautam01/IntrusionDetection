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
    ref_counts = [n for n in (25000, 50000, 100000, 200000, 400000, 600000, 800000) if n <= max_refere