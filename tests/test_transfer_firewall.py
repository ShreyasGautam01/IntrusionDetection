from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from ids_research.review_ranking import ranked_binary_event_metrics, stable_review_selections
from ids_research.transfer_scoring import reliability_score_batch
from ids_research.target_lockbox import (
    iter_final_evaluation_labels,
    iter_target_feature_batches,
    validate_both_transfer_manifests,
    verify_freeze_manifest,
)
from target_exact_knn import benchmark_exact_case
from score_target_transfer import capacity_requirements
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], check=True,
                            capture_output=True, text=True)
    return result.stdout.strip()


class FeatureBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.path = Path(self.temp.name) / "target.csv"
        self.features = [f"f{i:02d}" for i in range(46)]
        self.header = [*self.features, "Label", "Attack"]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_csv(self, header: list[str] | None = None, rows: list[list[str]] | None = None) -> None:
        with self.path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(self.header if header is None else header)
            for row in (rows if rows is not None else [
                [str(i) for i in range(46)] + ["label-secret-0", "family-secret-0"],
                [str(i + 1) for i in range(46)] + ["label-secret-1", "family-secret-1"],
            ]):
                writer.writerow(row)

    def test_streams_only_ordered_features_and_offsets(self) -> None:
        self.write_csv()
        batches = list(iter_target_feature_batches(
            self.path, self.features, batch_size=1, expected_header=self.header))
        self.assertEqual([start for start, _ in batches], [0, 1])
        self.assertEqual(batches[0][1][0], tuple(str(i) for i in range(46)))
        self.assertEqual(len(batches[0][1][0]), 46)
        self.assertNotIn("label-secret-0", repr(batches))
        self.assertNotIn("family-secret-0", repr(batches))

    def test_rejects_label_columns_duplicates_missing_schema_and_bad_rows(self) -> None:
        self.write_csv()
        with self.assertRaisesRegex(ValueError, "Target columns"):
            list(iter_target_feature_batches(self.path, [*self.features, "Label"]))
        with self.assertRaisesRegex(ValueError, "Duplicate requested"):
            list(iter_target_feature_batches(self.path, [*self.features, self.features[0]]))
        with self.assertRaisesRegex(ValueError, "frozen feature registry"):
            list(iter_target_feature_batches(self.path, self.features, expected_header=["wrong"]))
        with self.assertRaisesRegex(ValueError, "absent"):
            list(iter_target_feature_batches(self.path, [*self.features[:-1], "missing"]))
        self.write_csv(rows=[["only-one-field"]])
        with self.assertRaisesRegex(ValueError, "Malformed row width"):
            list(iter_target_feature_batches(self.path, self.features))


class ReviewRankingTests(unittest.TestCase):
    def test_floor_budget_stable_offset_ties_and_cutoff_count(self) -> None:
        scores = np.asarray([5, 4, 4, 4, 2, 1, 1, 1, 1, 0], dtype=np.float32)
        result = stable_review_selections(scores, (0.3, 0.5, 1.0))
        self.assertEqual(result[0.3]["selected_rows"], 3)
        np.testing.assert_array_equal(result[0.3]["selected_row_offsets"], [0, 1, 2])
        self.assertEqual(result[0.3]["cutoff_score"], 4.0)
        self.assertEqual(result[0.3]["cutoff_tie_count"], 3)
        self.assertEqual(result[0.5]["selected_rows"], 5)
        np.testing.assert_array_equal(result[0.5]["selected_row_offsets"], [0, 1, 2, 3, 4])

    def test_rejects_invalid_scores_or_budgets(self) -> None:
        with self.assertRaises(ValueError):
            stable_review_selections(np.asarray([[1.0, 2.0]]))
        with self.assertRaises(ValueError):
            stable_review_selections(np.asarray([1.0, np.nan]))
        with self.assertRaises(ValueError):
            stable_review_selections(np.asarray([1.0]), (-0.1,))

    def test_grouped_auprc_and_floor_budget_capture_match_sklearn(self) -> None:
        from sklearn.metrics import average_precision_score
        scores = np.asarray([.9, .8, .8, .6, .6, .1], dtype=np.float32)
        errors = np.asarray([0, 1, 0, 1, 0, 0], dtype=np.uint8)
        misses = np.asarray([1, 0, 0, 1, 0, 0], dtype=np.uint8)
        result = ranked_binary_event_metrics(scores, errors, misses, (.5,))
        self.assertAlmostEqual(result["generic_error_auprc"],
                               average_precision_score(errors, scores))
        self.assertAlmostEqual(result["attack_miss_auprc"],
                               average_precision_score(misses, scores))
        self.assertEqual(result["review_budgets"]["0.5"]["selected_rows"], 3)
        self.assertEqual(result["review_budgets"]["0.5"]["cutoff_tie_count"], 2)
        self.assertEqual(result["review_budgets"]["0.5"]["attack_miss_rows_captured"], 1)


