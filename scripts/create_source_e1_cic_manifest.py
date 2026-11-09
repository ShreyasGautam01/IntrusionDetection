"""Freeze the CIC source-only E1 implementation and resource decisions."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports/nf_v3_audit"
DATA = ROOT / "data/processed/source-e1-cic-lock-1"
CONFIG = AUDIT / "source_e1_cic_config.json"
STAGE = DATA / "stage_manifest.json"
OUTPUT = AUDIT / "source_e1_cic_experiment_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock-commit", required=True)
    ap.add_argument("--supersede-existing", action="store_true")
    args = ap.parse_args()
    previous = None
    previous_sha256 = None
    if OUTPUT.exists() and not args.supersede_existing:
        raise SystemExit(f"Refusing to overwrite a frozen CIC manifest: {OUTPUT}")
    if OUTPUT.exists():
        previous_sha256 = sha256(OUTPUT)
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if (previous.get("status") != "frozen"
                or previous.get("configuration_id") != "source-e1-cic-lock-1"
                or previous.get("direction") != "cic-to-unsw"):
            raise RuntimeError("Existing CIC manifest is not a compatible frozen manifest")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if head != args.lock_commit or dirty:
        raise RuntimeError("Manifest lock must equal a clean branch HEAD")

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    exact_report_path = AUDIT / "cic_exact_duplicate_compression_benchmark.json"
    merge_report_path = AUDIT / "cic_chunked_exact_merge_benchmark_validated.json"
    smoke_path = AUDIT / "source_e1_smoke_cic-to-unsw_chunked_5signal.json"
    exact_report = json.loads(exact_report_path.read_text(encoding="utf-8"))
    merge_report = json.loads(merge_report_path.read_text(encoding="utf-8"))
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))

    if stage["configuration_sha256"] != sha256(CONFIG):
        raise RuntimeError("CIC stage/config hashes differ")
    if stage["target_file_read"] or stage["target_labels_read"]:
        raise RuntimeError("CIC stage reports target access")
    for filename, meta in stage["files"].items():
        path = DATA / filename
        if not path.exists() or path.stat().st_size != meta["bytes"] or sha256(path) != meta["sha256"]:
            raise RuntimeError(f"CIC staged artifact does not match its stage manifest: {filename}")
    for report in (exact_report, merge_report):
        if report["target_file_read"] or report["target_labels_read"] or report["labels_read"]:
            raise RuntimeError("Feature-distance benchmark reports label or target access")
    check = merge_report["raw_exact_reference_check"]
    if not check["allclose_rtol_1e-12_atol_1e-12"] or check["exact_zero_count"] != check["merged_zero_count"]:
        raise RuntimeError("Exact chunk-merge benchmark did not pass its bounded equivalence check")
    if not smoke["all_finite"] or smoke["target_file_read"] or smoke["target_labels_read"]:
        raise RuntimeError("CIC five-signal smoke evidence is incomplete or reports target access")
    if set(smoke["score_shapes"]) != set(cfg["reliability_signals"]):
        raise RuntimeError("Smoke output does not include all five frozen signals")
    if any(shape != [smoke["rows"]] for shape in smoke["score_shapes"].values()):
        raise RuntimeError("Smoke output shape mismatch")

    source_arrays = {
        name: {"sha256": meta["sha256"], "bytes": meta["bytes"]}
        for name, meta in stage["files"].items()
    }
    code_files = [
        "scripts/run_source_e1_complete.py",
        "scripts/cic_exact_chunked_5nn.py",
        "scripts/finite_value_policy.py",
        "scripts/benchmark_cic_exact_duplicate_compression.py",
        "scripts/benchmark_cic_chunked_exact_merge.py",
        "scripts/create_source_e1_cic_manifest.py",
        "scripts/migrate_cic_exact_distance_checkpoint.py",
    ]
    distance_benchmarks = [
        "reports/nf_v3_audit/cic_distance_bank_benchmark.json",
        "reports/nf_v3_audit/cic_distance_bank_benchmark_validation.json",
        "reports/nf_v3_audit/cic_exact_duplicate_compression_benchmark.json",
        "reports/nf_v3_audit/cic_chunked_exact_merge_benchmark_preliminary_superseded.json",
        "reports/nf_v3_audit/cic_chunked_exact_merge_benchmark_validated.json",
    ]
    manifest = {
        "manifest_id": "source-e1-cic-experiment-v2" if previous else "source-e1-cic-experiment-v1",
        "status": "frozen",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "direction": "cic-to-unsw",
        "lock_commit": args.lock_commit,
        "supersedes_manifest_sha256": previous_sha256,
        "supersedes_lock_commit": previous.get("lock_commit") if previous else None,
        "configuration_id": cfg["configuration_id"],
        "configuration_sha256": sha256(CONFIG),
        "stage_manifest_sha256": sha256(STAGE),
        "source_dataset_sha256": cfg["source_dataset"]["sha256"],
        "source_row_count": cfg["source_dataset"]["row_count"],
        "split_definition": cfg["partition"],
        "split_hashes": source_arrays,
        "feature_count": cfg["features"]["count"],
        "feature_order": cfg["features"]["columns"],
        "feature_registry_sha256": cfg["features"]["feature_registry_sha256"],
        "excluded_metadata_columns": cfg["features"]["excluded_from_predictors_retained_in_registry"],
        "preprocessing": cfg["preprocessing"],
        "reliability_signals": cfg["reliability_signals"],
        "random_forest": cfg["random_forest"],
        "calibration": cfg["calibration"],
        "e1_reporting": cfg["e1_reporting"],
        "distance_execution": {
            "mathematically_equivalent": True,
            "approximation": False,
            "definition": "For each source-test row, mean Euclidean distance in source-train-standardized 46-feature space to the five nearest original CIC source-train rows.",
            "scaler_fit": "All original CIC source-train rows, StandardScaler.partial_fit in 100000-row input-order blocks.",
            "reference_chunk_rows": 500000,
            "reference_chunk_order": "Consecutive source-train input offsets, starting at zero.",
            "duplicate_compression": "Within each chunk, np.unique(axis=0, return_counts=True) over finite float32 feature rows; integer multiplicity is retained exactly.",
            "per_chunk_search": "Fit one sklearn KDTree on the standardized unique rows and retrieve the five nearest distinct vectors per query.",
            "merge": "Merge prior and current chunk candidates by stable ascending distance; retain the best five distinct candidate entries with counts capped at five. Sum the first five original-reference distances by multiplicity and divide by five.",
            "equivalence_argument": "No chunk can contribute a global top-five reference beyond its five nearest distinct vectors; a sixth distinct vector is no closer than five vectors from that chunk. Equal-distance boundary ties have identical distances. Per-row multiplicities reproduce repeated original reference rows.",
            "query_batch_rows": 2048,
            "output_dtype": "float32",
            "kd_tree_leaf_size": 30,
            "distance_threads": 1,
            "distance_shared_across_rf_seeds": True,
            "output_path_ignored_locally": "data/processed/source-e1-cic-lock-1/full_runs/common/feature_space_distance.npy",
            "resume_state": "Two disk-backed top-five distance/count state slots with per-reference-chunk atomic checkpoint.",
        },
        "resource_decision": {
            "full_distance_estimated_hours": merge_report["full_distance_estimate"]["projected_total_hours_excluding_checkpoint_and_output_io"],
            "projected_peak_working_set_bytes": merge_report["full_distance_estimate"]["rough_projected_peak_working_set_bytes"],
            "minimum_available_memory_bytes": 4_200_000_000,
            "rf_concurrent_workers": 1,
            "rf_internal_threads": 1,
            "rf_concurrency_rationale": "The 2%-data two-worker sample improved pair throughput 1.74x, but full-data per-forest memory was not measured. Use one CIC worker to limit peak memory on the 12.07M-row source split.",
        },
        "seeds": list(range(10)),
        "label_use": "CIC labels are source labels for this source-only gate. No UNSW labels or feature data are accessed.",
        "randomness": "No new random sampling is used by the distance implementation. RF and IsolationForest use their frozen run seed; all other transformations and calibration sub-splits follow the source config.",
        "software": exact_report["software"],
        "software_lock_sha256": sha256(ROOT / "uv.lock"),
        "code_sha256": {name: sha256(ROOT / name) for name in code_files},
        "benchmark_reports": {name: sha256(ROOT / name) for name in distance_benchmarks},
        "smoke_evidence": {"path": smoke_path.relative_to(ROOT).as_posix(), "sha256": sha256(smoke_path),
                           "rows": smoke["rows"], "score_shapes": smoke["score_shapes"]},
        "target_access": {"features_read": False, "labels_read": False},
        "scope_exclusions": ["ToN-IoT", "XGBoost", "8-feature sensitivity"],
        "frozen_documents_unchanged": ["research_proposal.md", "methodology_final.md"],
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(OUTPUT), "manifest_id": manifest["manifest_id"],
                      "lock_commit": args.lock_commit, "sha256": sha256(OUTPUT),
                      "distance_estimated_hours": manifest["resource_decision"]["full_distance_estimated_hours"],
                      "projected_peak_working_set_bytes": manifest["resource_decision"]["projected_peak_working_set_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
