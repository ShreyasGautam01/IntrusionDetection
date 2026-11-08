"""Stage the CIC source partition for the pre-transfer CIC -> UNSW E1 gate."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports/nf_v3_audit/audit.json"
BASE_CONFIG = ROOT / "reports/nf_v3_audit/source_e1_config.json"
LABEL_COUNTS = ROOT / "reports/nf_v3_audit/target_value_counts.csv"
CONFIG_OUT = ROOT / "reports/nf_v3_audit/source_e1_cic_config.json"
REPLACEMENTS_OUT = ROOT / "reports/nf_v3_audit/cic_train_finite_replacements.json"
DEFAULT_OUT = ROOT / "data/processed/source-e1-cic-lock-1"
PARTS = ("train", "calibration", "source_test")
PART_CODE = {"train": 0, "calibration": 1, "source_test": 2}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def vector_digest(row: list[str], indices: list[int]) -> bytes:
    h = hashlib.sha256()
    for i in indices:
        h.update(row[i].encode("utf-8"))
        h.update(b"\x1f")
    return h.digest()


def assign_part(row: list[str], indices: list[int]) -> str:
    bucket = int.from_bytes(vector_digest(row, indices)[:8], "big") % 100
    return "train" if bucket < 60 else "calibration" if bucket < 80 else "source_test"


def audit_row_count() -> int:
    total = 0
    with LABEL_COUNTS.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["dataset"] == "NF-CSE-CIC-IDS2018-v3" and row["column"] == "Label":
                total += int(row["count"])
    return total


def make_cic_config(base: dict, ds: dict, counts: dict, replacements: dict) -> dict:
    cfg = json.loads(json.dumps(base))
    cfg["configuration_id"] = "source-e1-cic-lock-1"
    cfg["created_utc"] = datetime.now(timezone.utc).isoformat()
    cfg["status"] = "prepared_before_resource_benchmark"
    cfg["scope"] = "NF-CSE-CIC-IDS2018-v3 source-only E1 for the CIC -> UNSW core direction; no target evaluation"
    cfg["source_dataset"] = {
        "name": "NF-CSE-CIC-IDS2018-v3",
        "sha256": ds["sha256"],
        "row_count": int(sum(counts.values())),
    }
    cfg["partition"]["rows"] = counts
    cfg["partition"]["definition"] = (
        "SHA-256 of canonical raw 53-feature strings; first 8 digest bytes interpreted big-endian modulo 100; "
        "train buckets 0-59, calibration 60-79, source_test 80-99"
    )
    cfg["features"]["source"] = "reports/nf_v3_audit/source_e1_config.json; exact locked 46-column order"
    cfg["preprocessing"]["replacement_values_file"] = "reports/nf_v3_audit/cic_train_finite_replacements.json"
    cfg["preprocessing"]["replacement_values_sha256"] = None
    cfg["preprocessing"]["fit_partition"] = "CIC source-train only"
    cfg["preprocessing"]["values"] = replacements
    cfg["preprocessing"]["target_preprocessing"] = "not run"
    cfg["target"] = {
        "dataset": "NF-UNSW-NB15-v3",
        "features_accessed": False,
        "labels_accessed": False,
        "evaluation_unlocked": False,
    }
    cfg["calibration"]["calibration_partition_source"] = "CIC calibration split only"
    cfg["calibration"]["target_recalibration"] = False
    cfg["e1_reporting"]["target_eval_allowed_after_this_run"] = False
    cfg["e1_reporting"]["acceptance_rule"] = (
        "Report CIC source-only stability; target transfer remains locked pending project-level interpretation."
    )
    cfg["method_note"] = (
        "Reverse-direction CIC source-only E1 using the exact 46-feature order and existing five signal definitions. "
        "CIC labels are source labels only for this gate; UNSW is not read."
    )
    cfg["reliability_signals"]["feature_space_distance"]["reference"] = "CIC source-train only"
    cfg["reliability_signals"]["feature_space_distance"]["scaler"] = "StandardScaler fit only on CIC source-train"
    cfg["reliability_signals"]["split_conformal"]["calibration"] = (
        "disjoint conformal_quantile_fit subset of CIC source calibration partition"
    )
    cfg["reliability_signals"]["isolation_forest"]["fit_data"] = "CIC source-train only"
    return cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=None)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--config-output", type=Path, default=CONFIG_OUT)
    ap.add_argument("--replace-output", type=Path, default=REPLACEMENTS_OUT)
    args = ap.parse_args()

    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite existing CIC staging path: {args.output}")
    if args.config_output.exists() or args.replace_output.exists():
        raise SystemExit("Refusing to overwrite an existing CIC config/replacement record; inspect it first")

    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    base = json.loads(BASE_CONFIG.read_text(encoding="utf-8"))
    ds = next(x for x in audit["datasets"] if x["dataset"] == "NF-CSE-CIC-IDS2018-v3")
    source = args.source or Path(ds["file"])
    if not source.is_file():
        raise SystemExit(f"Audited CIC source file not found: {source}")
    expected_sha = ds["sha256"]
    started = time.perf_counter()
    observed_sha = sha256_file(source)
    hash_seconds = time.perf_counter() - started
    if observed_sha != expected_sha:
        raise SystemExit(f"CIC source SHA-256 differs from audit: {observed_sha}")

    expected_rows = audit_row_count()
    if expected_rows <= 0:
        raise SystemExit("Audited CIC Label row count is unavailable")
    expected_features = audit["expected_features"]
    features = base["features"]["columns"]
    replacement_columns = list(base["preprocessing"]["values"])
    replacements_allowed = set(replacement_columns)
    if not set(features).issubset(expected_features):
        raise SystemExit("The locked 46 features are outside the audited 53-feature schema")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.mkdir()
    raw_x_path = args.output / "cic_all_X.float32.tmp"
    raw_y_path = args.output / "cic_all_y.int8.tmp"
    raw_p_path = args.output / "cic_partition.uint8.tmp"
    total = expected_rows
    xraw = np.memmap(raw_x_path, mode="w+", dtype=np.float32, shape=(total, len(features)))
    yraw = np.memmap(raw_y_path, mode="w+", dtype=np.int8, shape=(total,))
    praw = np.memmap(raw_p_path, mode="w+", dtype=np.uint8, shape=(total,))
    replacement_maps = {
        name: np.memmap(args.output / f"{name}.train-finite.float32.tmp", mode="w+", dtype=np.float32, shape=(total,))
        for name in replacement_columns
    }
    replacement_rows = {name: 0 for name in replacement_columns}

    counts = {part: 0 for part in PARTS}
    class_counts = {part: {"0": 0, "1": 0} for part in PARTS}
    nonfinite = {name: {"train": 0, "calibration": 0, "source_test": 0} for name in features}
    calibration_subsplit = {"probability_calibration_fit": 0, "conformal_quantile_fit": 0}
    rows = 0
    feature_pos = {name: j for j, name in enumerate(features)}
    stage_started = time.perf_counter()
    with source.open("r", encoding="utf-8-sig", newline="", buffering=1024 * 1024) as f:
        reader = csv.reader(f)
        header = next(reader)
        if len(header) != len(set(header)):
            raise SystemExit("Duplicate CIC headers prevent safe staging")
        absent = set(expected_features).union(features, {"Label"}).difference(header)
        if absent:
            raise SystemExit(f"Audited/configured CIC columns are absent: {sorted(absent)}")
        index = {name: i for i, name in enumerate(header)}
        hash_indices = [index[name] for name in expected_features]
        feature_indices = [index[name] for name in features]
        label_index = index["Label"]

        for row_no, row in enumerate(reader):
            if row_no >= total:
                raise ValueError("CIC row count exceeds the audited Label count")
            if len(row) != len(header):
                raise ValueError(f"Malformed CIC row width at data row {row_no}")
            part = assign_part(row, hash_indices)
            part_code = PART_CODE[part]
            label = row[label_index].strip()
            if label not in ("0", "1"):
                raise ValueError(f"Unexpected binary CIC Label {label!r} at data row {row_no}")
            values = np.empty(len(features), dtype=np.float32)
            with np.errstate(over="ignore", invalid="ignore"):
                for j, (name, i) in enumerate(zip(features, feature_indices)):
                    token = row[i].strip()
                    try:
                        value = np.float32(float(token))
                    except (ValueError, OverflowError):
                        value = np.float32(np.nan)
                    if not np.isfinite(value):
                        nonfinite[name][part] += 1
                        if name not in replacements_allowed:
                            raise ValueError(
                                f"Unexpected non-finite CIC value in {name} at data row {row_no}; "
                                "do not infer a replacement outside the locked finite policy"
                            )
                        value = np.float32(np.nan)
                    values[j] = value
            xraw[row_no] = values
            yraw[row_no] = int(label)
            praw[row_no] = part_code
            counts[part] += 1
            class_counts[part][label] += 1
            if part == "train":
                for name in replacement_columns:
                    j = feature_pos[name]
                    if np.isfinite(values[j]):
                        pos = replacement_rows[name]
                        replacement_maps[name][pos] = values[j]
                        replacement_rows[name] = pos + 1
            rows += 1
            if rows % 1_000_000 == 0:
                print(f"staging source rows={rows}/{total} elapsed={time.perf_counter()-stage_started:.1f}s", flush=True)

    if rows != total:
        raise ValueError(f"CIC row count differs from audit: observed {rows}, expected {total}")
    xraw.flush()
    yraw.flush()
    praw.flush()
    for value_map in replacement_maps.values():
        value_map.flush()

    medians: dict[str, float] = {}
    fallback: dict[str, bool] = {}
    for name in replacement_columns:
        valid_count = replacement_rows[name]
        missing_train = nonfinite[name]["train"]
        if valid_count:
            # The temporary memmap keeps exact source-train replacement fitting
            # bounded in RAM; only one feature column is copied for its median.
            valid_values = np.asarray(replacement_maps[name][:valid_count], dtype=np.float32)
            medians[name] = float(np.median(valid_values))
            fallback[name] = False
        else:
            medians[name] = 0.0
            fallback[name] = True
        if not missing_train:
            fallback[name] = False

    # Match run_source_e1_complete.cal_mask: calibration membership is derived
    # from the post-replacement canonical float32 feature row bytes.
    cal_indices = np.flatnonzero(praw == PART_CODE["calibration"])
    for offset in range(0, len(cal_indices), 100_000):
        rows_idx = cal_indices[offset:offset + 100_000]
        block = np.asarray(xraw[rows_idx], dtype=np.float32).copy()
        for name, median in medians.items():
            j = features.index(name)
            mask = ~np.isfinite(block[:, j])
            if mask.any():
                block[mask, j] = np.float32(median)
        for row_values in block:
            digest = hashlib.sha256(b"source-e1-cal-v1\x00" + row_values.tobytes()).digest()
            key = int.from_bytes(digest[:8], "big") % 100
            calibration_subsplit["probability_calibration_fit" if key < 50 else "conformal_quantile_fit"] += 1

    cfg = make_cic_config(base, ds, counts, medians)
    cfg["preprocessing"]["replacement_values_sha256"] = None
    cfg["calibration"]["calibration_probability_rows"] = calibration_subsplit["probability_calibration_fit"]
    cfg["calibration"]["conformal_calibration_rows"] = calibration_subsplit["conformal_quantile_fit"]

    replacement_record = {
        "policy": "Replace empty, NaN, and +/-Inf only with the median fitted on CIC source-train rows; 0.0 only if that source column has no finite training values.",
        "source_file_sha256": expected_sha,
        "source_dataset": "NF-CSE-CIC-IDS2018-v3",
        "split_rule": cfg["partition"]["definition"],
        "source_train_rows": counts["train"],
        "replacement_values": medians,
        "nonfinite_counts_by_feature_and_partition": {
            name: counts_by_part for name, counts_by_part in nonfinite.items() if any(counts_by_part.values())
        },
        "fallback_used": fallback,
    }

    args.replace_output.parent.mkdir(parents=True, exist_ok=True)
    args.replace_output.write_text(json.dumps(replacement_record, indent=2) + "\n", encoding="utf-8")
    cfg["preprocessing"]["replacement_values_sha256"] = sha256_file(args.replace_output)
    args.config_output.parent.mkdir(parents=True, exist_ok=True)
    args.config_output.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")

    final_arrays: dict[str, tuple[np.memmap, np.memmap]] = {}
    for part in PARTS:
        final_arrays[part] = (
            np.lib.format.open_memmap(
                args.output / f"{part}_X.npy", mode="w+", dtype=np.float32,
                shape=(counts[part], len(features))
            ),
            np.lib.format.open_memmap(
                args.output / f"{part}_y.npy", mode="w+", dtype=np.int8,
                shape=(counts[part],)
            ),
        )

    write_pos = {part: 0 for part in PARTS}
    for part in PARTS:
        code = PART_CODE[part]
        indices = np.flatnonzero(praw == code)
        out_x, out_y = final_arrays[part]
        for offset in range(0, len(indices), 100_000):
            rows_idx = indices[offset:offset + 100_000]
            block = np.asarray(xraw[rows_idx], dtype=np.float32).copy()
            for name, median in medians.items():
                j = feature_pos[name]
                mask = ~np.isfinite(block[:, j])
                if mask.any():
                    block[mask, j] = np.float32(median)
            out_x[offset:offset + len(rows_idx)] = block
            out_y[offset:offset + len(rows_idx)] = yraw[rows_idx]
        out_x.flush()
        out_y.flush()
        write_pos[part] = len(indices)

    arrays = {}
    for path in sorted(args.output.glob("*.npy")):
        arrays[path.name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}

    stage = {
        "report_id": "source-e1-cic-stage-1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_id": cfg["configuration_id"],
        "configuration_sha256": sha256_file(args.config_output),
        "source_dataset": cfg["source_dataset"],
        "source_file": str(source),
        "source_file_hash_seconds": hash_seconds,
        "source_label_role": "CIC labels used only as source labels for CIC in-domain E1 and the CIC -> UNSW direction",
        "target_file_read": False,
        "target_labels_read": False,
        "split_definition": cfg["partition"]["definition"],
        "partition_rows": write_pos,
        "class_counts": class_counts,
        "calibration_subsplit_rows": calibration_subsplit,
        "feature_order": features,
        "dtype": "float32 features; int8 binary Label",
        "finite_replacements": medians,
        "nonfinite_counts_by_feature_and_partition": {
            name: counts_by_part for name, counts_by_part in nonfinite.items() if any(counts_by_part.values())
        },
        "files": arrays,
    }
    (args.output / "stage_manifest.json").write_text(json.dumps(stage, indent=2) + "\n", encoding="utf-8")

    del final_arrays, xraw, yraw, praw
    for value_map in replacement_maps.values():
        value_map.flush()
        value_map._mmap.close()
    replacement_maps.clear()
    raw_x_path.unlink()
    raw_y_path.unlink()
    raw_p_path.unlink()
    for name in replacement_columns:
        (args.output / f"{name}.train-finite.float32.tmp").unlink()

    print(json.dumps({
        "stage_dir": str(args.output),
        "partition_rows": write_pos,
        "class_counts": class_counts,
        "feature_count": len(features),
        "staged_file_bytes": sum(x["bytes"] for x in arrays.values()),
        "source_file_hash_seconds": hash_seconds,
        "staging_elapsed_seconds": time.perf_counter() - stage_started,
        "target_file_read": False,
        "target_labels_read": False,
    }, indent=2))


if __name__ == "__main__":
    main()