class ExactDistanceTests(unittest.TestCase):
    def test_duplicate_compression_and_chunk_merge_match_raw_exact_five_nn(self) -> None:
        rng = np.random.default_rng(20261112)
        unique = rng.normal(size=(24, 46)).astype(np.float32)
        repeats = np.asarray([1 + (i % 4) for i in range(len(unique))])
        source = np.repeat(unique, repeats, axis=0)
        queries = rng.normal(size=(13, 46)).astype(np.float32)
        scaler = StandardScaler().fit(source)
        result = benchmark_exact_case(
            source, queries, scaler, reference_rows=len(source), query_rows=len(queries),
            chunk_rows=17, query_batch_rows=4, return_scores=True,
        )
        raw_index = NearestNeighbors(n_neighbors=5, algorithm="brute", metric="euclidean", n_jobs=1)
        raw_index.fit(scaler.transform(source))
        expected = raw_index.kneighbors(scaler.transform(queries), return_distance=True)[0].mean(axis=1)
        self.assertTrue(result["all_finite"])
        self.assertLessEqual(float(np.max(np.abs(expected - result["scores"]))), 1e-6)


class ReliabilityBatchTests(unittest.TestCase):
    def test_five_scores_match_the_frozen_formulas(self) -> None:
        class Tree:
            def __init__(self, prediction):
                self.prediction = np.asarray(prediction, dtype=np.uint8)

            def predict(self, features):
                return self.prediction[:len(features)]

        class Model:
            estimators_ = [Tree([1, 0]), Tree([1, 0]), Tree([0, 0])]

            def predict_proba(self, features):
                p = np.asarray([.8, .3], dtype=np.float64)[:len(features)]
                return np.column_stack((p, 1 - p))

        class Calibrator:
            def predict_proba(self, logits):
                p = 1 / (1 + np.exp(-logits[:, 0]))
                return np.column_stack((p, 1 - p))

        class Isolation:
            def score_samples(self, features):
                return np.asarray([-.1, -.9])[:len(features)]

        scores = reliability_score_batch(
            Model(), Calibrator(), Isolation(), np.ones((2, 46), dtype=np.float32),
            conformal_quantile=.21)
        np.testing.assert_allclose(scores["confidence"], [.2, .3], atol=1e-6)
        np.testing.assert_allclose(scores["random_forest_disagreement"], [1 / 3, 0], atol=1e-6)
        np.testing.assert_array_equal(scores["split_conformal"], [0, -1])
        np.testing.assert_allclose(scores["isolation_forest"], [.1, .9], atol=1e-6)
        self.assertEqual(scores["calibrated_probability"].shape, (2,))

    def test_rejects_malformed_or_non_finite_features(self) -> None:
        with self.assertRaisesRegex(ValueError, "float32 feature matrix"):
            reliability_score_batch(None, None, None, np.ones((1, 46), dtype=np.float64),
                                    conformal_quantile=.1)
        with self.assertRaisesRegex(ValueError, "non-finite"):
            reliability_score_batch(None, None, None, np.full((1, 46), np.nan, dtype=np.float32),
                                    conformal_quantile=.1)


