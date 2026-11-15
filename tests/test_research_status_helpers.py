from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.research_status import process_snapshot, summarize_progress
from scripts.validate_transfer_manifests import validate


class ResearchStatusHelperTests(unittest.TestCase):
    def test_process_query_denial_is_unknown_not_inactive(self) -> None:
        def denied(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 3, "", "Access denied")

        result = process_snapshot(denied)
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("transfer_runner_active", result)

    def test_progress_summary_reports_checkpoint_without_claiming_hash_verification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.json"
            path.write_text(json.dumps({
                "direction": "unsw-to-cic", "expected_seeds": [0, 1, 2],
                "completed_seeds": [{"seed": 0}, {"seed": 1}],
                "last_completed_seed": 1, "target_labels_read": False,
            }), encoding="utf-8")
            result = summarize_progress(path)
        self.assertEqual(result["completed_seeds"], [0, 1])
        self.assertEqual(result["completed_seed_count"], 2)
        self.assertIsNone(result["all_per_seed_outputs_integrity_verified"])

    def test_manifest_cli_adapter_propagates_strict_validation_failure(self) -> None:
        def reject(*args, **kwargs):
            raise ValueError("manifest is dirty")

        with self.assertRaisesRegex(ValueError, "manifest is dirty"):
            validate(validator=reject, specs_factory=lambda: {})


if __name__ == "__main__":
    unittest.main()
