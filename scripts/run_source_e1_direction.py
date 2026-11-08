"""Direction-aware source E1 staging/configuration and bounded smoke runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DIRECTIONS = {
    "unsw-to-cic": {
        "source_dataset": "NF-UNSW-NB15-v3", "target_dataset": "NF-CSE-CIC-IDS2018-v3",
        "config": ROOT / "reports/nf_v3_audit/source_e1_config.json",
        "data": ROOT / "data/processed/source-e1-lock-1",
        "stage_script": SCRIPTS / "stage_source_e1.py",
    },
    "cic-to-unsw": {
        "source_dataset": "NF-CSE-CIC-IDS2018-v3", "target_dataset": "NF-UNSW-NB15-v3",
        "config": ROOT / "reports/nf_v3_audit/source_e1_cic_config.json",
        "data": ROOT / "data/processed/source-e1-cic-lock-1",
        "stage_script": SCRIPTS / "stage_source_e1_cic.py",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def resolve_direction(direction: str) -> tuple[dict, dict]:
    try: spec = DIRECTIONS[direction]
    except KeyError as exc: raise ValueError(f"Unsupported source direction: {direction}") from exc
    if not spec["config"].is_file(): raise FileNotFoundError(f"Direction config is missing: {spec['config']}")
    cfg = json.loads(spec["config"].read_text(encoding="utf-8"))
    if cfg["source_dataset"]["name"] != spec["source_dataset"] or cfg["target"]["dataset"] != spec["target_dataset"]:
        raise ValueError("Direction registry does not match config source/target datasets")
    return spec, cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction", required=True, choices=sorted(DIRECTIONS))
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true", help="Create the direction's source-only arrays (never overwrite)")
    mode.add_argument("--smoke", action="store_true", help="Run the five-signal source-only pipeline on bounded class-present samples")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output", type=Path, default=None)
    args = ap.parse_args()
    spec, cfg = resolve_direction(args.direction)
    if args.stage:
        if spec["data"].exists():
            raise SystemExit(f"Refusing to overwrite existing stage: {spec['data']}")
        subprocess.run([sys.executable, str(spec["stage_script"])], cwd=ROOT, check=True)
        return
    if args.seed not in cfg["random_forest"]["seeds"]:
        raise SystemExit("Smoke seed must be declared in the direction config")
    stage_path = spec["data"] / "stage_manifest.json"
    if not stage_path.is_file(): raise SystemExit(f"Source stage is missing: {stage_path}")
    stage = json.loads(stage_path.read_text(encoding="utf-8"))
    if stage.get("configuration_id") != cfg["configuration_id"]:
        raise SystemExit("Source stage/configuration identity mismatch")
    if stage.get("feature_order") != cfg["features"]["columns"] or len(cfg["features"]["columns"]) != 46:
        raise SystemExit("Source stage feature order differs from the frozen 46-feature config")
    if stage.get("target_file_read") or stage.get("target_labels_read"):
        raise SystemExit("Source smoke refuses a stage that claims target access")
    for filename, metadata in stage["files"].items():
        path = spec["data"] / filename
        if path.stat().st_size != metadata["bytes"] or sha256(path) != metadata["sha256"]:
            raise SystemExit(f"Source stage hash mismatch: {filename}")

    sys.path.insert(0, str(SCRIPTS))
    import run_source_e1_complete as runner
    runner.DATA = spec["data"]
    runner.CONFIG_PATH = spec["config"]
    runner.RUNS = spec["data"] / "full_runs"
    runner.COMMON = runner.RUNS / "common"
    runner.LOG = spec["data"] / "runlogs" / f"{cfg['configuration_id']}-smoke.log"
    result = runner.run_seed(args.seed, smoke=True)
    result.update({"report_id": "directional-source-e1-five-signal-smoke-1",
                   "direction": args.direction, "configuration_id": cfg["configuration_id"],
                   "config_sha256": sha256(spec["config"]), "stage_manifest_sha256": sha256(stage_path),
                   "source_dataset": spec["source_dataset"], "target_dataset": spec["target_dataset"],
                   "source_sha256": cfg["source_dataset"]["sha256"],
                   "signal_definitions": cfg["reliability_signals"],
                   "target_file_read": False, "target_labels_read": False,
                   "smoke_selection": "input-order-preserving first 2,500 rows per class for source train and first 1,000 per class for calibration/source test; labels used only to ensure both classes are present in the plumbing sample",
                   "note": "Bounded source-only pipeline smoke; RF, calibration, conformal, Isolation Forest, and exact 5-NN distance run on deterministic class-present samples. The smoke source-test sample had zero detector errors/misses, so error and attack-miss ranking metrics are not interpreted; scores and metrics are not final E1 results."})
    out = args.output or ROOT / "reports/nf_v3_audit" / f"source_e1_smoke_{args.direction}_seed{args.seed}.json"
    if out.exists(): raise SystemExit(f"Refusing to overwrite smoke evidence: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "seed": args.seed, "rows": result["rows"],
                      "signals": list(result["score_shapes"]), "all_finite": result["all_finite"],
                      "target_file_read": False, "target_labels_read": False}, indent=2))


if __name__ == "__main__": main()
