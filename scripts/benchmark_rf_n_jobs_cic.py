"""Bounded CIC source-only RandomForest n_jobs benchmark; no target files/labels."""
from __future__ import annotations

import argparse
import ctypes
import gc
import hashlib
import json
import os
import platform
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.ensemble import RandomForestClassifier
from threadpoolctl import threadpool_limits


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def memory_snapshot() -> dict:
    class MS(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                    ("total", ctypes.c_ulonglong), ("available", ctypes.c_ulonglong),
                    ("total_page", ctypes.c_ulonglong), ("available_page", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong), ("available_virtual", ctypes.c_ulonglong),
                    ("available_extended", ctypes.c_ulonglong)]
    x = MS(); x.length = ctypes.sizeof(MS)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(x)):
        raise ctypes.WinError()
    return {"total_physical_bytes": int(x.total), "available_physical_bytes": int(x.available),
            "memory_load_pct": int(x.load)}


class FT(ctypes.Structure):
    _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]


def system_ticks() -> tuple[int, int, int]:
    idle, kernel, user = FT(), FT(), FT()
    if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
        raise ctypes.WinError()
    def value(x): return (int(x.high) << 32) + int(x.low)
    return value(idle), value(kernel), value(user)


class Monitor:
    """Sample scorer process-tree working set/CPU plus system CPU/RAM."""
    def __init__(self):
        self.done = threading.Event(); self.samples = []; self.system_cpu = []
        self.tree_cpu = []; self.pid_sets = []
        self.thread = threading.Thread(target=self._run, daemon=True)

    @staticmethod
    def _process_tree():
        """Return descendant PID -> (working set bytes, CPU seconds) for this process."""
        DWORD, LONG = ctypes.c_uint32, ctypes.c_int32
        ULONG_PTR = ctypes.c_size_t
        class Entry(ctypes.Structure):
            _fields_ = [("dwSize", DWORD), ("cntUsage", DWORD), ("th32ProcessID", DWORD),
                        ("th32DefaultHeapID", ULONG_PTR), ("th32ModuleID", DWORD),
                        ("cntThreads", DWORD), ("th32ParentProcessID", DWORD),
                        ("pcPriClassBase", LONG), ("dwFlags", DWORD),
                        ("szExeFile", ctypes.c_wchar * 260)]
        class FileTime(ctypes.Structure):
            _fields_ = [("low", DWORD), ("high", DWORD)]
        class Counters(ctypes.Structure):
            _fields_ = [("cb", DWORD), ("PageFaultCount", DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        kernel = ctypes.windll.kernel32; psapi = ctypes.windll.psapi
        HANDLE = ctypes.c_void_p
        kernel.CreateToolhelp32Snapshot.argtypes = [DWORD, DWORD]
        kernel.CreateToolhelp32Snapshot.restype = HANDLE
        kernel.Process32FirstW.argtypes = [HANDLE, ctypes.POINTER(Entry)]
        kernel.Process32FirstW.restype = ctypes.c_bool
        kernel.Process32NextW.argtypes = [HANDLE, ctypes.POINTER(Entry)]
        kernel.Process32NextW.restype = ctypes.c_bool
        kernel.OpenProcess.argtypes = [DWORD, ctypes.c_bool, DWORD]
        kernel.OpenProcess.restype = HANDLE
        kernel.CloseHandle.argtypes = [HANDLE]
        kernel.GetProcessTimes.argtypes = [HANDLE, ctypes.POINTER(FileTime), ctypes.POINTER(FileTime),
                                           ctypes.POINTER(FileTime), ctypes.POINTER(FileTime)]
        psapi.GetProcessMemoryInfo.argtypes = [HANDLE, ctypes.POINTER(Counters), DWORD]
        snap = kernel.CreateToolhelp32Snapshot(0x00000002, 0)
        invalid = ctypes.c_void_p(-1).value
        if snap == invalid:
            return {}
        entries = {}
        try:
            entry = Entry(); entry.dwSize = ctypes.sizeof(Entry)
            ok = kernel.Process32FirstW(snap, ctypes.byref(entry))
            while ok:
                entries[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                ok = kernel.Process32NextW(snap, ctypes.byref(entry))
        finally:
            kernel.CloseHandle(snap)
        root = os.getpid(); pids = {root}; changed = True
        while changed:
            changed = False
            for pid, parent in entries.items():
                if parent in pids and pid not in pids:
                    pids.add(pid); changed = True
        result = {}
        for pid in pids:
            handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
            if not handle:
                continue
            try:
                counters = Counters(); counters.cb = ctypes.sizeof(Counters)
                creation, exit_time, kernel_time, user_time = FileTime(), FileTime(), FileTime(), FileTime()
                if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                    continue
                if not kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                              ctypes.byref(kernel_time), ctypes.byref(user_time)):
                    continue
                def ticks(v): return (int(v.high) << 32) | int(v.low)
                cpu_seconds = (ticks(kernel_time) + ticks(user_time)) / 10_000_000.0
                result[pid] = (int(counters.WorkingSetSize), cpu_seconds)
            finally:
                kernel.CloseHandle(handle)
        return result

    def _run(self):
        prev_system = None; prev_tree = None; prev_time = None
        while not self.done.is_set():
            try:
                now = time.perf_counter(); mem = memory_snapshot(); ticks = system_ticks()
                tree = self._process_tree()
                self.samples.append({**mem, "tree_working_set_bytes": sum(x[0] for x in tree.values()),
                                     "tree_pid_count": len(tree)})
                self.pid_sets.append(sorted(tree))
                if prev_system is not None and prev_time is not None:
                    di = ticks[0] - prev_system[0]
                    dt = (ticks[1] - prev_system[1]) + (ticks[2] - prev_system[2])
                    if dt > 0:
                        self.system_cpu.append(max(0.0, min(100.0, 100.0 * (dt - di) / dt)))
                if prev_tree is not None and prev_time is not None:
                    cpu_now = sum(x[1] for x in tree.values())
                    cpu_before = sum(x[1] for x in prev_tree.values())
                    self.tree_cpu.append(max(0.0, cpu_now - cpu_before) / max(now - prev_time, 1e-9))
                prev_system, prev_tree, prev_time = ticks, tree, now
            except Exception:
                pass
            self.done.wait(.1)
    def __enter__(self): self.thread.start(); return self
    def __exit__(self, *_): self.done.set(); self.thread.join()
    def result(self):
        peak_tree = max((m["tree_working_set_bytes"] for m in self.samples), default=0)
        first_tree = self.samples[0]["tree_working_set_bytes"] if self.samples else 0
        cpu_cores = sum(self.tree_cpu) / len(self.tree_cpu) if self.tree_cpu else None
        logical = os.cpu_count() or 1
        return {"process_tree_peak_working_set_bytes": peak_tree,
                "process_tree_working_set_baseline_bytes": first_tree,
                "process_tree_peak_increment_bytes": max(0, peak_tree - first_tree),
                "process_tree_peak_cpu_core_equivalents": max(self.tree_cpu, default=None),
                "process_tree_mean_cpu_core_equivalents": cpu_cores,
                "process_tree_mean_cpu_utilization_pct_of_logical_capacity":
                    None if cpu_cores is None else cpu_cores * 100 / logical,
                "process_tree_peak_cpu_utilization_pct_of_logical_capacity":
                    None if not self.tree_cpu else max(self.tree_cpu) * 100 / logical,
                "minimum_system_available_physical_bytes": min((m["available_physical_bytes"] for m in self.samples), default=None),
                "peak_system_memory_load_pct": max((m["memory_load_pct"] for m in self.samples), default=None),
                "mean_system_cpu_utilization_pct": sum(self.system_cpu) / len(self.system_cpu) if self.system_cpu else None,
                "peak_system_cpu_utilization_pct": max(self.system_cpu, default=None),
                "logical_cpu_count": logical,
                "monitor_samples": len(self.samples),
                "observed_process_tree_pids": sorted({pid for pids in self.pid_sets for pid in pids})}


def tree_digest(model) -> str:
    h = hashlib.sha256()
    for i, estimator in enumerate(model.estimators_):
        tree = estimator.tree_
        h.update(int(i).to_bytes(4, "little")); h.update(int(estimator.random_state).to_bytes(8, "little", signed=True))
        for name in ("children_left", "children_right", "feature", "threshold", "impurity",
                     "n_node_samples", "weighted_n_node_samples", "value"):
            a = np.ascontiguousarray(getattr(tree, name))
            h.update(name.encode()); h.update(str(a.dtype).encode()); h.update(repr(a.shape).encode()); h.update(a.view(np.uint8))
    return h.hexdigest()


def disagreement(model, x: np.ndarray) -> np.ndarray:
    votes = np.zeros((len(x), 2), dtype=np.uint16)
    for tree in model.estimators_:
        pred = tree.predict(x).astype(np.uint8, copy=False)
        np.add.at(votes, (np.arange(len(x)), pred), 1)
    return 1.0 - votes.max(axis=1).astype(np.float32) / len(model.estimators_)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--jobs", type=int, nargs="+", default=[1, 2, 4], choices=[1, 2, 4, 8])
    ap.add_argument("--fraction", type=float, default=.02)
    ap.add_argument("--seed", type=int, default=2)
    a = ap.parse_args(); root = a.repo_root.resolve()
    if os.name != "nt": raise SystemExit("RAM/CPU sampling requires Windows")
    if not 0 < a.fraction <= .05: raise SystemExit("fraction must be in (0,.05]")
    if a.output.exists(): raise SystemExit(f"Refusing to overwrite {a.output}")
    data = root / "data/processed/source-e1-cic-lock-1"
    cfg_path = root / "reports/nf_v3_audit/source_e1_cic_config.json"
    stage_path = data / "stage_manifest.json"
    stage = json.loads(stage_path.read_text(encoding="utf-8")); cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    for name in ("train_X.npy", "train_y.npy"):
        meta = stage["files"][name]; path = data / name
        if path.stat().st_size != meta["bytes"] or sha256(path) != meta["sha256"]:
            raise RuntimeError(f"Frozen staged input hash mismatch: {name}")
    x = np.load(data / "train_X.npy", mmap_mode="r"); y = np.load(data / "train_y.npy", mmap_mode="r")
    xte = np.load(data / "source_test_X.npy", mmap_mode="r")
    if x.shape[1] != 46 or x.dtype != np.float32 or y.shape != (len(x),): raise ValueError("Unexpected source schema")
    rng = np.random.default_rng(20261109)
    idx = np.sort(rng.choice(len(y), size=max(1, int(len(y) * a.fraction)), replace=False))
    xs = np.asarray(x[idx], dtype=np.float32); ys = np.asarray(y[idx], dtype=np.uint8)
    qidx = np.linspace(0, len(xte) - 1, min(4096, len(xte)), dtype=np.int64)
    xq = np.asarray(xte[qidx], dtype=np.float32)
    params = dict(cfg["random_forest"]["parameters"]); params.update(random_state=a.seed)
    if 1 not in a.jobs or a.jobs[0] != 1:
        raise SystemExit("Benchmark order must begin with n_jobs=1 for the equivalence reference")
    baseline = {}; runs = []
    for jobs in a.jobs:
        gc.collect()
        before = memory_snapshot()
        if before["available_physical_bytes"] < 2_000_000_000:
            print(json.dumps({"n_jobs": jobs, "skipped": "less than 2 GB system RAM available before fit"}), flush=True)
            break
        wall0 = time.perf_counter(); cpu0 = time.process_time()
        monitor = Monitor()
        with monitor, threadpool_limits(limits=1):
            model = RandomForestClassifier(**{**params, "n_jobs": jobs})
            model.fit(xs, ys)
        elapsed = time.perf_counter() - wall0; process_cpu = time.process_time() - cpu0
        model.n_jobs = 1
        prob = model.predict_proba(xq)[:, 1].astype(np.float32)
        dis = disagreement(model, xq)
        digest = tree_digest(model)
        row = {"n_jobs": jobs, "wall_seconds": elapsed, "main_process_cpu_seconds": process_cpu,
               "main_process_cpu_core_equivalents": process_cpu / max(elapsed, 1e-12),
               "sample_rows": len(ys), "sample_fraction": a.fraction,
               "sample_indices_sha256": hashlib.sha256(idx.tobytes()).hexdigest(),
               "validation_source_test_rows": len(qidx), "validation_offsets_sha256": hashlib.sha256(qidx.tobytes()).hexdigest(),
               "tree_structure_sha256": digest,
               "probability_sha256": hashlib.sha256(prob.tobytes()).hexdigest(),
               "disagreement_sha256": hashlib.sha256(dis.tobytes()).hexdigest(),
               "finite_outputs": bool(np.isfinite(prob).all() and np.isfinite(dis).all()),
               "system_memory_before": before, "system_memory_after": memory_snapshot(),
               "system_resource_samples": monitor.result()}
        row["full_source_train_fit_projection"] = {
            "linear_seconds": elapsed * len(x) / len(ys),
            "nlogn_seconds": elapsed * len(x) / len(ys) *
                (np.log2(max(2, len(x))) / np.log2(max(2, len(ys)))),
            "projection_note": "sample-fit extrapolation only; actual full-seed time is authoritative"}
        if baseline:
            row["speedup_vs_n_jobs_1"] = baseline["wall_seconds"] / elapsed
        else:
            baseline["wall_seconds"] = elapsed
        if jobs == a.jobs[0]:
            baseline = {"tree_structure_sha256": digest, "probability": prob.copy(),
                        "disagreement": dis.copy(), "wall_seconds": elapsed}
            row["equivalence"] = {"reference_n_jobs": None, "tree_structure_exact": True,
                                   "probability_exact": True, "disagreement_exact": True}
        else:
            row["equivalence"] = {"reference_n_jobs": a.jobs[0],
                "tree_structure_exact": digest == baseline["tree_structure_sha256"],
                "probability_exact": bool(np.array_equal(prob, baseline["probability"])),
                "disagreement_exact": bool(np.array_equal(dis, baseline["disagreement"]))}
            row["equivalence"]["probability_max_abs_difference"] = float(np.max(np.abs(prob - baseline["probability"])))
            row["equivalence"]["disagreement_max_abs_difference"] = float(np.max(np.abs(dis - baseline["disagreement"])))
        runs.append(row); print(json.dumps({k: row[k] for k in ("n_jobs", "wall_seconds", "system_resource_samples", "equivalence")}), flush=True)
        if row["system_resource_samples"]["minimum_system_available_physical_bytes"] is not None and row["system_resource_samples"]["minimum_system_available_physical_bytes"] < 2_000_000_000:
            break
    git_head = subprocess.check_output(["git", "-c", "safe.directory=D:/IntrusionDetection",
                                       "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    reference_model_meta = root / "data/processed/target-transfer-v1/cic-to-unsw/verified_models/seed-1/verified_models.json"
    reference_fit = None
    if reference_model_meta.is_file():
        reference_meta = json.loads(reference_model_meta.read_text(encoding="utf-8"))
        reference_fit = {
            "seed": 1,
            "RF_fit_wall_seconds": reference_meta.get("RF_fit_timing", {}).get("wall_seconds"),
            "model_metadata_sha256": sha256(reference_model_meta),
            "source_test_exact": all(reference_meta.get("source_test_verification", {}).get("exact_match", {}).values()),
        }
    report = {"report_id": "cic-rf-internal-njobs-benchmark-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_head, "direction": "cic-to-unsw", "seed": a.seed,
        "source_dataset_sha256": cfg["source_dataset"]["sha256"],
        "source_stage_manifest_sha256": sha256(stage_path), "source_train_sha256": stage["files"]["train_X.npy"]["sha256"],
        "source_train_rows": len(x), "feature_order": cfg["features"]["columns"],
        "parameters": {**params, "n_jobs_values": a.jobs}, "software": {"python": platform.python_version(),
        "numpy": np.__version__, "scikit_learn": sklearn.__version__}, "thread_limits": {"BLAS": 1, "OpenMP": 1},
        "target_access": {"target_file_read": False, "target_labels_read": False},
        "observed_full_scale_reference_fit": reference_fit,
        "measurement_note": "Process-tree working set and CPU plus system-wide CPU and available physical RAM are sampled every 100 ms. Process-tree working set sums may count shared pages more than once; system-wide minimum available RAM is reported separately. Predictions are evaluated with n_jobs=1 so the comparison isolates fit parallelism.",
        "runs": runs}
    report["benchmark_script_sha256"] = sha256(Path(__file__).resolve())
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(a.output), "runs": len(runs), "target_labels_read": False}, indent=2))


if __name__ == "__main__": main()
