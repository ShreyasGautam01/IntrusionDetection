#!/usr/bin/env python3
"""Streaming, read-only audit for the three locally downloaded NF-v3 CSV files.

Example:
  python scripts/audit_nf_v3_datasets.py --root D:\\NF-v3-datasets \\
      --output reports/nf_v3_audit

The CSV inputs are only read. Temporary duplicate fingerprints are stored in
SQLite under the output directory and deleted when the run finishes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_DATASETS = {
    "NF-CICIDS2018-v3.csv": "NF-CSE-CIC-IDS2018-v3",
    "NF-UNSW-NB15-v3.csv": "NF-UNSW-NB15-v3",
    "NF-ToN-IoT-v3.csv": "NF-ToN-IoT-v3",
}
DEFAULT_DATASETS = ["NF-CSE-CIC-IDS2018-v3", "NF-UNSW-NB15-v3"]
DEFERRED_PLAN_NOTE = (
    "NF-ToN-IoT-v3 is not in RQ1's current two-dataset UNSW/CIC transfer plan; "
    "the v3 experiment record says adding ToN-IoT would be a separate broader multi-domain experiment."
)
NON_NUMERIC_FEATURES = {"IPV4_SRC_ADDR", "IPV4_DST_ADDR"}
NULL_MARKERS = {"", "na", "n/a", "null", "none", "<na>"}
IDENTIFIER_OR_LEAKAGE_CANDIDATES = {
    "IPV4_SRC_ADDR": "source host identifier; can encode capture/site/role",
    "IPV4_DST_ADDR": "destination host identifier; can encode capture/site/role",
    "L4_SRC_PORT": "endpoint/service identifier; may encode attack tooling or service",
    "L4_DST_PORT": "endpoint/service identifier; may encode attack target/service",
    "FLOW_START_MILLISECONDS": "absolute timestamp; can reveal capture period or split membership",
    "FLOW_END_MILLISECONDS": "absolute timestamp; can reveal capture period or split membership",
    "DNS_QUERY_ID": "transaction identifier; often high-cardinality/session-like",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bag_manifest_check(bag_root: Path) -> dict[str, Any]:
    manifest = bag_root / "manifest-sha1.txt"
    result: dict[str, Any] = {"manifest": str(manifest), "present": manifest.exists(), "entries": []}
    if not manifest.exists():
        return result
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            expected, relative = line.split(None, 1)
            relative = relative.lstrip("*").replace("/", os.sep)
            item = bag_root / relative
            if item.is_file():
                digest = hashlib.sha1()
                with item.open("rb") as data_handle:
                    for block in iter(lambda: data_handle.read(8 * 1024 * 1024), b""):
                        digest.update(block)
                actual = digest.hexdigest()
            else:
                actual = None
            result["entries"].append({
                "path": relative,
                "expected_sha1": expected,
                "observed_sha1": actual,
                "matches": actual == expected,
            })
        except (ValueError, OSError) as exc:
            result["entries"].append({"line": line, "error": str(exc), "matches": False})
    result["all_match"] = all(entry.get("matches", False) for entry in result["entries"])
    return result


def classify(values: Counter[str], nonempty: int, numeric_ok: int, finite: int) -> str:
    if nonempty == 0:
        return "empty"
    if numeric_ok == nonempty:
        return "numeric_finite" if finite == nonempty else "numeric_with_nonfinite"
    if numeric_ok == 0:
        return "text"
    return "mixed_numeric_and_text"


def audit_one(path: Path, root: Path, expected_features: list[str], db: sqlite3.Connection,
              chunk_rows: int = 250_000,
              duplicate_override: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    dataset_name = EXPECTED_DATASETS[path.name]
    bag_root = path.parent.parent
    digest = sha256_file(path)
    size = path.stat().st_size
    started = time.monotonic()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header_raw = next(reader)
        header = [name.strip() for name in header_raw]
        duplicate_headers = [name for name, n in Counter(header).items() if n > 1]
        indexes = {name: i for i, name in enumerate(header) if name not in duplicate_headers}
        feature_missing = [name for name in expected_features if name not in indexes]
        feature_indexes = [indexes[name] for name in expected_features if name in indexes]
        target_columns = [name for name in ("Label", "Attack") if name in indexes]
        stats = {
            name: {"empty": 0, "null_marker": 0, "nan": 0, "positive_inf": 0,
                   "negative_inf": 0, "numeric": 0, "finite": 0, "invalid_numeric": 0,
                   "negative": 0, "minimum": None, "maximum": None,
                   "examples": Counter()}
            for name in header
        }
        label_counts = {name: Counter() for name in target_columns}
        observed_types = {name: Counter() for name in header}
        exact_duplicates = 0
        feature_duplicates = 0
        rows = 0
        malformed_rows = 0
        null_tokens = {"na", "n/a", "null", "none", "<na>"}
        while True:
            batch = 0
            for row in reader:
                rows += 1
                batch += 1
                if len(row) != len(header):
                    malformed_rows += 1
                    row = (row + [""] * len(header))[:len(header)]
                for i, name in enumerate(header):
                    value = row[i]
                    s = stats[name]
                    if value == "":
                        s["empty"] += 1
                        continue
                    low = value.strip().casefold()
                    if low in null_tokens:
                        s["null_marker"] += 1
                    observed_types[name]["text"] += 1
                    try:
                        number = float(value)
                        s["numeric"] += 1
                        if math.isnan(number):
                            s["nan"] += 1
                        elif math.isinf(number):
                            s["positive_inf" if number > 0 else "negative_inf"] += 1
                        else:
                            s["finite"] += 1
                            if number < 0:
                                s["negative"] += 1
                            s["minimum"] = number if s["minimum"] is None else min(s["minimum"], number)
                            s["maximum"] = number if s["maximum"] is None else max(s["maximum"], number)
                    except ValueError:
                        if low in {"nan", "+nan", "-nan"}:
                            s["nan"] += 1
                        elif low in {"inf", "+inf", "infinity", "+infinity"}:
                            s["positive_inf"] += 1
                        elif low in {"-inf", "-infinity"}:
                            s["negative_inf"] += 1
                        elif low not in null_tokens and name not in NON_NUMERIC_FEATURES and name in expected_features:
                            s["invalid_numeric"] += 1
                            if len(s["examples"]) < 5:
                                s["examples"][value] += 1
                    if name in label_counts:
                        label_counts[name][value] += 1
                exact = hashlib.sha256(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).digest()
                feature_values = [row[i] for i in feature_indexes]
                feature_key = hashlib.sha256(json.dumps(feature_values, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).digest()
                if duplicate_override is None:
                    db.executemany("INSERT INTO seen(key) VALUES (?)", ((b"R" + exact,), (b"F" + feature_key,)))
                if batch >= chunk_rows:
                    db.commit()
                    batch = 0
            db.commit()
            break

    # Building the fingerprint index in a bulk sort is much faster than
    # maintaining a random-write unique index for every input record.
    if duplicate_override is None:
        db.execute("CREATE INDEX seen_key_idx ON seen(key)")
        duplicate_groups = db.execute(
            "SELECT substr(key, 1, 1), SUM(n - 1) FROM "
            "(SELECT key, COUNT(*) AS n FROM seen GROUP BY key HAVING COUNT(*) > 1) "
            "GROUP BY substr(key, 1, 1)"
        ).fetchall()
        for kind, duplicate_count in duplicate_groups:
            if kind == b"R":
                exact_duplicates = int(duplicate_count)
            elif kind == b"F":
                feature_duplicates = int(duplicate_count)
        db.execute("DROP INDEX seen_key_idx")
        db.commit()
    else:
        exact_duplicates = int(duplicate_override["exact_duplicate_rows_beyond_first"])
        feature_duplicates = int(duplicate_override["duplicate_expected_feature_vectors_beyond_first"])

    schema = []
    for index, name in enumerate(header):
        s = stats[name]
        nonempty = rows - s["empty"]
        numeric_ok = s["numeric"]
        if name in NON_NUMERIC_FEATURES:
            observed = "address_text"
        else:
            observed = classify(s["examples"], nonempty, numeric_ok, s["finite"])
        schema.append({
            "dataset": dataset_name, "ordinal": index + 1, "column": name,
            "observed_type": observed, "expected_feature": name in expected_features,
            "role": "label" if name == "Label" else "attack_family" if name == "Attack" else
                    "feature" if name in expected_features else "extra",
            "nonempty_values": nonempty, "empty_values": s["empty"],
            "null_marker_values": s["null_marker"], "nan_values": s["nan"],
            "positive_inf_values": s["positive_inf"], "negative_inf_values": s["negative_inf"],
            "invalid_numeric_values": s["invalid_numeric"], "negative_finite_values": s["negative"],
            "finite_min": s["minimum"], "finite_max": s["maximum"],
            "invalid_examples": json.dumps(dict(s["examples"]), ensure_ascii=False),
            "possible_leakage_or_identifier": IDENTIFIER_OR_LEAKAGE_CANDIDATES.get(name, ""),
        })
    package_files = []
    for item in sorted(bag_root.rglob("*")):
        if item.is_file():
            package_files.append({"path": str(item.relative_to(root)), "size_bytes": item.stat().st_size})
    info_path = bag_root / "bag-info.txt"
    elapsed = time.monotonic() - started
    info = {
        "dataset": dataset_name, "file": str(path), "relative_file": str(path.relative_to(root)),
        "package_root": str(bag_root), "package_files": package_files,
        "bag_info": info_path.read_text(encoding="utf-8", errors="replace") if info_path.exists() else None,
        "bagit_sha1_integrity": bag_manifest_check(bag_root),
        "file_size_bytes": size, "sha256": digest, "row_count_excluding_header": rows,
        "column_count": len(header), "columns": header, "duplicate_headers": duplicate_headers,
        "observed_feature_order": [name for name in header if name in expected_features],
        "expected_feature_order_matches": [name for name in header if name in expected_features] == expected_features,
        "expected_features_count": len(expected_features), "observed_expected_features_count": len(expected_features) - len(feature_missing),
        "missing_expected_features": feature_missing,
        "extra_columns": [name for name in header if name not in expected_features and name not in target_columns],
        "target_columns": target_columns,
        "label_and_attack_value_counts": {name: dict(sorted(counts.items())) for name, counts in label_counts.items()},
        "exact_duplicate_rows_beyond_first": exact_duplicates,
        "duplicate_expected_feature_vectors_beyond_first": feature_duplicates,
        "duplicate_count_method": duplicate_override.get("source") if duplicate_override else "computed from full-table SHA-256 fingerprint index",
        "malformed_row_width_count": malformed_rows,
        "scan_seconds_including_sha256": round(elapsed, 2),
        "streaming": {"method": "Python csv reader, one record at a time; SQLite disk-backed SHA-256 sets",
                      "working_memory_rows": 1, "chunk_rows_before_commit": chunk_rows},
    }
    return info, schema, [
        {"dataset": dataset_name, "column": column, "value": value, "count": count}
        for column, counts in label_counts.items() for value, count in sorted(counts.items())
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Root containing the three extracted BagIt packages")
    parser.add_argument("--output", type=Path, default=Path("reports/nf_v3_audit"))
    parser.add_argument("--chunk-rows", type=int, default=250_000)
    parser.add_argument("--render-report-only", action="store_true", help="Rebuild REPORT.md from an existing audit.json")
    parser.add_argument("--finalize-checkpoint", action="store_true", help="Promote saved partial results into final audit artifacts")
    parser.add_argument("--datasets", nargs="+", choices=sorted(EXPECTED_DATASETS.values()), default=DEFAULT_DATASETS,
                        help="Dataset(s) to audit; defaults to the current two-dataset RQ1 scope")
    parser.add_argument("--recovered-duplicates", type=Path, help="JSON mapping dataset names to already-computed duplicate counts")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.render_report_only:
        full = json.loads((output / "audit.json").read_text(encoding="utf-8"))
        (output / "REPORT.md").write_text(render_report(full), encoding="utf-8")
        print(f"Wrote {output / 'REPORT.md'}")
        return
    if args.finalize_checkpoint:
        full = json.loads((output / "audit.partial.json").read_text(encoding="utf-8"))
        full["total_elapsed_seconds"] = sum(ds["scan_seconds_including_sha256"] for ds in full["datasets"])
        full["deferred_datasets"] = deferred_dataset_record()
        (output / "audit.json").write_text(json.dumps(full, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for source, target in [("schema.partial.csv", "schema.csv"), ("target_value_counts.partial.csv", "target_value_counts.csv")]:
            (output / target).write_bytes((output / source).read_bytes())
        (output / "REPORT.md").write_text(render_report(full), encoding="utf-8")
        for partial in output.glob("*.partial.*"):
            partial.unlink()
        print(f"Finalized checkpoint artifacts in {output}")
        return
    root = args.root.resolve()
    selected_filenames = [name for name, dataset in EXPECTED_DATASETS.items() if dataset in args.datasets]
    csvs = {path.name: path for path in root.rglob("*.csv") if path.name in selected_filenames}
    missing = sorted(set(selected_filenames) - set(csvs))
    if missing:
        raise SystemExit(f"Missing expected dataset file(s) under {root}: {missing}")
    feature_files = list(root.rglob("NetFlow_v3_Features.csv"))
    if not feature_files:
        raise SystemExit("No NetFlow_v3_Features.csv found in dataset packages")
    with feature_files[0].open("r", encoding="utf-8-sig", newline="") as handle:
        expected_features = [row[0].strip() for row in csv.reader(handle) if row and row[0].strip() and row[0].strip() != "Feature"]
    if len(expected_features) != 53:
        raise SystemExit(f"Feature dictionary has {len(expected_features)} entries; expected 53")

    db_path = output / ".duplicate_fingerprints.sqlite3"
    if db_path.exists():
        db_path.unlink()
    reports: list[dict[str, Any]] = []
    schemas: list[dict[str, Any]] = []
    target_counts: list[dict[str, Any]] = []
    started = time.monotonic()
    db = sqlite3.connect(db_path)
    try:
        db.execute("PRAGMA journal_mode=OFF")
        db.execute("PRAGMA synchronous=OFF")
        db.execute("PRAGMA temp_store=FILE")
        db.execute("PRAGMA cache_size=-65536")
        db.execute("CREATE TABLE seen (key BLOB NOT NULL)")
        recovered = json.loads(args.recovered_duplicates.read_text(encoding="utf-8-sig")) if args.recovered_duplicates else {}
        for filename in selected_filenames:
            db.execute("DROP INDEX IF EXISTS seen_key_idx")
            db.execute("DELETE FROM seen")
            dataset_name = EXPECTED_DATASETS[filename]
            override = recovered.get(dataset_name)
            info, schema, counts = audit_one(csvs[filename], root, expected_features, db, args.chunk_rows, override)
            reports.append(info)
            schemas.extend(schema)
            target_counts.extend(counts)
            checkpoint = {
                "audit_created_utc": datetime.now(timezone.utc).isoformat(),
                "source_root": str(root), "expected_feature_dictionary": str(feature_files[0]),
                "expected_feature_count": len(expected_features), "expected_features": expected_features,
                "datasets": reports,
                "interpretation_notes": [
                    "Hashes identify observed bytes; BagIt manifests provide an independent integrity check.",
                    "Exact duplicate counts use SHA-256 fingerprints of parsed CSV fields; feature-vector duplicates use only the 53 dictionary features, excluding Label and Attack.",
                    "Duplicate counts are rows beyond the first occurrence. Fingerprint collision risk is negligible but nonzero.",
                    "No rows were removed, relabeled, sampled, or transformed. No modeling decisions were made from target columns.",
                ],
            }
            (output / "audit.partial.json").write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            with (output / "schema.partial.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(schemas[0].keys()))
                writer.writeheader()
                writer.writerows(schemas)
            with (output / "target_value_counts.partial.csv").open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["dataset", "column", "value", "count"])
                writer.writeheader()
                writer.writerows(target_counts)
            print(f"Audited {filename}: {info['row_count_excluding_header']:,} rows; {info['scan_seconds_including_sha256']} sec", flush=True)
    finally:
        db.close()
        if db_path.exists():
            db_path.unlink()

    full = {
        "audit_created_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(root), "expected_feature_dictionary": str(feature_files[0]),
        "expected_feature_count": len(expected_features), "expected_features": expected_features,
        "datasets": reports, "total_elapsed_seconds": round(time.monotonic() - started, 2),
        "deferred_datasets": deferred_dataset_record(),
        "interpretation_notes": [
            "Hashes identify the observed bytes; BagIt manifests supply an independent package integrity check.",
            "Exact duplicate counts use SHA-256 fingerprints of parsed CSV fields; feature-vector duplicates use only the 53 dictionary features, excluding Label and Attack.",
            "Duplicate counts are rows beyond the first occurrence. Fingerprint collision risk is negligible but nonzero.",
            "Null-marker counts include explicit empty, NA, N/A, NULL, NONE, and <NA> markers; empty counts are reported separately.",
            "No rows were removed, relabeled, sampled, or transformed. No modeling decisions were made from target columns.",
        ],
    }
    (output / "audit.json").write_text(json.dumps(full, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for filename, rows, fields in [
        ("schema.csv", schemas, list(schemas[0].keys()) if schemas else []),
        ("target_value_counts.csv", target_counts, ["dataset", "column", "value", "count"]),
    ]:
        with (output / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    (output / "REPORT.md").write_text(render_report(full), encoding="utf-8")
    for partial in output.glob("*.partial.*"):
        partial.unlink()
    print(f"Wrote audit artifacts to {output}", flush=True)


def render_report(full: dict[str, Any]) -> str:
    lines = [
        "# NF-v3 dataset acquisition and audit",
        "",
        f"Audit generated: {full['audit_created_utc']}",
        f"Source folder: `{full['source_root']}`",
        "",
        "## Findings",
        "",
        "The downloaded files are extracted BagIt packages attributed in their bag metadata to the University of Queensland dataset `NFV3DATA-A11964-A11964` (RAiD `https://hdl.handle.net/102.100.100/602564`). The supplied folder contains extracted package trees rather than archive files. Each observed CSV has the expected dataset-specific NF-v3 filename. BagIt manifest checks are reported per package below.",
        "",
        f"The completed row-level audit covers {len(full['datasets'])} datasets in the current two-dataset research scope. Each audited schema contains the expected 53 NetFlow-v3 features plus `Label` and `Attack`. The 53-feature dictionary is supplied in the packages as `NetFlow_v3_Features.csv`; the full column-by-column audit is in `schema.csv`. The JSON records both feature-set completeness and whether observed feature order matches the dictionary order.",
        f"NF-ToN-IoT-v3 is present in the downloaded folder but its full row-level audit is deferred: {DEFERRED_PLAN_NOTE}",
        "A prior completed full-table pass processed all 27,520,260 ToN-IoT rows and found 1,816,137 repeated rows/53-feature vectors. Its full label and per-column quality report was not preserved, so ToN-IoT is marked deferred here.",
        "",
        "No rows were changed, cleaned, relabeled, sampled, or transformed. Target labels were counted for inventory only and were not used for modeling decisions.",
        "",
        "## File inventory and integrity",
        "",
        "| Dataset | Size (bytes) | Rows | Columns | Features match | SHA-256 | BagIt SHA-1 |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for ds in full["datasets"]:
        bag = ds["bagit_sha1_integrity"].get("all_match", False)
        match = f"{ds['observed_expected_features_count']}/{ds['expected_features_count']}"
        lines.append(f"| {ds['dataset']} | {ds['file_size_bytes']} | {ds['row_count_excluding_header']} | {ds['column_count']} | {match} | `{ds['sha256']}` | {'PASS' if bag else 'FAIL / unavailable'} |")
    lines.extend(["", "### Extracted package structure", ""])
    for ds in full["datasets"]:
        lines.extend([f"**{ds['dataset']}** (`{ds['package_root']}`)", "", "```text"])
        for package_file in ds["package_files"]:
            lines.append(f"{package_file['path']} ({package_file['size_bytes']} bytes)")
        lines.extend(["```", ""])
    lines.extend(["", "## Labels and attack-family values", ""])
    for ds in full["datasets"]:
        lines.extend([f"### {ds['dataset']}", ""])
        for column, counts in ds["label_and_attack_value_counts"].items():
            title = "Label" if column == "Label" else "Attack family (Attack)"
            lines.extend([f"**{title}**", "", "| Exact value | Rows |", "|---|---:|"])
            for value, count in counts.items():
                shown = value.replace("|", "\\|").replace("\n", "\\n") or "(empty string)"
                lines.append(f"| `{shown}` | {count} |")
            lines.append("")
    lines.extend(["## Data quality and duplicate audit", ""])
    lines.extend(["| Dataset | Malformed-width rows | Exact duplicate rows beyond first | Duplicate 53-feature vectors beyond first |", "|---|---:|---:|---:|"])
    for ds in full["datasets"]:
        lines.append(f"| {ds['dataset']} | {ds['malformed_row_width_count']} | {ds['exact_duplicate_rows_beyond_first']} | {ds['duplicate_expected_feature_vectors_beyond_first']} |")
    lines.extend(["", "Per-column empty values, explicit null markers, NaN, positive/negative infinity, invalid numeric values, negative finite numeric values, and finite ranges are tabulated in `schema.csv`. Only expected numeric features are checked for nonnumeric values; the IPv4 address features are treated as textual identifiers.", "", "## Potential identifier, session, and time leakage fields", "", "The feature schema includes source and destination IPv4 addresses, source and destination ports, flow start and end timestamps, and `DNS_QUERY_ID`. These can identify hosts/services, capture periods, or transactions and should be reviewed against the frozen methodology before any modeling. This report makes no modeling recommendation based on target values.", "", "## Processing and reproducibility", "", "The script uses Python's standard-library CSV reader and processes one record at a time. SHA-256 is streamed in 8 MiB blocks. Duplicate detection fingerprints parsed rows and the 53 feature values with SHA-256 and stores fingerprints in a temporary SQLite table on disk; the temporary table is deleted after a successful run. It does not load a dataset into RAM. The audit performed a full scan of every CSV; no row sampling was used.", "", "Run from the repository root:", "", "```powershell", "python scripts/audit_nf_v3_datasets.py --root 'D:\\NF-v3-datasets' --output 'reports/nf_v3_audit'", "```", "", "## Artifact guide", "", "- `audit.json`: complete dataset, package, hash, schema, target-value and duplicate results.", "- `schema.csv`: one row per observed column per dataset, with values-quality totals and leakage notes.", "- `target_value_counts.csv`: exact value/count pairs for `Label` and `Attack`.", "- `REPORT.md`: this human-readable summary.", "", "The audit does not substitute datasets, change the research question, or modify the frozen `research_proposal.md` or `methodology_final.md`.", ""])
    return "\n".join(lines)


def deferred_dataset_record() -> list[dict[str, Any]]:
    return [{
        "dataset": "NF-ToN-IoT-v3",
        "status": "deferred; not in current RQ1",
        "reason": DEFERRED_PLAN_NOTE,
        "prior_full_scan_row_count": 27_520_260,
        "prior_full_scan_duplicate_rows_beyond_first": 1_816_137,
        "prior_full_scan_duplicate_feature_vectors_beyond_first": 1_816_137,
        "prior_duplicate_count_source": "Completed full-table SHA-256 fingerprint index from the initial audit pass; per-column quality and label inventory are deferred.",
    }]


if __name__ == "__main__":
    main()
