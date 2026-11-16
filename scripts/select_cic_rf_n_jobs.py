"""Choose the fastest safe, bitwise-equivalent CIC RF fit profile."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

METHOD = "fastest bitwise-equivalent candidate with at least 2 GB system RAM remaining"
MIN_RAM = 2_000_000_000
MIN_PARALLEL_SPEEDUP = 1.20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def exact_and_safe(record: dict) -> bool:
    memory = record.get("system_resource_samples", {}).get("minimum_system_available_physical_bytes")
    equiv = record.get("equivalence", {})
    return bool(memory is not None and memory >= MIN_RAM
                and record.get("finite_outputs") is True
                and equiv.get("tree_structure_exact") is True
                and equiv.get("probability_exact") is True
                and equiv.get("disagreement_exact") is True)


def fmt(value, decimals: int = 1) -> str:
    return "n/a" if value is None else f"{value:.{decimals}f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--markdown", type=Path, required=True)
    args = ap.parse_args()
    report = json.loads(args.benchmark.read_text(encoding="utf-8"))
    if report.get("report_id") != "cic-rf-internal-njobs-benchmark-v1":
        raise SystemExit("Unexpected RF benchmark report")
    if report.get("target_access") != {"target_file_read": False, "target_labels_read": False}:
        raise SystemExit("Benchmark did not keep target data sealed")
    runs = report.get("runs", [])
    baseline = next((r for r in runs if r.get("n_jobs") == 1), None)
    if baseline is None or not exact_and_safe(baseline):
        raise SystemExit("No valid, resource-safe n_jobs=1 benchmark reference")
    faster = [r for r in runs if r.get("n_jobs") in (2, 4)
              and exact_and_safe(r)
              and baseline["wall_seconds"] / r["wall_seconds"] >= MIN_PARALLEL_SPEEDUP]
    selected = min(faster, key=lambda r: r["wall_seconds"]) if faster else baseline
    report_relative = args.benchmark.resolve().as_posix()
    profile = {
        "profile_id": "cic-to-unsw-rf-fit-parallelism-v1",
        "direction": "cic-to-unsw",
        "selected_rf_fit_n_jobs": int(selected["n_jobs"]),
        "RF_prediction_n_jobs": 1,
        "frozen_config_n_jobs": 1,
        "BLAS_threads": 1,
        "OpenMP_threads": 1,
        "selection_method": METHOD,
        "selection_thresholds": {
            "minimum_system_available_physical_bytes": MIN_RAM,
            "minimum_parallel_speedup_vs_n_jobs_1": MIN_PARALLEL_SPEEDUP,
        },
        "selected_benchmark_wall_seconds": selected["wall_seconds"],
        "selected_speedup_vs_n_jobs_1": baseline["wall_seconds"] / selected["wall_seconds"],
        "selected_tree_structure_sha256": selected["tree_structure_sha256"],
        "selected_equivalence": selected["equivalence"],
        "selected_minimum_available_physical_bytes":
            selected["system_resource_samples"]["minimum_system_available_physical_bytes"],
        "source_dataset_sha256": report["source_dataset_sha256"],
        "source_stage_manifest_sha256": report["source_stage_manifest_sha256"],
        "source_train_sha256": report["source_train_sha256"],
        "feature_order": report["feature_order"],
        "benchmark_report_path": "reports/nf_v3_audit/cic_rf_n_jobs_benchmark.json",
        "benchmark_report_sha256": sha256(args.benchmark),
        "benchmark_commit": report["git_commit"],
        "target_labels_read": False,
        "full_seed_source_e1_verification_required": True,
        "failure_policy": "If any full-seed refit fails exact source-E1 verification, stop the parallel runner and resume remaining seeds with frozen n_jobs=1.",
    }
    canonical = json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
    profile["sha256"] = hashlib.sha256(canonical).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    rows = []
    for run in runs:
        resources = run.get("system_resource_samples", {})
        equivalence = run.get("equivalence", {})
        rows.append(
            f"| {run['n_jobs']} | {run['wall_seconds']:.2f} | "
            f"{resources.get('process_tree_peak_working_set_bytes', 0) / 1e9:.2f} GB | "
            f"{resources.get('minimum_system_available_physical_bytes', 0) / 1e9:.2f} GB | "
            f"{fmt(resources.get('process_tree_mean_cpu_utilization_pct_of_logical_capacity'))}% | "
            f"{str(equivalence.get('tree_structure_exact'))} / "
            f"{str(equivalence.get('probability_exact'))} / "
            f"{str(equivalence.get('disagreement_exact'))} |"
        )
    reference = report.get("observed_full_scale_reference_fit") or {}
    reference_seconds = reference.get("RF_fit_wall_seconds")
    estimate = None if reference_seconds is None else reference_seconds / profile["selected_speedup_vs_n_jobs_1"]
    lines = [
        "# CIC RF `n_jobs` Equivalence and Execution Decision",
        "",
        f"Benchmark report SHA-256: `{profile['benchmark_report_sha256']}`.",
        f"Source dataset SHA-256: `{profile['source_dataset_sha256']}`.",
        f"Source stage SHA-256: `{profile['source_stage_manifest_sha256']}`.",
        "",
        "| RF fit `n_jobs` | Sample fit seconds | Peak process-tree working set | Minimum free physical RAM | Mean machine CPU utilization | Tree / probability / disagreement exact |",
        "|---:|---:|---:|---:|---:|:---|",
        *rows,
        "",
        f"Selected fit setting: **`n_jobs={profile['selected_rf_fit_n_jobs']}`** "
        f"({profile['selected_speedup_vs_n_jobs_1']:.2f}× sampled speedup; "
        f"{profile['selected_minimum_available_physical_bytes'] / 1e9:.2f} GB minimum free RAM).",
        "",
        "The selection required identical tree structures, probabilities, and RF disagreement, finite outputs, at least 2 GB free system RAM, and at least 1.20× speedup for any parallel setting. The frozen RF configuration remains `n_jobs=1`; the selected value is recorded as an execution-only fit override. Serialized models use `n_jobs=1` for prediction. Every full-seed refit must still reproduce that seed's source E1 test arrays exactly before target scoring.",
        "",
        f"Observed seed-1 full-source fit: {reference_seconds if reference_seconds is not None else 'unavailable'} seconds. "
        + (f"Using the bounded measured speedup as a projection gives about {estimate / 3600:.2f} hours for one parallel full-source fit; this is an estimate, not a guarantee." if estimate is not None else "No full-source runtime projection was available."),
        "",
        "Target files and labels were not read by the benchmark. `target_labels_read` is false.",
        "",
    ]
    args.markdown.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"selected_rf_fit_n_jobs": profile["selected_rf_fit_n_jobs"],
                      "speedup_vs_n_jobs_1": profile["selected_speedup_vs_n_jobs_1"],
                      "minimum_available_ram": profile["selected_minimum_available_physical_bytes"],
                      "profile_sha256": profile["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
