"""Shared direction and source-only preprocessing helpers for core transfer."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/nf_v3_audit"
REGISTRY = REPORTS / "transfer_feature_registry.csv"
FAMILY_REGISTRY = REPORTS / "transfer_family_registry.csv"
FAMILY_MATRIX = REPORTS / "transfer_family_pair_matrix.csv"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from run_source_e1_direction import DIRECTIONS  # noqa: E402
from ids_research.target_lockbox import iter_target_feature_batches  # noqa: E402


@dataclass(frozen=True)
class DirectionContext:
    direction: str
    config: dict
    config_path: Path
    data_dir: Path
    source_file: Path
    target_file: Path
    source_record: dict
    target_record: dict
    stage_manifest: Path
    source_e1_manifest: Path
    source_e1_results: Path
    feature_order: tuple[str, ...]
    source_e1_seed_root: Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _audit_record(dataset: str) -> dict:
    audit = json.loads((REPORTS / "audit.json").read_text(encoding="utf-8"))
    matches = [row for row in audit["datasets"] if row["dataset"] == dataset]
    if len(matches) != 1:
        raise ValueError(f"Expected one audited dataset record for {dataset}")
    return matches[0]


def resolve_direction(direction: str) -> DirectionContext:
    try:
        spec = DIRECTIONS[direction]
    except KeyError as exc:
        raise ValueError(f"Unsupported transfer direction: {direction}") from exc
    config_path = spec["config"]
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_name = config["source_dataset"]["name"]
    target_name = config["target"]["dataset"]
    source = _audit_record(source_name)
    target = _audit_record(target_name)
    if source["sha256"] != config["source_dataset"]["sha256"]:
        raise ValueError("Direction config and audited source dataset hash differ")
    if len(config["features"]["columns"]) != 46:
        raise ValueError("Core transfer requires the frozen 46-feature E1 representation")
    manifest = (REPORTS / "source_e1_manifest.json" if direction == "unsw-to-cic"
                else REPORTS / "source_e1_cic_experiment_manifest.json")
    results = (REPORTS / "source_e1_final_results.json" if direction == "unsw-to-cic"
               else REPORTS / "source_e1_cic_final_results.json")
    ctx = DirectionContext(
        direction=direction,
        config=config,
        config_path=config_path,
        data_dir=spec["data"],
        source_file=Path(source["file"]),
        target_file=Path(target["file"]),
        source_record=source,
        target_record=target,
        stage_manifest=spec["data"] / "stage_manifest.json",
        source_e1_manifest=manifest,
        source_e1_results=results,
        feature_order=tuple(config["features"]["columns"]),
        source_e1_seed_root=spec["data"] / "full_runs",
    )
    for path in (ctx.source_file, ctx.target_file, ctx.stage_manifest, manifest, results):
        if not path.is_file():
            raise FileNotFoundError(path)
    return ctx


def expected_raw_header(dataset: str) -> tuple[str, ...]:
    with REGISTRY.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["dataset"] == dataset]
    ordered = sorted(rows, key=lambda r: int(r["raw_column_order"]))
    if len(ordered) != 55:
        raise ValueError(f"Expected 55 frozen raw columns for {dataset}")
    return tuple(r["raw_column"] for r in ordered)


def target_feature_batches(ctx: DirectionContext, *, batch_size: int = 8192
                           ) -> Iterator[tuple[int, list[tuple[str, ...]]]]:
    return iter_target_feature_batches(
        ctx.target_file,
        ctx.feature_order,
        batch_size=batch_size,
        expected_header=expected_raw_header(ctx.config["target"]["dataset"]),
    )


def source_replacements(ctx: DirectionContext) -> dict[str, float]:
    policy = ctx.config["preprocessing"]
    replacement_path = ROOT / policy["replacement_values_file"]
    if sha256_file(replacement_path) != policy["replacement_values_sha256"]:
        raise ValueError("Source finite-replacement record hash differs from direction config")
    record = json.loads(replacement_path.read_text(encoding="utf-8"))
    if record.get("source_file_sha256") != ctx.config["source_dataset"]["sha256"]:
        raise ValueError("Finite replacements are not bound to the direction source dataset")
    return {k: float(v) for k, v in record["replacement_values"].items()}


def parse_source_preprocessed_batch(
    rows: list[tuple[str, ...]],
    feature_order: tuple[str, ...],
    replacements: dict[str, float],
) -> np.ndarray:
    values = np.empty((len(rows), len(feature_order)), dtype=np.float32)
    for i, row in enumerate(rows):
        if len(row) != len(feature_order):
            raise ValueError("Feature batch row width differs from the frozen predictor list")
        for j, (name, token) in enumerate(zip(feature_order, row)):
            try:
                values[i, j] = np.nan if not token.strip() else float(token)
            except ValueError as exc:
                raise ValueError(f"Non-numeric target token in predictor {name!r}") from exc
    for col, name in enumerate(feature_order):
        invalid = ~np.isfinite(values[:, col])
        if invalid.any():
            if name not in replacements:
                raise ValueError(f"Target predictor {name!r} is non-finite without a source-fitted replacement")
            values[invalid, col] = replacements[name]
    if not np.isfinite(values).all():
        raise ValueError("Source-fitted finite replacement did not produce a finite target batch")
    return values
