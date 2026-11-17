from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED_DIRECTIONS = {"unsw-to-cic", "cic-to-unsw"}
EXPECTED_SIGNALS = {
    "confidence",
    "random_forest_disagreement",
    "feature_space_distance",
    "split_conformal",
    "isolation_forest",
}
EXPECTED_SEEDS = set(range(10))
PRIMARY_METRICS = {"attack_miss_auprc", "capture_0.05"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def add_failure(failures: list[str], message: str) -> None:
    failures.append(message)


def add_warning(warnings: list[str], message: str) -> None:
    warnings.append(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports" / "nf_v3_audit"

    required = [
        reports / "FINAL_ANALYSIS_AUDIT.json",
        reports / "analysis_per_seed_all_metrics.csv",
        reports / "analysis_aggregate.csv",
        reports / "analysis_paired_statistics.csv",
        reports / "analysis_calibration_conformal.csv",
        root / "PAPER_PRODUCTION_PLAN.md",
        root / "PAPER_RESEARCH_HARNESS.md",
        root / "PAPER_CLAIM_EVIDENCE_MATRIX.md",
    ]

    failures: list[str] = []
    warnings: list[str] = []

    for path in required:
        if not path.exists():
            add_failure(failures, f"Missing required artifact: {path}")

    if failures:
        print("PAPER HARNESS: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1

    audit = json.loads((reports / "FINAL_ANALYSIS_AUDIT.json").read_text(encoding="utf-8"))

    if audit.get("pass") is not True:
        add_failure(failures, "FINAL_ANALYSIS_AUDIT.json does not report pass=true.")
    if audit.get("issues") not in ([], None):
        add_failure(failures, f"Integrity audit reports issues: {audit.get('issues')}")
    for key in (
        "target_labels_used_for_fitting",
        "target_labels_used_for_tuning",
        "target_labels_used_for_recalibration",
        "target_labels_used_for_score_construction",
    ):
        if audit.get(key) is not False:
            add_failure(failures, f"Target-label firewall violation or missing proof: {key}")

    rows = read_csv(reports / "analysis_per_seed_all_metrics.csv")
    directions = {row["direction"] for row in rows}
    signals = {row["signal"] for row in rows}
    seeds = {int(row["seed"]) for row in rows}

    if directions != EXPECTED_DIRECTIONS:
        add_failure(failures, f"Unexpected transfer directions: {sorted(directions)}")
    if signals != EXPECTED_SIGNALS:
        add_failure(failures, f"Unexpected primary signals: {sorted(signals)}")
    if seeds != EXPECTED_SEEDS:
        add_failure(failures, f"Unexpected seed set: {sorted(seeds)}")

    counts = Counter((row["direction"], row["signal"], int(row["seed"])) for row in rows)
    duplicates = [key for key, count in counts.items() if count != 1]
    if duplicates:
        add_failure(failures, f"Missing/duplicated seed records: {duplicates[:10]}")

    aggregate = read_csv(reports / "analysis_aggregate.csv")
    aggregate_keys = {
        (row["direction"], row["signal"], row["metric"])
        for row in aggregate
    }
    for direction in sorted(EXPECTED_DIRECTIONS):
        for signal in sorted(EXPECTED_SIGNALS):
            for metric in sorted(PRIMARY_METRICS):
                if (direction, signal, metric) not in aggregate_keys:
                    add_failure(
                        failures,
                        f"Missing primary aggregate: {direction}/{signal}/{metric}",
                    )

    for row in aggregate:
        if row["metric"] in PRIMARY_METRICS:
            if int(row["n"]) != 10:
                add_failure(
                    failures,
                    f"Primary aggregate does not use ten seeds: {row}",
                )
            try:
                value = float(row["mean"])
            except ValueError:
                add_failure(failures, f"Non-numeric aggregate mean: {row}")
                continue
            if not 0.0 <= value <= 1.0:
                add_failure(failures, f"Primary metric outside [0,1]: {row}")

    paired = read_csv(reports / "analysis_paired_statistics.csv")
    for row in paired:
        try:
            n = int(row["n"])
            p = float(row["exact_sign_flip_p_two_sided"])
            low = float(row["bootstrap_ci_low"])
            high = float(row["bootstrap_ci_high"])
        except (KeyError, ValueError) as exc:
            add_failure(failures, f"Malformed paired-statistics row: {row} ({exc})")
            continue
        if n != 10:
            add_failure(failures, f"Paired comparison without ten matched seeds: {row}")
        if not 0.0 <= p <= 1.0:
            add_failure(failures, f"Invalid p-value: {row}")
        if low > high:
            add_failure(failures, f"Bootstrap CI is reversed: {row}")

    calibration = read_csv(reports / "analysis_calibration_conformal.csv")
    conformal_blockers = []
    for row in calibration:
        for field in ("target_ambiguity_rate", "target_mean_prediction_set_size"):
            value_text = row.get(field, "")
            if value_text == "":
                continue
            try:
                value = float(value_text)
            except ValueError:
                conformal_blockers.append(
                    f"Non-numeric conformal diagnostic {field}: {row}"
                )
                continue
            if field == "target_ambiguity_rate" and not 0.0 <= value <= 1.0:
                conformal_blockers.append(
                    f"Impossible target ambiguity rate {value} in {row['direction']} seed {row['seed']}"
                )
        if not row.get("conformal_quantile"):
            conformal_blockers.append(
                f"Missing conformal quantile in {row['direction']} seed {row['seed']}"
            )
        if not row.get("target_empirical_coverage"):
            conformal_blockers.append(
                f"Missing target empirical coverage in {row['direction']} seed {row['seed']}"
            )

    if conformal_blockers:
        add_warning(
            warnings,
            "Conformal/calibration diagnostics are not publication-ready. "
            "Do not make coverage, ambiguity-rate, or quantile claims until "
            "the implementation and saved provenance are validated.",
        )
        for item in conformal_blockers[:8]:
            add_warning(warnings, item)

    result = {
        "pass": not failures,
        "publication_ready_for_primary_results": not failures,
        "conformal_claims_ready": not conformal_blockers,
        "failures": failures,
        "warnings": warnings,
    }

    print(json.dumps(result, indent=2))

    if failures:
        return 1

    if warnings:
        print("PAPER HARNESS: PRIMARY RESULTS PASS; SECONDARY CLAIM GATES REMAIN.")
        return 0

    print("PAPER HARNESS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
