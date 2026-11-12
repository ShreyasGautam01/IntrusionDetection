"""Freeze the active-pair E1 feature order and conservative family crosswalk."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/nf_v3_audit"
DATASETS = ("NF-UNSW-NB15-v3", "NF-CSE-CIC-IDS2018-v3")
CONFIGS = {
    "NF-UNSW-NB15-v3": REPORTS / "source_e1_config.json",
    "NF-CSE-CIC-IDS2018-v3": REPORTS / "source_e1_cic_config.json",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_registry() -> tuple[list[dict[str, object]], list[str], dict[str, dict]]:
    inventory = read_csv(ROOT / "feature_registry.csv")
    configs = {dataset: json.loads(CONFIGS[dataset].read_text(encoding="utf-8"))
               for dataset in DATASETS}
    feature_orders = {dataset: configs[dataset]["features"]["columns"] for dataset in DATASETS}
    if feature_orders[DATASETS[0]] != feature_orders[DATASETS[1]]:
        raise ValueError("The two frozen E1 configurations do not share an identical ordered feature list")
    if len(feature_orders[DATASETS[0]]) != 46 or len(set(feature_orders[DATASETS[0]])) != 46:
        raise ValueError("The E1 predictor list must contain 46 unique columns")

    output: list[dict[str, object]] = []
    fields = ["dataset", "raw_column_order", "raw_column", "transfer_role",
              "e1_feature_order", "used_for_prediction", "preprocessing_rule", "notes"]
    for dataset in DATASETS:
        rows = [r for r in inventory if r["dataset"] == dataset]
        if len(rows) != 55 or len({r["feature"] for r in rows}) != 55:
            raise ValueError(f"Expected 55 unique audited columns for {dataset}")
        candidates = [r["feature"] for r in rows if r["role"] == "predictive_candidate"]
        locked = feature_orders[dataset]
        if len(candidates) != 46 or set(candidates) != set(locked):
            raise ValueError(f"Audited predictor inventory differs from E1 config for {dataset}")
        nonpredictors = [r for r in rows if r["role"] != "predictive_candidate"]
        role_counts = {role: sum(r["role"] == role for r in nonpredictors)
                       for role in {r["role"] for r in nonpredictors}}
        if role_counts != {"audit_split_metadata": 2, "identifier_like": 5, "target": 2}:
            raise ValueError(f"Unexpected seven metadata/identifier and two target columns for {dataset}: {role_counts}")
        by_feature = {r["feature"]: r for r in rows}
        for raw_order, source_row in enumerate(rows, start=1):
            name, old_role = source_row["feature"], source_row["role"]
            if name in locked:
                role, order, used = "predictor", locked.index(name) + 1, "yes"
                prep = "source-training finite replacement per direction; no target fitting"
            elif name == "Label":
                role, order, used = "binary_target_label", "", "evaluation only after manifest validation"
                prep = "never a predictor or preprocessing input"
            elif name == "Attack":
                role, order, used = "attack_family_target_label", "", "evaluation only after manifest validation"
                prep = "never a predictor or preprocessing input"
            elif old_role == "audit_split_metadata":
                role, order, used = "split_metadata", "", "no"
                prep = "excluded from E1 predictors"
            elif old_role == "identifier_like":
                role, order, used = "identifier", "", "no"
                prep = "excluded from E1 predictors"
            else:
                raise ValueError(f"Unclassified column {dataset}:{name}")
            output.append({
                "dataset": dataset,
                "raw_column_order": raw_order,
                "raw_column": name,
                "transfer_role": role,
                "e1_feature_order": order,
                "used_for_prediction": used,
                "preprocessing_rule": prep,
                "notes": source_row["notes"],
            })
    return output, fields, configs


def build_family_outputs() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    family_rows = read_csv(REPORTS / "family_mapping_draft.csv")
    pair_rows = read_csv(REPORTS / "family_matrix_draft.csv")
    if not family_rows or not pair_rows:
        raise ValueError("The audited family mapping artifacts are required")
    shared = [r for r in pair_rows if r["relation"] == "documented_shared"]
    if len(shared) != 1 or (shared[0]["source_family"], shared[0]["target_family"]) != ("DoS", "DoS"):
        raise ValueError("Expected only the documented DoS/DoS shared category from the existing audit")

    final_families: list[dict[str, object]] = []
    fields = ["dataset", "raw_attack_label", "binary_label", "local_canonical_family",
              "local_mapping_basis", "cross_domain_family_id", "cross_domain_decision",
              "unseen_family_claim", "local_rows", "evidence_url"]
    for row in family_rows:
        family = row["canonical_family"]
        benign = row["binary_label"] == "0"
        is_dos = family == "DoS" and not benign
        final_families.append({
            "dataset": row["dataset"],
            "raw_attack_label": row["raw_label"],
            "binary_label": row["binary_label"],
            "local_canonical_family": family,
            "local_mapping_basis": row["mapping_basis"],
            "cross_domain_family_id": "shared:DoS" if is_dos else "",
            "cross_domain_decision": "documented_shared_category; scenario identity not asserted" if is_dos
                                     else "dataset-local; no cross-domain equivalence asserted",
            "unseen_family_claim": "withheld",
            "local_rows": row["rows"],
            "evidence_url": row["source_url"],
        })

    final_pairs: list[dict[str, object]] = []
    for row in pair_rows:
        relation = row["relation"]
        decision = {
            "documented_shared": "shared_category_only",
            "ambiguous_possible_overlap": "retain_dataset_local_ambiguous",
            "no_documented_equivalence": "retain_dataset_local",
        }.get(relation)
        if decision is None:
            raise ValueError(f"Unknown family relation: {relation}")
        final_pairs.append({**row, "frozen_decision": decision,
                            "unseen_family_claim": "withheld_without_predefined_semantic_crosswalk"})
    return final_families, final_pairs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate frozen inputs without writing outputs")
    args = parser.parse_args()
    registry, registry_fields, configs = build_registry()
    family_rows, family_pairs = build_family_outputs()
    if args.check:
        print(f"Validated {len(registry)} feature-role rows, {len(family_rows)} family rows, "
              f"and {len(family_pairs)} family-pair rows.")
        return

    write_csv(REPORTS / "transfer_feature_registry.csv", registry, registry_fields)
    write_csv(REPORTS / "transfer_family_registry.csv", family_rows,
              ["dataset", "raw_attack_label", "binary_label", "local_canonical_family",
               "local_mapping_basis", "cross_domain_family_id", "cross_domain_decision",
               "unseen_family_claim", "local_rows", "evidence_url"])
    write_csv(REPORTS / "transfer_family_pair_matrix.csv", family_pairs,
              [*read_csv(REPORTS / "family_matrix_draft.csv")[0].keys(),
               "frozen_decision", "unseen_family_claim"])

    dos = next(r for r in family_pairs if r["source_family"] == "DoS" and r["target_family"] == "DoS")
    report = f"""# Frozen Transfer Representation and Family Crosswalk

