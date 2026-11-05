"""Stream only duration and protocol fields for the 8-feature draft crosswalk.

No target label or family columns are requested or used. Input data are never
rewritten; only feature-value counts are emitted to a JSON audit artifact.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

FEATURES = ("FLOW_DURATION_MILLISECONDS", "PROTOCOL")


def scan(path: Path, chunksize: int) -> dict:
    protocol_counts: Counter[str] = Counter()
    result = {
        "file": str(path),
        "rows": 0,
        "duration_missing": 0,
        "duration_non_numeric": 0,
        "duration_zero": 0,
        "duration_negative": 0,
        "protocol_missing": 0,
        "protocol_non_numeric": 0,
    }
    for chunk in pd.read_csv(
        path,
        usecols=list(FEATURES),
        dtype="string",
        chunksize=chunksize,
        low_memory=False,
    ):
        result["rows"] += len(chunk)
        duration_raw = chunk[FEATURES[0]].str.strip()
        protocol_raw = chunk[FEATURES[1]].str.strip()
        duration = pd.to_numeric(duration_raw, errors="coerce")
        protocol = pd.to_numeric(protocol_raw, errors="coerce")
        result["duration_missing"] += int(duration_raw.isna().sum())
        result["duration_non_numeric"] += int((duration_raw.notna() & duration.isna()).sum())
        result["duration_zero"] += int((duration == 0).sum())
        result["duration_negative"] += int((duration < 0).sum())
        result["protocol_missing"] += int(protocol_raw.isna().sum())
        result["protocol_non_numeric"] += int((protocol_raw.notna() & protocol.isna()).sum())
        protocol_counts.update(protocol_raw.dropna().tolist())
    result["protocol_value_counts"] = dict(sorted(protocol_counts.items(), key=lambda x: int(x[0])))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="UNSW-v3 CSV")
    parser.add_argument("--target", required=True, type=Path, help="CIC2018-v3 CSV")
    parser.add_argument("--output", type=Path, default=Path("reports/nf_v3_audit/representation_input_check.json"))
    parser.add_argument("--chunksize", type=int, default=250_000)
    args = parser.parse_args()
    if args.chunksize < 1:
        parser.error("--chunksize must be positive")
    report = {
        "scope": "Only FLOW_DURATION_MILLISECONDS and PROTOCOL were read; Label and Attack were not requested.",
        "chunksize": args.chunksize,
        "source": scan(args.source, args.chunksize),
        "target": scan(args.target, args.chunksize),
    }
    source_protocols = set(map(int, report["source"]["protocol_value_counts"]))
    target_protocols = set(map(int, report["target"]["protocol_value_counts"]))
    report["protocol_code_comparison"] = {
        "source_distinct_codes": len(source_protocols),
        "target_distinct_codes": len(target_protocols),
        "shared_codes": sorted(source_protocols & target_protocols),
        "source_only_codes": sorted(source_protocols - target_protocols),
        "target_only_codes": sorted(target_protocols - source_protocols),
        "sets_equal": source_protocols == target_protocols,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "source_rows": report["source"]["rows"],
        "source_zero_duration": report["source"]["duration_zero"],
        "source_protocol_distinct_count": len(source_protocols),
        "target_rows": report["target"]["rows"],
        "target_zero_duration": report["target"]["duration_zero"],
        "target_protocol_distinct_count": len(target_protocols),
        "shared_protocol_codes": sorted(source_protocols & target_protocols),
        "source_only_protocol_count": len(source_protocols - target_protocols),
        "target_only_protocol_codes": sorted(target_protocols - source_protocols),
    }, indent=2))


if __name__ == "__main__":
    main()
