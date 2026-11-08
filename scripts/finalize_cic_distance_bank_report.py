"""Combine first-pass bank-selection evidence with finite-checked revalidation."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/nf_v3_audit/cic_distance_bank_benchmark.json"
VALIDATION = ROOT / "reports/nf_v3_audit/cic_distance_bank_benchmark_validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    first = json.loads(REPORT.read_text(encoding="utf-8"))
    check = json.loads(VALIDATION.read_text(encoding="utf-8"))
    validation_script = ROOT / "scripts/revalidate_cic_distance_bank_benchmark.py"
    generator_script = ROOT / "scripts/benchmark_cic_distance_bank.py"
    check["validation_script_sha256"] = sha256(validation_script)
    check["generator_script_sha256_at_handoff"] = sha256(generator_script)
    check["code_provenance_note"] = (
        "The first-pass generator was an uncommitted working-tree script and its score-aggregation lines were corrected after the run; its exact executed bytes were not archived. "
        "The deterministic selection rule and output offsets were revalidated by the hashed validation script; the original first-pass report hash is retained below. "
        "Use the committed validation script and retained offset-list hashes as the reproducible benchmark evidence."
    )
    VALIDATION.write_text(json.dumps(check, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    validation_hash = sha256(VALIDATION)

    if first.get("report_id") == "cic-source-e1-deterministic-distance-bank-benchmark-validated-1":
        if first.get("preliminary_first_pass_report_sha256") != check["prior_benchmark_report_sha256"]:
            raise RuntimeError("Final report and revalidation first-pass lineage differ")
        first["validation_report_sha256"] = validation_hash
        first["validation_script_sha256"] = check["validation_script_sha256"]
        first["generator_script_sha256_at_handoff"] = check["generator_script_sha256_at_handoff"]
        first["code_provenance_note"] = check["code_provenance_note"]
        REPORT.write_text(json.dumps(first, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(REPORT), "provenance_refreshed": True,
                          "validation_report_sha256": validation_hash}, indent=2))
        return

    if first.get("report_id") != "cic-source-e1-deterministic-distance-bank-benchmark-1":
        raise RuntimeError("Expected a first-pass or final report; refusing overwrite")
    if check["prior_benchmark_report_sha256"] != sha256(REPORT):
        raise RuntimeError("Revalidation does not match the first-pass report hash")

    first_sha = sha256(REPORT)
    first_relative_errors = {}
    for key, value in first["comparisons"].items():
        metrics = value["relative_error_to_bounded_exact_2p4m"]
        first_relative_errors[key] = {
            "metrics": {name: (number if math.isfinite(number) else None)
                        for name, number in metrics.items()},
            "validity": "Not interpreted: per-row relative errors are unstable for zero and near-zero exact scores.",
        }
    merged = {
        **first,
        "report_id": "cic-source-e1-deterministic-distance-bank-benchmark-validated-1",
        "generated_utc": check["generated_utc"],
        "preliminary_first_pass_report_sha256": first_sha,
        "validation_report_sha256": validation_hash,
        "validation_script_sha256": check["validation_script_sha256"],
        "generator_script_sha256_at_handoff": check["generator_script_sha256_at_handoff"],
        "code_provenance_note": check["code_provenance_note"],
        "scaler_fit_all_source_train": check["scaler_fit_all_source_train"],
        "scaler_parameter_sha256": check["scaler_parameter_sha256"],
        "bounded_exact_baseline": check["bounded_exact_baseline"],
        "standardized_bank_transform_k500000": check["standardized_bank_transform_k500000"],
        "comparisons": check["comparisons"],
        "maximum_observed_timed_phase_peak_working_set_bytes": check[
            "maximum_observed_timed_phase_peak_working_set_bytes"],
        "system_memory_before": check["system_memory_before"],
        "system_memory_after": check["system_memory_after"],
        "relative_error_metric_correction": {
            "first_pass_relative_error_values": first_relative_errors,
            "status": "Invalid aggregation at zero/near-zero exact distances; do not interpret. Revalidation recomputed all comparisons and reports finite-checked absolute errors and Spearman correlation.",
            "validated_report": "cic_distance_bank_benchmark_validation.json"},
        "validation_note": check["interpretation_note"],
    }
    REPORT.write_text(json.dumps(merged, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "validated": True,
                      "preliminary_report_sha256": first_sha,
                      "validation_report_sha256": sha256(VALIDATION)}, indent=2))


if __name__ == "__main__":
    main()