class TransferCapacityTests(unittest.TestCase):
    def test_model_cache_reserve_scales_from_measured_seed_zero_size(self) -> None:
        plan = capacity_requirements(
            target_rows=1000, seed_count=10, seed0_model_cache_bytes=1_200_000_000,
            missing_model_cache_seeds=9,
        )
        self.assertEqual(plan["model_cache_reserve_bytes"], 13_500_000_000)
        self.assertEqual(plan["missing_model_cache_seeds"], 9)
        complete = capacity_requirements(
            target_rows=1000, seed_count=10, seed0_model_cache_bytes=1_200_000_000,
            missing_model_cache_seeds=0,
        )
        self.assertEqual(complete["model_cache_reserve_bytes"], 0)
        self.assertGreater(plan["headroom_bytes"], complete["headroom_bytes"])


class FreezeManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self.temp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Transfer Test")
        git(self.root, "config", "user.email", "transfer-test@example.invalid")
        self.manifests = self.root / "manifests"
        self.manifests.mkdir()
        self.manifest_path = self.manifests / "transfer_src_to_tgt.json"
        self.source_file = self.root / "source.csv"
        self.target_file = self.root / "target.csv"
        self.source_file.write_text("source-only-bytes\n", encoding="utf-8")
        self.target_file.write_text("f00,Label,Attack\n1,0,Benign\n", encoding="utf-8")
        self.code_file = self.root / "scripts" / "locked.py"
        self.code_file.parent.mkdir()
        self.code_file.write_text("locked transfer implementation\n", encoding="utf-8")
        self.smoke_code_paths = (
            "scripts/score_target_transfer.py", "scripts/target_exact_knn.py",
            "scripts/target_transfer_common.py", "src/ids_research/transfer_scoring.py",
        )
        self.smoke_code = {}
        for relative in self.smoke_code_paths:
            code_path = self.root / relative
            code_path.parent.mkdir(parents=True, exist_ok=True)
            code_path.write_text("locked smoke implementation\n", encoding="utf-8")
            self.smoke_code[relative] = sha(code_path)
        self.gate_report = self.root / "gate_interpretation.md"
        self.gate_report.write_text("## Owner decision\nOwner accepted source-only gate.\n", encoding="utf-8")
        self.config_file = self.root / "config.json"
        self.feature_order = [f"f{i:02d}" for i in range(46)]
        self.config_file.write_text(json.dumps({
            "configuration_id": "cfg-v1",
            "source_dataset": {"name": "SRC", "sha256": sha(self.source_file)},
            "target": {"dataset": "TGT"},
            "features": {"columns": self.feature_order},
        }), encoding="utf-8")
        self.stage = self.root / "stage.json"
        self.stage.write_text(json.dumps({
            "configuration_id": "cfg-v1", "configuration_sha256": sha(self.config_file),
            "feature_order": self.feature_order, "target_file_read": False,
            "target_labels_read": False,
        }), encoding="utf-8")
        self.e1_manifest = self.root / "source_manifest.json"
        self.e1_manifest.write_text(json.dumps({
            "configuration_id": "cfg-v1", "configuration_sha256": sha(self.config_file),
            "feature_order": self.feature_order,
            "source_dataset": {"name": "SRC", "sha256": sha(self.source_file)},
        }), encoding="utf-8")
        self.e1_results = self.root / "source_results.json"
        self.e1_results.write_text(json.dumps({
            "direction": "src-to-tgt", "configuration_id": "cfg-v1", "complete_seed_count": 10,
            "all_per_seed_outputs_integrity_verified": True,
            "manifest_sha256": sha(self.e1_manifest),
        }), encoding="utf-8")
        self.feature_registry = self.root / "feature_registry.csv"
        with self.feature_registry.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=[
                "dataset", "raw_column", "transfer_role", "e1_feature_order", "used_for_prediction"])
            writer.writeheader()
            for dataset in ("SRC", "TGT"):
                for i, name in enumerate(self.feature_order, 1):
                    writer.writerow({"dataset": dataset, "raw_column": name,
                                     "transfer_role": "predictor", "e1_feature_order": i,
                                     "used_for_prediction": "yes"})
                for i in range(5):
                    writer.writerow({"dataset": dataset, "raw_column": f"id{i:02d}",
                                     "transfer_role": "identifier", "e1_feature_order": "",
                                     "used_for_prediction": "no"})
                for i in range(2):
                    writer.writerow({"dataset": dataset, "raw_column": f"meta{i:02d}",
                                     "transfer_role": "split_metadata", "e1_feature_order": "",
                                     "used_for_prediction": "no"})
                for name, role in (("Label", "binary_target_label"),
                                   ("Attack", "attack_family_target_label")):
                    writer.writerow({"dataset": dataset, "raw_column": name,
                                     "transfer_role": role, "e1_feature_order": "",
                                     "used_for_prediction": "no"})
        self.family_registry = self.root / "family_registry.csv"
        self.family_registry.write_text(
            "dataset,unseen_family_claim\nSRC,withheld\nTGT,withheld\n", encoding="utf-8")
        self.family_matrix = self.root / "family_matrix.csv"
        self.family_matrix.write_text(
            "source_family,target_family,relation,unseen_family_claim\n"
            "LocalA,LocalB,no_documented_equivalence,withheld_without_crosswalk\n",
            encoding="utf-8")
        self.bench_distance = self.root / "distance_benchmark.json"
        self.bench_inference = self.root / "inference_benchmark.json"
        common_benchmark = {
            "direction": "src-to-tgt", "source_dataset_sha256": sha(self.source_file),
            "target_dataset_sha256": sha(self.target_file),
            "config_sha256": sha(self.config_file), "target_labels_read": False,
        }
        self.bench_distance.write_text(json.dumps({**common_benchmark,
                                                  "report_id": "target-exact-distance-src-to-tgt-v1"}),
                                       encoding="utf-8")
        self.bench_inference.write_text(json.dumps({**common_benchmark,
                                                    "report_id": "target-inference-src-to-tgt-v1"}),
                                        encoding="utf-8")
        self.smoke_report = self.root / "smoke_benchmark.json"
        self.smoke_report.write_text(json.dumps({
            **common_benchmark, "report_id": "target-transfer-five-signal-smoke-src-to-tgt-v1",
            "all_finite": True, "rows": 256,
            "signals": ["confidence", "random_forest_disagreement", "feature_space_distance",
                        "split_conformal", "isolation_forest"],
            "source_e1_verification": {"exact_match": {
                "prediction.npy": True, "calibrated_probability.npy": True,
                "random_forest_disagreement.npy": True, "isolation_forest.npy": True}},
            "code_sha256": self.smoke_code,
        }), encoding="utf-8")
        self.software_lock = self.root / "uv.lock"
        self.software_lock.write_text("locked software\n", encoding="utf-8")
        (self.root / "lock.txt").write_text("locked\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "lock transfer inputs")
        self.lock_commit = git(self.root, "rev-parse", "HEAD")
        self.manifest = {
            "manifest_id": "src-to-tgt-v1", "status": "frozen", "direction": "src-to-tgt",
            "lock_commit": self.lock_commit, "source_sha256": sha(self.source_file),
            "target_sha256": sha(self.target_file), "config_sha256": sha(self.config_file),
            "source_stage_manifest_sha256": sha(self.stage),
            "source_e1_manifest_sha256": sha(self.e1_manifest),
            "source_e1_results_sha256": sha(self.e1_results),
            "source_gate_interpretation_sha256": sha(self.gate_report),
            "feature_registry_sha256": sha(self.feature_registry),
            "family_registry_sha256": sha(self.family_registry),
            "family_pair_matrix_sha256": sha(self.family_matrix),
            "source_dataset": "SRC", "target_dataset": "TGT",
            "feature_order": self.feature_order, "target_labels_read": False,
            "source_gate_accepted": True,
            "seeds": list(range(10)), "max_target_batch_rows": 8192,
            "distance_parameters": {"neighbors": 5, "metric": "euclidean", "exact": True,
                                    "reference_chunk_rows": 500000, "query_batch_rows": 2048},
            "review_budgets": [0.01, 0.05, 0.10],
            "software_lock_sha256": sha(self.software_lock),
            "software": {"python": __import__("platform").python_version(),
                         "numpy": np.__version__, "scikit_learn": sklearn.__version__},
            "benchmarks": {
                "distance_benchmark.json": sha(self.bench_distance),
                "inference_benchmark.json": sha(self.bench_inference),
                "smoke_benchmark.json": sha(self.smoke_report),
            },
            "smoke_evidence": {"path": "smoke_benchmark.json",
                               "sha256": sha(self.smoke_report), "rows": 256,
                               "target_labels_read": False},
            "code_sha256": {"scripts/locked.py": sha(self.code_file), **self.smoke_code},
        }
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
        git(self.root, "add", "manifests/transfer_src_to_tgt.json")
        git(self.root, "commit", "-q", "-m", "freeze transfer manifest")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def validate(self, path: Path | None = None, direction: str = "src-to-tgt") -> dict:
        return verify_freeze_manifest(
            path or self.manifest_path, repository_root=self.root, direction=direction,
            source_file=self.source_file, target_file=self.target_file,
            config_file=self.config_file, source_stage_manifest=self.stage,
            source_e1_manifest=self.e1_manifest, source_e1_results=self.e1_results,
            source_gate_interpretation=self.gate_report,
            feature_registry=self.feature_registry, family_registry=self.family_registry,
            family_pair_matrix=self.family_matrix,
        )

    def test_committed_manifest_passes(self) -> None:
        self.assertEqual(self.validate()["status"], "frozen")

    def test_missing_draft_uncommitted_and_dirty_manifests_fail_closed(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.validate(self.root / "missing.json")
        draft = self.root / "draft.json"
        draft_data = {**self.manifest, "status": "draft"}
        draft.write_text(json.dumps(draft_data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "status is frozen"):
            self.validate(draft)
        uncommitted = self.root / "manifests/uncommitted.json"
        uncommitted.write_text(json.dumps(self.manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "must be committed"):
            self.validate(uncommitted)
        dirty = {**self.manifest, "benchmarks": {**self.manifest["benchmarks"], "draft_note": "changed"}}
        self.manifest_path.write_text(json.dumps(dirty), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "uncommitted or differs"):
            self.validate()

    def test_stale_input_and_wrong_direction_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "direction"):
            self.validate(direction="tgt-to-src")
        self.target_file.write_text("changed bytes\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Target dataset hash"):
            self.validate()

    def test_stale_code_and_benchmark_fail_closed(self) -> None:
        self.code_file.write_text("changed implementation\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Code file differs"):
            self.validate()
        self.code_file.write_text("locked transfer implementation\n", encoding="utf-8")
        self.bench_distance.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Benchmark evidence hash"):
            self.validate()

    def test_both_direction_locks_are_required_before_label_iterator(self) -> None:
        with self.assertRaisesRegex(ValueError, "Both core transfer manifests"):
            validate_both_transfer_manifests(
                {"unsw-to-cic": {}}, repository_root=self.root)
        with self.assertRaisesRegex(ValueError, "Both direction manifests"):
            list(iter_final_evaluation_labels(
                self.target_file, manifest_path=self.manifest_path,
                repository_root=self.root, direction="src-to-tgt",
                source_file=self.source_file, config_file=self.config_file,
                source_stage_manifest=self.stage, source_e1_manifest=self.e1_manifest,
                source_e1_results=self.e1_results,
                source_gate_interpretation=self.gate_report,
                feature_registry=self.feature_registry, family_registry=self.family_registry,
                family_pair_matrix=self.family_matrix, validated_locks=None,
            ))


if __name__ == "__main__":
    unittest.main()