**Status:** Frozen for the two core NF-v3 transfer directions.

**Feature source:** Both source E1 configurations, each with {len(configs[DATASETS[0]]['features']['columns'])} predictors in the same ordered list.

**Registry:** `transfer_feature_registry.csv`.

## Feature roles

The transfer predictor list is exactly the ordered 46-column E1 list. Each dataset has 55 audited columns: 46 predictors, seven non-predictor metadata/identifier columns (two split/chronology fields and five identifier-like fields), and the `Label` and `Attack` evaluation targets. The two targets are available only to final evaluation after the direction manifests validate. Target preprocessing uses only replacements fitted on the source training partition; distance scaling also fits on source training only.

## Family crosswalk

Only the audited `DoS` ↔ `DoS` pair is assigned cross-domain ID `shared:DoS` ({dos['rationale']}). This denotes a documented shared category; it does not claim identical attack scenarios. The `DoS`/`DDoS` relationship and all other ambiguous or undocumented pairs remain dataset-local. Raw labels and local family groupings are preserved. **No target-exclusive or “unseen family” claim is made solely from absent or different label strings.**

Machine-readable records are in `transfer_family_registry.csv` and `transfer_family_pair_matrix.csv`; their bases and sources are retained from the audited draft artifacts. The frozen feature order is reproducible with `scripts/finalize_transfer_registry.py --check`.
"""
    (REPORTS / "TRANSFER_REPRESENTATION_AND_FAMILY_LOCK.md").write_text(report, encoding="utf-8")
    print(f"Wrote {len(registry)} feature-role rows, {len(family_rows)} family rows, "
          f"and {len(family_pairs)} family-pair rows.")


if __name__ == "__main__":
    main()
