"""CIC→UNSW scorer with audited RF fit parallelism and seed checkpoints.

The frozen model parameters, data, calibration and scoring code stay unchanged.
Only RF fitting n_jobs is selected from a committed exact-equivalence benchmark;
the serialized RF is reset to n_jobs=1 for target prediction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import joblib


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-c", "safe.directory=D:/IntrusionDetection",
                                    "-C", str(root), *args], text=True).strip()


def atomic_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", required=True, choices=["cic-to-unsw"])
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--batch-size", type=int, required=True)
    ap.add_argument("--execution-profile", type=Path, required=True)
    ap.add_argument("--wrapped-runner", type=Path, required=True,
                    help="Original manifest-bound scorer path; included for process monitoring")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.manifest.resolve() != root / "reports/nf_v3_audit/target_transfer_manifest_cic_to_unsw.json":
        raise SystemExit("Direction and committed manifest path do not match")
    if args.wrapped_runner.resolve() != root / "scripts/score_target_transfer.py":
        raise SystemExit("Original scorer path does not match repository")
    profile_path = args.execution_profile.resolve()
    if not profile_path.is_relative_to(root):
        raise SystemExit("Execution profile must be inside the repository")
    if git(root, "status", "--porcelain"):
        raise SystemExit("Repository must be clean before resuming the checkpointed scorer")
    git(root, "ls-files", "--error-unmatch", str(profile_path.relative_to(root).as_posix()))
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if (profile.get("direction") != "cic-to-unsw"
            or profile.get("target_labels_read") is not False
            or profile.get("selection_method") != "fastest bitwise-equivalent candidate with at least 2 GB system RAM remaining"):
        raise SystemExit("Execution profile is incomplete or not approved by benchmark criteria")
    unsigned_profile = dict(profile)
    claimed_profile_sha = unsigned_profile.pop("sha256", None)
    canonical_profile = json.dumps(unsigned_profile, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical_profile).hexdigest() != claimed_profile_sha:
        raise SystemExit("Execution profile self-hash is invalid")
    benchmark_path = root / profile["benchmark_report_path"]
    if sha256(benchmark_path) != profile.get("benchmark_report_sha256"):
        raise SystemExit("Benchmark report hash differs from committed execution profile")
    selected_jobs = int(profile["selected_rf_fit_n_jobs"])
    safe_exact = [r for r in json.loads(benchmark_path.read_text(encoding="utf-8"))["runs"]
                  if r["n_jobs"] == selected_jobs
                  and r.get("system_resource_samples", {}).get("minimum_system_available_physical_bytes", 0) >= 2_000_000_000
                  and r.get("equivalence", {}).get("tree_structure_exact") is True
                  and r.get("equivalence", {}).get("probability_exact") is True
                  and r.get("equivalence", {}).get("disagreement_exact") is True]
    if not safe_exact:
        raise SystemExit("Selected RF setting lacks exact output equivalence or memory headroom")

    sys.path.insert(0, str(root / "scripts"))
    sys.path.insert(0, str(root / "src"))
    import benchmark_target_inference as bti  # noqa: E402
    import run_source_e1_complete as e1  # noqa: E402
    import score_target_transfer as scorer  # noqa: E402

    direction = args.direction
    ctx = scorer.resolve_direction(direction)
    actual_data_root = bti.DATA
    original_rf_config = e1.rf_config
    original_fit = bti.fit_or_load_seed
    original_score_one = scorer.score_one_seed
    original_commit = scorer.commit_seed_progress
    execution_by_seed: dict[int, dict] = {}
    runner_hash = sha256(Path(__file__).resolve())

    def profile_from_cache(seed: int) -> dict:
        model_dir = actual_data_root / direction / "verified_models" / f"seed-{seed}"
        metadata_path = model_dir / "verified_models.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        frozen_jobs = int(metadata["identity"]["rf_parameters"]["n_jobs"])
        recorded = metadata.get("RF_execution", {})
        return {
            "seed": seed,
            "RF_fit_n_jobs": int(recorded.get("RF_fit_n_jobs", frozen_jobs)),
            "RF_prediction_n_jobs": int(recorded.get("RF_prediction_n_jobs", frozen_jobs)),
            "BLAS_threads": int(recorded.get("BLAS_threads", 1)),
            "OpenMP_threads": int(recorded.get("OpenMP_threads", 1)),
            "source_test_exact": all(metadata["source_test_verification"]["exact_match"].values()),
            "model_cache_metadata_sha256": sha256(metadata_path),
            "execution_profile_sha256": profile.get("sha256", ""),
        }

    def ensure_model_cache(seed: int) -> dict:
        actual_dir = actual_data_root / direction / "verified_models" / f"seed-{seed}"
        expected_files = ("random_forest.joblib", "calibrator.joblib", "isolation_forest.joblib",
                          "verified_models.json")
        exists = [ (actual_dir / name).is_file() for name in expected_files ]
        if all(exists):
            metadata = json.loads((actual_dir / "verified_models.json").read_text(encoding="utf-8"))
            if metadata.get("RF_execution", {}).get("execution_profile_sha256") not in (None, profile["sha256"]):
                raise RuntimeError(f"Seed {seed} cache belongs to a different execution profile")
            return profile_from_cache(seed)
        if any(exists) or (actual_dir.exists() and any(actual_dir.iterdir())):
            raise RuntimeError(f"Partial verified-model cache exists; preserving {actual_dir}")

        scratch_parent = actual_data_root / direction / "verified_models" / "njobs_scratch"
        scratch_parent.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix=f"seed-{seed}-", dir=scratch_parent))
        original_data = bti.DATA
        old_rf = e1.rf_config
        try:
            bti.DATA = scratch
            e1.rf_config = lambda cfg, run_seed: original_rf_config(  # noqa: E731
                cfg, run_seed
            ).set_params(n_jobs=selected_jobs)
            model, calibrator, isolation, metadata = original_fit(ctx, seed, args.batch_size)
            exact_fit = metadata.get("source_test_verification", {}).get("exact_match", {})
            if not exact_fit or not all(exact_fit.values()):
                raise RuntimeError(f"Seed {seed} parallel fit did not exactly reproduce source E1")
            model.n_jobs = 1
            identity_jobs = int(metadata["identity"]["rf_parameters"]["n_jobs"])
            if identity_jobs != 1:
                raise RuntimeError("Frozen E1 configuration no longer specifies RF n_jobs=1")

            actual_dir.mkdir(parents=True, exist_ok=True)
            artifacts = {
                "random_forest": (model, actual_dir / "random_forest.joblib"),
                "calibrator": (calibrator, actual_dir / "calibrator.joblib"),
                "isolation_forest": (isolation, actual_dir / "isolation_forest.joblib"),
            }
            hashes = {}
            for name, (estimator, output) in artifacts.items():
                tmp = output.with_suffix(output.suffix + ".tmp")
                joblib.dump(estimator, tmp, compress=0)
                os.replace(tmp, output)
                hashes[name] = sha256(output)
            metadata["model_sha256"] = hashes
            metadata["RF_execution"] = {
                "RF_fit_n_jobs": selected_jobs,
                "RF_prediction_n_jobs": 1,
                "frozen_config_n_jobs": 1,
                "BLAS_threads": 1,
                "OpenMP_threads": 1,
                "random_state": seed,
                "fit_source_test_exact_match": exact_fit,
                "fit_source_test_rows": metadata["source_test_verification"]["rows_verified"],
                "benchmark_report_sha256": profile["benchmark_report_sha256"],
                "execution_profile_sha256": profile["sha256"],
                "runner_sha256": runner_hash,
            }
            atomic_json(actual_dir / "verified_models.json", metadata)
            return profile_from_cache(seed)
        finally:
            bti.DATA = original_data
            e1.rf_config = old_rf
            shutil.rmtree(scratch, ignore_errors=True)

    def score_one(ctx_arg, seed, manifest_sha, target_features, feature_meta,
                  distance, distance_meta, batch_rows):
        execution_by_seed[seed] = ensure_model_cache(seed)
        return original_score_one(ctx_arg, seed, manifest_sha, target_features,
                                  feature_meta, distance, distance_meta, batch_rows)

    def commit_progress(path, payload, seed, direction_arg):
        profiles = {}
        for record in payload.get("completed_seeds", []):
            s = int(record["seed"])
            profiles[s] = execution_by_seed.get(s) or profile_from_cache(s)
            record["RF_execution"] = profiles[s]
        payload["RF_execution_amendment"] = {
            "benchmark_report_sha256": profile["benchmark_report_sha256"],
            "execution_profile_sha256": profile["sha256"],
            "runner_sha256": runner_hash,
            "RF_fit_n_jobs_for_new_refits": selected_jobs,
            "RF_prediction_n_jobs": 1,
            "BLAS_threads": 1,
            "OpenMP_threads": 1,
            "target_labels_read": False,
        }
        return original_commit(path, payload, seed, direction_arg)

    bti.DATA = actual_data_root
    scorer.score_one_seed = score_one
    scorer.commit_seed_progress = commit_progress
    scorer.run(direction, args.manifest, args.batch_size)


if __name__ == "__main__":
    main()
