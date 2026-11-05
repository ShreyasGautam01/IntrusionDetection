"""Create a reviewable primary feature-set proposal from the E0 registry."""
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "feature_registry.csv"
AUDIT = ROOT / "reports/nf_v3_audit/audit.json"
OUT = ROOT / "reports/nf_v3_audit"
SOURCE = "NF-UNSW-NB15-v3"
TARGET = "NF-CSE-CIC-IDS2018-v3"


def main() -> None:
    registry = list(csv.DictReader(REGISTRY.open(encoding="utf-8-sig", newline="")))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    expected = audit["expected_features"]
    expected_set = set(expected)
    source_registry_rows = [row for row in registry if row["dataset"] == SOURCE and row["feature"] in expected_set]
    target_registry_rows = [row for row in registry if row["dataset"] == TARGET and row["feature"] in expected_set]
    source_rows = {row["feature"]: row for row in source_registry_rows}
    target_rows = {row["feature"]: row for row in target_registry_rows}
    if len(expected) != 53 or set(source_rows) != set(expected) or set(target_rows) != set(expected):
        raise ValueError("Registry and audited 53-feature dictionary do not match exactly")
    if len(source_registry_rows) != len(expected) or len(target_registry_rows) != len(expected):
        raise ValueError("Duplicate feature rows found in active-pair registry")

    rows = []
    included = []
    excluded = []
    for feature in expected:
        src, tgt = source_rows[feature], target_rows[feature]
        if src["role"] != tgt["role"]:
            raise ValueError(f"Role mismatch between active datasets: {feature}")
        role = src["role"]
        include = role == "predictive_candidate"
        note = (
            "Proposed input because registry role is predictive_candidate; review before freeze."
            if include else
            "Retain in full registry/audit metadata; exclude from this proposed predictive matrix pending governance."
        )
        row = {
            "feature": feature,
            "source_role": src["role"],
            "target_role": tgt["role"],
            "source_type": src["observed_type"],
            "target_type": tgt["observed_type"],
            "proposed_primary_input": "yes" if include else "no",
            "decision_status": "draft_review_required",
            "source_notes": src["notes"],
            "target_notes": tgt["notes"],
        }
        rows.append(row)
        (included if include else excluded).append(feature)

    with (OUT / "primary_feature_set_draft.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    hashes = {x["dataset"]: x["sha256"] for x in audit["datasets"] if x["dataset"] in (SOURCE, TARGET)}
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    generated_from = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True,
        capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()
    summary = {
        "configuration_id": "primary-features-draft-1",
        "generated_at_utc": generated_at,
        "generated_from_git_commit": generated_from,
        "status": "draft_not_frozen",
        "scope": f"{SOURCE} source candidate to {TARGET} target candidate",
        "dataset_sha256": hashes,
        "feature_dictionary_count": len(expected),
        "proposed_predictive_input_count": len(included),
        "proposed_predictive_inputs_in_dictionary_order": included,
        "excluded_feature_count": len(excluded),
        "excluded_features_retained_in_registry": excluded,
        "role_policy": "Include every shared predictive_candidate field; exclude audit_split_metadata and identifier_like fields from this candidate model matrix; never remove fields from raw inputs or the feature registry.",
        "targets": ["Label", "Attack"],
        "target_label_policy": "Neither target column is included; target labels and label-count values are not used to construct this proposal.",
        "caution": "This explicit list is a review proposal derived from draft registry roles, not an approved or frozen feature set. Review identifier, timestamp, constant/domain-shortcut, and compact-representation governance before E1."
    }
    (OUT / "primary_feature_set_draft.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    report = [
        "# Proposed Primary Feature Set (Draft)", "",
        "**Status:** Review draft; not frozen and not used for model fitting.", "",
        f"**Config:** `primary-features-draft-1` · **Generated UTC:** `{generated_at}` · **Base commit:** `{generated_from}`.", "",
        f"Dataset SHA-256 values are recorded in `primary_feature_set_draft.json` (`{SOURCE}` `{hashes[SOURCE]}`, `{TARGET}` `{hashes[TARGET]}`).", "",
        "## Proposal", "",
        f"Include all **{len(included)}** shared `predictive_candidate` columns from the feature registry, in the audited NetFlow-v3 dictionary order. Keep the complete 53-feature interface visible in the registry. The other **{len(excluded)}** features remain present in the source files and audit records but are excluded from this proposed predictive matrix because their draft roles are audit/split metadata or identifier-like.", "",
        "The complete 53-row decision table is `primary_feature_set_draft.csv`; the ordered model-input list, dataset hashes, and generation provenance are in `primary_feature_set_draft.json`.", "",
        "## Explicitly excluded from this candidate matrix", "",
        "| Feature | Draft role | Reason retained outside predictors |", "|---|---|---|"
    ]
    for feature in excluded:
        src = source_rows[feature]
        report.append(f"| `{feature}` | `{src['role']}` | {src['notes']} |")
    report += [
        "", "## Required review", "",
        "This is a translation of the current draft registry, not a scientific decision. Review the candidate set before freezing it, especially the DNS query identifier, absolute timestamps, endpoint addresses and ports, and `FTP_COMMAND_RET_CODE` (which varies in UNSW but is constant in CIC2018). Do not silently alter this list. The compact 8-feature sensitivity has its own crosswalk and port decision.", "",
        "Target label values do not determine this proposal. Raw datasets were not modified.", ""
    ]
    (OUT / "PRIMARY_FEATURE_SET_DRAFT.md").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
