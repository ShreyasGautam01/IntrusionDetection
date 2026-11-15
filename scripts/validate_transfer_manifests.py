#!/usr/bin/env python3
"""Read-only CLI for the strict two-direction NF-v3 transfer lock validator."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


def validate(validator=None, specs_factory=None):
    if validator is None:
        from ids_research.target_lockbox import validate_both_transfer_manifests
        validator = validate_both_transfer_manifests
    if specs_factory is None:
        from score_target_transfer import lock_specs
        specs_factory = lock_specs
    return validator(specs_factory(), repository_root=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direction", choices=("unsw-to-cic", "cic-to-unsw"),
                        help="also assert that this direction is among the two validated locks")
    args = parser.parse_args()
    try:
        locks = validate()
        if args.direction and args.direction not in locks.directions:
            raise ValueError(f"Requested direction was not validated: {args.direction}")
        report = {
            "valid": True,
            "directions": sorted(locks.directions),
            "requested_direction": args.direction,
            "manifest_sha256": dict(locks.manifest_sha256),
            "head_commit": locks.head_commit,
            "target_labels_read": False,
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "error_type": type(exc).__name__,
                          "error": str(exc), "target_labels_read": False},
                         indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
