"""Validate and migrate a resumable CIC exact-distance checkpoint to manifest v2."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_source_e1_complete as runner  # noqa: E402


def main() -> None:
    runner.configure_direction("cic-to-unsw")
    config = json.loads(runner.CONFIG_PATH.read_text(encoding="utf-8"))
    manifest_sha, lock_commit = runner.require_cic_manifest(config)
    common = runner.COMMON
    checkpoint_path = common / "feature_space_distance.checkpoint.json"
    if not checkpoint_path.exists():
        raise RuntimeError("No in-progress CIC distance checkpoint exists")
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "reports/nf_v3_audit/source_e1_cic_experiment_manifest.json").read_text(encoding="utf-8"))
    completed = int(checkpoint.get("completed_chunks", -1))
    active = int(checkpoint.get("active_slot", -1))
    if completed < 1 or active not in (0, 1):
        raise RuntimeError("Invalid completed-chunk count or active state slot")
    if checkpoint.get("experiment_manifest_sha256") != manifest.get("supersedes_manifest_sha256"):
        raise RuntimeError("Checkpoint does not point to the manifest being superseded")
    if checkpoint.get("manifest_lock_commit") != manifest.get("supersedes_lock_commit"):
        raise RuntimeError("Checkpoint lock commit does not match the superseded manifest")
    for key, expected in {
        "configuration_id": config["configuration_id"],
        "config_sha256": runner.sha256(runner.CONFIG_PATH),
        "stage_manifest_sha256": runner.sha256(runner.DATA / "stage_manifest.json"),
        "train_X_sha256": runner.sha256(runner.DATA / "train_X.npy"),
        "source_test_X_sha256": runner.sha256(runner.DATA / "source_test_X.npy"),
    }.items():
        if checkpoint.get(key) != expected:
            raise RuntimeError(f"Checkpoint input identity mismatch: {key}")
    records = checkpoint.get("chunk_records", [])
    if len(records) != 2 * completed:
        raise RuntimeError("Checkpoint does not have the expected duplicated-record layout")
    recovered = []
    for chunk_id in range(completed):
        first, duplicate = records[2 * chunk_id:2 * chunk_id + 2]
        if first != duplicate or first.get("chunk_id") != chunk_id:
            raise RuntimeError(f"Duplicated checkpoint records do not match for chunk {chunk_id}")
        recovered.append(first)

    query_rows = int(checkpoint["query_rows"])
    for state_name, dtype, shape in (
        (f"top5_distances_state_{active}.npy", np.float64, (query_rows, 5)),
        (f"top5_counts_state_{active}.npy", np.int32, (query_rows, 5)),
    ):
        state_path = common / state_name
        state = np.load(state_path, mmap_mode="r")
        if state.shape != shape or state.dtype != dtype:
            raise RuntimeError(f"Active distance state shape/dtype mismatch: {state_name}")
        for start in range(0, query_rows, 100_000):
            end = min(start + 100_000, query_rows)
            values = state[start:end]
            if dtype == np.float64 and not np.isfinite(values).all():
                raise RuntimeError("Active top-five distance state contains non-finite values")
            if dtype == np.int32 and (np.any(values < 0) or np.any(values.sum(axis=1, dtype=np.int64) < 5)):
                raise RuntimeError("Active top-five multiplicity state is incomplete")
        state._mmap.close()

    old_sha = checkpoint["experiment_manifest_sha256"]
    checkpoint["chunk_records"] = recovered
    checkpoint["experiment_manifest_sha256"] = manifest_sha
    checkpoint["manifest_lock_commit"] = lock_commit
    migrations = list(checkpoint.get("checkpoint_migrations", []))
    migrations.append({
        "from_manifest_sha256": old_sha,
        "to_manifest_sha256": manifest_sha,
        "from_lock_commit": manifest["supersedes_lock_commit"],
        "to_lock_commit": lock_commit,
        "deduplicated_chunk_records": completed,
        "validated_active_slot": active,
        "migrated_utc": datetime.now(timezone.utc).isoformat(),
        "distance_definition_changed": False,
    })
    checkpoint["checkpoint_migrations"] = migrations
    checkpoint["updated_utc"] = datetime.now(timezone.utc).isoformat()
    temp = checkpoint_path.with_suffix(checkpoint_path.suffix + ".migration.tmp")
    temp.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, checkpoint_path)
    print(json.dumps({"status": "migrated_and_verified", "completed_chunks": completed,
                      "active_slot": active, "manifest_sha256": manifest_sha,
                      "lock_commit": lock_commit, "checkpoint": str(checkpoint_path)}, indent=2))


if __name__ == "__main__":
    main()
