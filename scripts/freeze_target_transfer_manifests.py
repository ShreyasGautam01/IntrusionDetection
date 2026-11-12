"""Create the two code-locked core transfer manifests without reading target labels."""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/nf_v3_audit"
sys.path.insert(0, str(ROOT / "scripts"))
from run_source_e1_direction import DIRECTIONS  # noqa: E402
from target_transfer_common import FAMILY_MATRIX, FAMILY_REGISTRY, REGISTRY, resolve_direction, sha256_file  # noqa: E402

MANIFEST_PATHS = {
    "unsw-to-cic": REPORTS / "target_transfer_manifest_unsw_to_cic.json",
    "cic-to-unsw": REPORTS / "target_transfer_manifest_cic_to_unsw.json",
}
GATES = {
    "unsw-to-cic": REPORTS / "SOURCE_E1_GATE_INTERPRETATION.md",
    "cic-to-unsw": REPORTS / "cic_source_e1_gate_interpretation.md",
}
DISTANCE_BENCHMARKS = {
    "unsw-to-cic": REPORTS / "target_exact_distance_benchmark_unsw_to_cic.json",
    "cic-to-unsw": REPORTS / "target_exact_distance_benchmark_cic_to_unsw.json",
}
INFERENCE_BENCHMARKS = {
    "unsw-to-cic": REPORTS / "target_inference_benchmark_unsw_to_cic_seed0.json",
    "cic-to-unsw": REPORTS / "target_inference_benchmark_cic_to_unsw_seed0.json",
}
SMOKE_REPORTS = {
    "unsw-to-cic": REPORTS / "target_transfer_smoke_unsw_to_cic_v2.json",
    "cic-to-unsw": REPORTS / "target_transfer_smoke_cic_to_unsw.json",
}
CODE_PATHS = (
    "scripts/freeze_target_transfer_manifests.py",
    "scripts/score_target_transfer.py",
    "scripts/evaluate_target_transfer.py",
    "scripts/benchmark_target_distance.py",
    "scripts/benchmark_target_inference.py",
    "scripts/target_exact_knn.py",
    "scripts/target_transfer_common.py",
    "scripts/run_source_e1_complete.py",
    "scripts/run_source_e1_direction.py",
    "scripts/benchmark_source_e1_cic.py",
    "scripts/cic_exact_chunked_5nn.py",
    "scripts/finite_value_policy.py",
    "src/ids_research/target_lockbox.py",
    "src/ids_research/transfer_scoring.py",
    "src/ids_research/review_ranking.py",
    "tests/test_transfer_firewall.py",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def build_manifest(direction: str, lock_commit: str) -> dict:
    ctx = resolve_direction(direction)
    gate = GATES[direction]
    gate_text = gate.read_text(encoding="utf-8").casefold()
    if "owner decision" not in gate_text or "accepted" not in gate_text:
        raise ValueError(f"Source E1 gate lacks explicit owner acceptance: {gate}")
    source_hash = sha256_file(ctx.source_file)
    target_hash = sha256_file(ctx.target_file)
    if (source_hash != ctx.config["source_dataset"]["sha256"]
            or target_hash != ctx.target_record["sha256"]):
        raise ValueError(f"Source or target bytes differ from the audited direction: {direction}")
    distance_path = DISTANCE_BENCHMARKS[direction]
    inference_path = INFERENCE_BENCHMARKS[direction]
    smoke_path = SMOKE_REPORTS[direction]
    for path, name in ((distance_path, "distance"), (inference_path, "inference"),
                       (smoke_path, "five-signal smoke")):
        if not path.is_file():
            raise FileNotFoundError(f"Required bounded {name} benchmark is missing: {path}")
        evidence = json.loads(path.read_text(encoding="utf-8"))
        if (evidence.get("direction") != direction
                or evidence.get("source_dataset_sha256") != source_hash
                or evidence.get("target_dataset_sha256") != target_hash
                or evidence.get("target_labels_read") is not False):
            raise ValueError(f"Benchmark evidence does not match the feature-only transfer plan: {path}")
        if name == "five-signal smoke":
            required_smoke_code = {
                "scripts/score_target_transfer.py", "scripts/target_exact_knn.py",
                "scripts/target_transfer_common.py", "src/ids_research/transfer_scoring.py",
            }
            smoke_code = evidence.get("code_sha256", {})
            if (evidence.get("all_finite") is not True
                    or set(evidence.get("signals", [])) != {
                        "confidence", "random_forest_disagreement", "feature_space_distance",
                        "split_conformal", "isolation_forest"}
                    or evidence.get("rows", 0) < 1
                    or not required_smoke_code.issubset(smoke_code)
                    or any(code_hashes.get(relative) != smoke_code.get(relative)
                           for relative in required_smoke_code)):
                raise ValueError("Target five-signal smoke evidence is incomplete, stale, or non-finite")
    config_sha = sha256_file(ctx.config_path)
    stage_sha = sha256_file(ctx.stage_manifest)
    e1_manifest_sha = sha256_file(ctx.source_e1_manifest)
    e1_results_sha = sha256_file(ctx.source_e1_results)
    code_hashes = {relative: sha256_file(ROOT / relative) for relative in CODE_PATHS}
    e1_manifest = json.loads(ctx.source_e1_manifest.read_text(encoding="utf-8"))
    e1_results = json.loads(ctx.source_e1_results.read_text(encoding="utf-8"))
    if (e1_manifest.get("configuration_sha256") != config_sha
            or e1_results.get("manifest_sha256") != e1_manifest_sha
            or e1_results.get("configuration_id") != ctx.config["configuration_id"]
            or e1_results.get("complete_seed_count") != 10
            or e1_results.get("all_per_seed_outputs_integrity_verified") is not True):
        raise ValueError(f"Source E1 completion evidence is not valid for {direction}")
    stage = json.loads(ctx.stage_manifest.read_text(encoding="utf-8"))
    if stage.get("feature_order") != list(ctx.feature_order):
        raise ValueError(f"Source stage feature order differs from E1 for {direction}")
    benchmark_files = (distance_path, inference_path, smoke_path)
    seeds = list(ctx.config["random_forest"]["seeds"])
    if seeds != list(range(10)):
        raise ValueError(f"Frozen source seed set differs from 0–9 for {direction}")
    return {
        "manifest_id": f"target-transfer-{direction}-v1",
        "status": "frozen",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "direction": direction,
        "lock_commit": lock_commit,
        "configuration_id": ctx.config["configuration_id"],
        "source_dataset": ctx.config["source_dataset"]["name"],
        "target_dataset": ctx.config["target"]["dataset"],
        "source_sha256": source_hash,
        "target_sha256": target_hash,
        "source_rows": int(ctx.config["source_dataset"]["row_count"]),
        "target_rows": int(ctx.target_record["row_count_excluding_header"]),
        "config_sha256": config_sha,
        "source_stage_manifest_sha256": stage_sha,
        "source_e1_manifest_sha256": e1_manifest_sha,
        "source_e1_results_sha256": e1_results_sha,
        "source_gate_interpretation_sha256": sha256_file(gate),
        "source_gate_accepted": True,
        "feature_registry_sha256": sha256_file(REGISTRY),
        "family_registry_sha256": sha256_file(FAMILY_REGISTRY),
        "family_pair_matrix_sha256": sha256_file(FAMILY_MATRIX),
        "feature_order": list(ctx.feature_order),
        "feature_registry_roles": {
            "predictors": 46, "identifiers": 5, "split_metadata": 2,
            "binary_target_label": 1, "attack_family_target_label": 1,
        },
        "family_mapping_decision": "Only the documented DoS-to-DoS category is shared; ambiguous and undocumented families remain dataset-local, and unseen-family claims are withheld.",
        "preprocessing": {
            "replacement_values_file": ctx.config["preprocessing"]["replacement_values_file"],
            "replacement_values_sha256": ctx.config["preprocessing"]["replacement_values_sha256"],
            "replacement_fit_partition": "source train only",
            "target_fitted_preprocessing": False,
        },
        "reliability_signals": ctx.config["reliability_signals"],
        "random_forest": ctx.config["random_forest"],
        "seeds": seeds,
        "concurrency": {
            "direction_order": ["unsw-to-cic", "cic-to-unsw"],
            "seed_order": seeds,
            "simultaneous_workers": 1,
            "RF_n_jobs": 1, "IsolationForest_n_jobs": 1,
            "BLAS_threads": 1, "OpenMP_threads": 1,
            "target_scoring_batch_rows_max": 8192,
        },
        "max_target_batch_rows": 8192,
        "distance_parameters": {
            "definition": "Mean Euclidean distance to the five nearest original source-training rows after source-training StandardScaler",
            "exact": True, "neighbors": 5, "metric": "euclidean",
            "algorithm": "scikit-learn KDTree over per-chunk unique rows with integer multiplicities and exact top-five merge",
            "reference_chunk_rows": 500000, "query_batch_rows": 2048,
            "n_jobs": 1, "BLAS_threads": 1, "OpenMP_threads": 1,
            "mathematically_equivalent_duplicate_compression": True,
            "scaler_fit_partition": "source train only",
            "computed_once_per_source_direction": True,
        },
        "model_factorization": {
            "confidence": "RF seed and source-fitted calibrator dependent",
            "random_forest_disagreement": "RF seed dependent",
            "feature_space_distance": "source train/representation dependent, RF seed independent; compute once per direction",
            "split_conformal": "RF seed and source-fitted conformal quantile dependent",
            "isolation_forest": "source train and configured seed dependent; fit once per direction and seed",
        },
        "benchmarks": {path.relative_to(ROOT).as_posix(): sha256_file(path)
                       for path in benchmark_files},
        "benchmark_decision": "Measured exact duplicate-compressed distance is practical as a sequential long single-job computation; no approximation selected.",
        "full_distance_projection_seconds": json.loads(distance_path.read_text(encoding="utf-8"))["full_runtime_projection"],
        "target_labels_read": False,
        "review_budgets": [0.01, 0.05, 0.10],
        "ranking": {
            "selected_rows": "floor(budget * target_rows)",
            "tie_break": "stable ascending input row offset",
            "cutoff_tie_count": "number of full-target scores equal to the selection cutoff",
        },
        "target_evaluation": "locked until both direction manifests are committed and validated",
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit_learn": sklearn.__version__},
        "software_lock_sha256": sha256_file(ROOT / "uv.lock"),
        "code_sha256": code_hashes,
        "smoke_evidence": {"path": smoke_path.relative_to(ROOT).as_posix(),
                            "sha256": sha256_file(smoke_path),
                            "rows": json.loads(smoke_path.read_text(encoding="utf-8"))["rows"],
                            "target_labels_read": False},
        "scope_exclusions": ["ToN-IoT", "XGBoost", "8-feature sensitivity"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.write:
        raise SystemExit("Review generation requires explicit --write")
    status = git("status", "--porcelain")
    if status:
        raise SystemExit(f"Manifest generation requires a clean tracked worktree: {status}")
    frozen_diff = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--quiet", "HEAD", "--",
         "research_proposal.md", "methodology_final.md"], check=False
    )
    if frozen_diff.returncode != 0:
        raise SystemExit("Frozen proposal/methodology documents have a diff; refusing to freeze")
    lock_commit = git("rev-parse", "HEAD")
    for direction, out in MANIFEST_PATHS.items():
        if out.exists():
            raise FileExistsError(f"Refusing to overwrite transfer manifest: {out}")
        manifest = build_manifest(direction, lock_commit)
        out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"path": str(out), "direction": direction,
                          "lock_commit": lock_commit,
                          "manifest_sha256": sha256_file(out),
                          "target_labels_read": False}, indent=2))


if __name__ == "__main__":
    main()
