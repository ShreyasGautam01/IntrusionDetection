"""Streaming target-label firewall for the locked cross-domain evaluation.

Prediction-time code receives only selected target feature columns. Target
labels are available through a separate final-evaluation function only after
a versioned freeze manifest is present in the current Git history.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping, Sequence

TARGET_COLUMNS = frozenset({'Label', 'Attack'})
CORE_TRANSFER_DIRECTIONS = frozenset({'unsw-to-cic', 'cic-to-unsw'})


@dataclass(frozen=True)
class ValidatedTransferLocks:
    """Proof record returned only after both committed direction locks validate."""

    repository_root: str
    directions: frozenset[str]
    manifest_sha256: Mapping[str, str]
    head_commit: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', '-C', str(root), *args], check=True, capture_output=True,
        text=True, encoding='utf-8'
    )
    return result.stdout.strip()


def verify_freeze_manifest(
    manifest_path: Path,
    *,
    repository_root: Path,
    direction: str,
    source_file: Path,
    target_file: Path,
    config_file: Path,
    source_stage_manifest: Path,
    source_e1_manifest: Path,
    source_e1_results: Path,
    source_gate_interpretation: Path,
    feature_registry: Path,
    family_registry: Path,
    family_pair_matrix: Path,
) -> dict:
    """Validate a committed, direction-bound lock record before target use.

    The raw target file is streamed only for its byte-level integrity hash.
    Target label values are not parsed or yielded until this function returns.
    """
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    required = (
        'status', 'manifest_id', 'direction', 'lock_commit', 'source_sha256',
        'target_sha256', 'config_sha256', 'source_stage_manifest_sha256',
        'source_e1_manifest_sha256', 'source_e1_results_sha256',
        'source_gate_interpretation_sha256', 'code_sha256',
        'feature_registry_sha256', 'family_registry_sha256',
        'family_pair_matrix_sha256', 'source_dataset', 'target_dataset',
        'feature_order', 'target_labels_read', 'source_gate_accepted',
        'software', 'software_lock_sha256', 'benchmarks', 'seeds',
        'max_target_batch_rows', 'distance_parameters', 'review_budgets', 'smoke_evidence',
    )
    missing = [key for key in required if key not in manifest
               or manifest[key] is None or manifest[key] == '']
    if missing:
        raise ValueError(f'Freeze manifest lacks required fields: {missing}')
    if not isinstance(manifest['benchmarks'], dict) or len(manifest['benchmarks']) < 2:
        raise ValueError('Freeze manifest must bind distance and inference benchmark files')
    if not isinstance(manifest['code_sha256'], dict) or not manifest['code_sha256']:
        raise ValueError('Freeze manifest must bind code at its lock commit')
    if manifest['status'] != 'frozen':
        raise ValueError('Target labels remain sealed until status is frozen')
    if manifest['direction'] != direction:
        raise ValueError('Freeze manifest direction differs from the requested direction')
    if manifest['target_labels_read'] is not False:
        raise ValueError('Freeze manifest reports target-label access before the lock')
    if manifest['source_gate_accepted'] is not True:
        raise ValueError('Both source-only E1 gate interpretations must be accepted before transfer')
    if manifest['seeds'] != list(range(10)):
        raise ValueError('Transfer manifest must preserve the frozen source seed set 0–9')
    if (not isinstance(manifest['max_target_batch_rows'], int)
            or isinstance(manifest['max_target_batch_rows'], bool)
            or manifest['max_target_batch_rows'] < 1):
        raise ValueError('Manifest target batch bound is invalid')
    if manifest['review_budgets'] != [0.01, 0.05, 0.10]:
        raise ValueError('Transfer manifest review budgets differ from the frozen protocol')
    distance_parameters = manifest['distance_parameters']
    if (distance_parameters.get('neighbors') != 5
            or distance_parameters.get('metric') != 'euclidean'
            or distance_parameters.get('exact') is not True
            or distance_parameters.get('reference_chunk_rows') != 500_000
            or distance_parameters.get('query_batch_rows') != 2048):
        raise ValueError('Transfer manifest does not retain the frozen exact distance definition')
    if sha256_file(source_file) != manifest['source_sha256']:
        raise ValueError('Source dataset hash differs from the frozen manifest')
    if sha256_file(target_file) != manifest['target_sha256']:
        raise ValueError('Target dataset hash differs from the frozen manifest')
    bound_files = (
        (config_file, 'config_sha256', 'Experiment configuration'),
        (source_stage_manifest, 'source_stage_manifest_sha256', 'Source stage manifest'),
        (source_e1_manifest, 'source_e1_manifest_sha256', 'Source E1 manifest'),
        (source_e1_results, 'source_e1_results_sha256', 'Source E1 results'),
        (source_gate_interpretation, 'source_gate_interpretation_sha256', 'Source E1 gate interpretation'),
        (feature_registry, 'feature_registry_sha256', 'Feature registry'),
        (family_registry, 'family_registry_sha256', 'Family registry'),
        (family_pair_matrix, 'family_pair_matrix_sha256', 'Family pair matrix'),
    )
    for path, key, description in bound_files:
        if sha256_file(path) != manifest[key]:
            raise ValueError(f'{description} differs from the frozen manifest')
    gate_text = source_gate_interpretation.read_text(encoding='utf-8').casefold()
    if 'owner decision' not in gate_text or 'accepted' not in gate_text:
        raise ValueError('Source E1 interpretation does not record owner acceptance')

    config = json.loads(config_file.read_text(encoding='utf-8'))
    stage = json.loads(source_stage_manifest.read_text(encoding='utf-8'))
    source_manifest = json.loads(source_e1_manifest.read_text(encoding='utf-8'))
    source_results = json.loads(source_e1_results.read_text(encoding='utf-8'))
    source_target_access = source_manifest.get('target_access', {})
    if (source_manifest.get('target_data_accessed', False) is not False
            or source_target_access.get('features_read', False) is not False
            or source_target_access.get('labels_read', False) is not False):
        raise ValueError('Source E1 manifest records target access before transfer')
    if (manifest['source_dataset'] != config['source_dataset']['name']
            or manifest['target_dataset'] != config['target']['dataset']):
        raise ValueError('Freeze manifest source/target dataset names differ from direction config')
    if manifest['feature_order'] != config['features']['columns'] or len(manifest['feature_order']) != 46:
        raise ValueError('Freeze manifest feature order differs from the frozen E1 configuration')
    stage_target_read = stage.get('target_file_read', stage.get('target_data_accessed', False))
    stage_labels_read = stage.get('target_labels_read', stage.get('target_label_accessed', False))
    stage_config_sha = stage.get('configuration_sha256')
    stage_source_sha = stage.get('source_dataset', {}).get('sha256')
    if (stage.get('configuration_id') != config['configuration_id']
            or (stage_config_sha is not None and stage_config_sha != manifest['config_sha256'])
            or (stage_source_sha is not None and stage_source_sha != manifest['source_sha256'])
            or stage.get('feature_order') != manifest['feature_order']
            or stage_target_read is not False or stage_labels_read is not False):
        raise ValueError('Source-stage provenance differs from the direction configuration')
    source_feature_order = source_manifest.get('feature_order')
    if source_feature_order is None:
        source_feature_order = source_manifest.get('features', {}).get('order')
    source_dataset_info = source_manifest.get('source_dataset', {})
    source_manifest_name = source_dataset_info.get(
        'name', source_manifest.get('source_dataset_name', config['source_dataset']['name']))
    source_manifest_hash = source_dataset_info.get(
        'sha256', source_manifest.get('source_dataset_sha256'))
    if (source_manifest.get('configuration_id') != config['configuration_id']
            or source_manifest.get('configuration_sha256') != manifest['config_sha256']
            or source_feature_order != manifest['feature_order']
            or source_manifest_name != manifest['source_dataset']
            or source_manifest_hash != manifest['source_sha256']):
        raise ValueError('Source E1 manifest differs from the direction configuration')
    if (source_results.get('direction') not in (None, direction)
            or source_results.get('configuration_id') != config['configuration_id']
            or source_results.get('complete_seed_count') != 10
            or source_results.get('all_per_seed_outputs_integrity_verified') is not True
            or source_results.get('manifest_sha256') != manifest['source_e1_manifest_sha256']):
        raise ValueError('Source E1 results are incomplete or not bound to the frozen source manifest')

    expected_software = manifest['software']
    actual_software = {
        'python': __import__('platform').python_version(),
        'numpy': __import__('numpy').__version__,
        'scikit_learn': __import__('sklearn').__version__,
    }
    if expected_software != actual_software:
        raise ValueError('Runtime software versions differ from the transfer manifest')
    software_lock_root = repository_root.resolve()
    if sha256_file(software_lock_root / 'uv.lock') != manifest['software_lock_sha256']:
        raise ValueError('Software lock differs from the transfer manifest')

    with feature_registry.open('r', encoding='utf-8-sig', newline='') as stream:
        registry_rows = list(csv.DictReader(stream))
    for dataset in (manifest['source_dataset'], manifest['target_dataset']):
        rows = [r for r in registry_rows if r['dataset'] == dataset]
        predictors = sorted((r for r in rows if r['transfer_role'] == 'predictor'),
                            key=lambda r: int(r['e1_feature_order']))
        role_counts = {}
        for row in rows:
            role_counts[row['transfer_role']] = role_counts.get(row['transfer_role'], 0) + 1
        if (len(rows) != 55 or role_counts != {
                'predictor': 46, 'identifier': 5, 'split_metadata': 2,
                'binary_target_label': 1, 'attack_family_target_label': 1}):
            raise ValueError(f'Feature registry roles are incomplete for {dataset}')
        if ([r['raw_column'] for r in predictors] != manifest['feature_order']
                or any(r['used_for_prediction'] != 'yes' for r in predictors)):
            raise ValueError(f'Feature registry predictor order differs for {dataset}')
        labels = [r for r in rows if r['transfer_role'] in
                  ('binary_target_label', 'attack_family_target_label')]
        metadata = [r for r in rows if r not in predictors and r not in labels]
        if ({r['raw_column'] for r in labels} != TARGET_COLUMNS
                or any(r['used_for_prediction'] != 'evaluation only after manifest validation'
                       for r in labels)
                or any(r['used_for_prediction'] != 'no' for r in metadata)):
            raise ValueError(f'Feature registry metadata/label roles are invalid for {dataset}')
        if any(r['used_for_prediction'] not in
               ('yes', 'no', 'evaluation only after manifest validation') for r in rows):
            raise ValueError(f'Feature registry contains an invalid prediction role for {dataset}')
    with family_registry.open('r', encoding='utf-8-sig', newline='') as stream:
        families = list(csv.DictReader(stream))
    if not families or any(r['unseen_family_claim'] != 'withheld' for r in families):
        raise ValueError('Family registry makes an unreviewed unseen-family claim')
    with family_pair_matrix.open('r', encoding='utf-8-sig', newline='') as stream:
        family_pairs = list(csv.DictReader(stream))
    if not family_pairs or any('withheld' not in r['unseen_family_claim'] for r in family_pairs):
        raise ValueError('Family pair matrix contains an unsupported unseen-family claim')
    shared = [r for r in family_pairs if r['relation'] == 'documented_shared_category']
    if any((r['source_family'], r['target_family']) != ('DoS', 'DoS') for r in shared):
        raise ValueError('Family pair matrix promotes an unsupported cross-domain mapping')

    root = repository_root.resolve()
    manifest_abs = manifest_path.resolve()
    try:
        manifest_rel = manifest_abs.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError('Freeze manifest must be stored inside the repository') from exc
    head = _git(root, 'rev-parse', 'HEAD')
    tracked = subprocess.run(
        ['git', '-C', str(root), 'ls-files', '--error-unmatch', manifest_rel],
        check=False, capture_output=True, text=True, encoding='utf-8'
    )
    if tracked.returncode != 0:
        raise ValueError('Freeze manifest must be committed before target access')
    committed_manifest = _git(root, 'show', f'HEAD:{manifest_rel}')
    if _git(root, 'status', '--porcelain', '--', manifest_rel):
        raise ValueError('Freeze manifest is uncommitted or differs from the committed record')
    if json.loads(committed_manifest) != manifest:
        raise ValueError('Freeze manifest differs from its committed version')
    lock_ancestor = subprocess.run(
        ['git', '-C', str(root), 'merge-base', '--is-ancestor', manifest['lock_commit'], head],
        check=False, capture_output=True, text=True, encoding='utf-8'
    )
    if lock_ancestor.returncode != 0:
        raise ValueError('Freeze manifest code lock commit is not an ancestor of HEAD')
    for relative, expected in manifest['code_sha256'].items():
        code_rel = Path(relative)
        if code_rel.is_absolute() or '..' in code_rel.parts:
            raise ValueError('Code lock paths must be repository-relative')
        code_path = root / code_rel
        try:
            code_path.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError('Code lock path escapes the repository') from exc
        if not code_path.is_file() or sha256_file(code_path) != expected:
            raise ValueError(f'Code file differs from the frozen lock: {relative}')
        tracked_code = subprocess.run(
            ['git', '-C', str(root), 'ls-files', '--error-unmatch', relative],
            check=False, capture_output=True, text=True, encoding='utf-8'
        )
        if tracked_code.returncode != 0:
            raise ValueError(f'Frozen code file is not committed: {relative}')
        unchanged = subprocess.run(
            ['git', '-C', str(root), 'diff', '--quiet', manifest['lock_commit'], 'HEAD', '--', relative],
            check=False, capture_output=True
        )
        if unchanged.returncode != 0:
            raise ValueError(f'Code changed after its lock commit: {relative}')
    benchmark_ids = set()
    for relative, expected in manifest['benchmarks'].items():
        benchmark_path = root / relative
        try:
            benchmark_path.resolve().relative_to(root)
        except ValueError as exc:
            raise ValueError('Benchmark paths must stay inside the repository') from exc
        if not benchmark_path.is_file() or sha256_file(benchmark_path) != expected:
            raise ValueError(f'Benchmark evidence hash mismatch: {relative}')
        benchmark = json.loads(benchmark_path.read_text(encoding='utf-8'))
        benchmark_config_sha = benchmark.get('direction_config_sha256', benchmark.get('config_sha256'))
        if (benchmark.get('direction') != direction
                or benchmark.get('target_labels_read') is not False
                or benchmark.get('source_dataset_sha256') != manifest['source_sha256']
                or benchmark.get('target_dataset_sha256') != manifest['target_sha256']
                or benchmark_config_sha != manifest['config_sha256']):
            raise ValueError(f'Benchmark evidence does not match the frozen direction: {relative}')
        benchmark_ids.add(str(benchmark.get('report_id', '')))
    if (not any('distance' in report_id for report_id in benchmark_ids)
            or not any('inference' in report_id for report_id in benchmark_ids)):
        raise ValueError('Freeze manifest requires exact-distance and target-inference benchmark evidence')
    smoke = manifest['smoke_evidence']
    if (not isinstance(smoke, dict) or smoke.get('target_labels_read') is not False
            or smoke.get('path') not in manifest['benchmarks']
            or manifest['benchmarks'].get(smoke.get('path')) != smoke.get('sha256')):
        raise ValueError('Freeze manifest does not bind its feature-only five-signal smoke evidence')
    smoke_report = json.loads((root / smoke['path']).read_text(encoding='utf-8'))
    smoke_source_checks = smoke_report.get('source_e1_verification', {}).get('exact_match', {})
    smoke_code = smoke_report.get('code_sha256', {})
    required_smoke_code = {
        'scripts/score_target_transfer.py', 'scripts/target_exact_knn.py',
        'scripts/target_transfer_common.py', 'src/ids_research/transfer_scoring.py',
    }
    if (not required_smoke_code.issubset(smoke_code)
            or any(manifest['code_sha256'].get(path) != smoke_code.get(path)
                   for path in required_smoke_code)):
        raise ValueError('Five-signal smoke code does not match the frozen scoring implementation')
    if (smoke_report.get('direction') != direction
            or smoke_report.get('source_dataset_sha256') != manifest['source_sha256']
            or smoke_report.get('target_dataset_sha256') != manifest['target_sha256']
            or smoke_report.get('config_sha256') != manifest['config_sha256']
            or smoke_report.get('target_labels_read') is not False
            or smoke_report.get('all_finite') is not True
            or smoke_report.get('rows') != smoke.get('rows')
            or set(smoke_report.get('signals', [])) != {
                'confidence', 'random_forest_disagreement', 'feature_space_distance',
                'split_conformal', 'isolation_forest'}
            or not smoke_source_checks or not all(smoke_source_checks.values())):
        raise ValueError('Five-signal smoke report does not match the frozen direction')
    if _git(root, 'status', '--porcelain'):
        raise ValueError('Freeze manifest validation requires a clean tracked checkout')
    return manifest


def validate_both_transfer_manifests(
    specs: Mapping[str, dict], *, repository_root: Path
) -> ValidatedTransferLocks:
    """Validate both core direction locks before any target labels may be read."""
    if frozenset(specs) != CORE_TRANSFER_DIRECTIONS:
        raise ValueError('Both core transfer manifests must be provided together')
    root = repository_root.resolve()
    validated = {}
    hashes = {}
    for direction in sorted(CORE_TRANSFER_DIRECTIONS):
        spec = dict(specs[direction])
        manifest_path = spec.pop('manifest_path')
        validated[direction] = verify_freeze_manifest(
            manifest_path, repository_root=root, direction=direction, **spec
        )
        hashes[direction] = sha256_file(manifest_path)
    return ValidatedTransferLocks(
        repository_root=str(root), directions=frozenset(validated),
        manifest_sha256=hashes, head_commit=_git(root, 'rev-parse', 'HEAD'),
    )


def iter_target_features(
    target_file: Path,
    feature_columns: Sequence[str],
) -> Iterator[tuple[int, dict[str, str]]]:
    """Yield row number and features only; target columns are never returned."""
    selected = tuple(feature_columns)
    for start_row, batch in iter_target_feature_batches(target_file, selected, batch_size=1):
        yield start_row, dict(zip(selected, batch[0]))


def iter_target_feature_batches(
    target_file: Path,
    feature_columns: Sequence[str],
    *,
    batch_size: int = 8192,
    expected_header: Sequence[str] | None = None,
) -> Iterator[tuple[int, list[tuple[str, ...]]]]:
    """Yield bounded batches of selected features, never labels.

    `start_row` is a zero-based data-row offset (the header is not counted).
    Each record is a tuple ordered exactly like `feature_columns`. Only the
    selected values are returned or retained in the batch. This supports
    memory-bounded prediction on the full target lockbox.
    """
    selected = tuple(feature_columns)
    if not selected:
        raise ValueError('At least one explicit feature column is required')
    if len(selected) != len(set(selected)):
        raise ValueError('Duplicate requested feature names prevent safe selection')
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1:
        raise ValueError('batch_size must be a positive integer')
    forbidden = TARGET_COLUMNS.intersection(selected)
    if forbidden:
        raise ValueError(f'Target columns cannot enter prediction features: {sorted(forbidden)}')
    with target_file.open('r', encoding='utf-8-sig', newline='', buffering=1024*1024) as stream:
        reader = csv.reader(stream)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError('Target file is empty and has no feature header') from exc
        if len(header) != len(set(header)):
            raise ValueError('Duplicate input column names prevent safe selection')
        if expected_header is not None and tuple(header) != tuple(expected_header):
            raise ValueError('Input header differs from the frozen feature registry schema')
        absent = set(selected).difference(header)
        if absent:
            raise ValueError(f'Requested feature columns are absent: {sorted(absent)}')
        indices = [header.index(name) for name in selected]
        batch: list[tuple[str, ...]] = []
        batch_start = 0
        for row_number, row in enumerate(reader):
            if len(row) != len(header):
                raise ValueError(f'Malformed row width at row {row_number + 2}')
            batch.append(tuple(row[i] for i in indices))
            if len(batch) == batch_size:
                yield batch_start, batch
                batch_start = row_number + 1
                batch = []
        if batch:
            yield batch_start, batch


def iter_final_evaluation_labels(
    target_file: Path,
    *,
    manifest_path: Path,
    repository_root: Path,
    direction: str,
    source_file: Path,
    config_file: Path,
    source_stage_manifest: Path,
    source_e1_manifest: Path,
    source_e1_results: Path,
    source_gate_interpretation: Path,
    feature_registry: Path,
    family_registry: Path,
    family_pair_matrix: Path,
    validated_locks: ValidatedTransferLocks,
    expected_header: Sequence[str] | None = None,
) -> Iterator[tuple[int, str, str]]:
    """Yield target labels only after a matching committed freeze record."""
    for start, batch in iter_final_evaluation_label_batches(
        target_file,
        manifest_path=manifest_path,
        repository_root=repository_root,
        direction=direction,
        source_file=source_file,
        config_file=config_file,
        source_stage_manifest=source_stage_manifest,
        source_e1_manifest=source_e1_manifest,
        source_e1_results=source_e1_results,
        source_gate_interpretation=source_gate_interpretation,
        feature_registry=feature_registry,
        family_registry=family_registry,
        family_pair_matrix=family_pair_matrix,
        validated_locks=validated_locks,
        expected_header=expected_header,
        batch_size=1,
    ):
        for offset, (label, attack) in enumerate(batch):
            yield start + offset, label, attack


def iter_final_evaluation_label_batches(
    target_file: Path,
    *,
    manifest_path: Path,
    repository_root: Path,
    direction: str,
    source_file: Path,
    config_file: Path,
    source_stage_manifest: Path,
    source_e1_manifest: Path,
    source_e1_results: Path,
    source_gate_interpretation: Path,
    feature_registry: Path,
    family_registry: Path,
    family_pair_matrix: Path,
    validated_locks: ValidatedTransferLocks,
    expected_header: Sequence[str] | None = None,
    batch_size: int = 8192,
) -> Iterator[tuple[int, list[tuple[str, str]]]]:
    """Yield bounded binary/family label batches after both transfer locks pass."""
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1:
        raise ValueError('batch_size must be a positive integer')
    root = repository_root.resolve()
    if (not isinstance(validated_locks, ValidatedTransferLocks)
            or validated_locks.directions != CORE_TRANSFER_DIRECTIONS
            or direction not in validated_locks.directions
            or validated_locks.repository_root != str(root)
            or validated_locks.head_commit != _git(root, 'rev-parse', 'HEAD')
            or validated_locks.manifest_sha256.get(direction) != sha256_file(manifest_path)):
        raise ValueError('Both direction manifests must validate before target labels are available')
    verify_freeze_manifest(
        manifest_path,
        repository_root=repository_root,
        direction=direction,
        source_file=source_file,
        target_file=target_file,
        config_file=config_file,
        source_stage_manifest=source_stage_manifest,
        source_e1_manifest=source_e1_manifest,
        source_e1_results=source_e1_results,
        source_gate_interpretation=source_gate_interpretation,
        feature_registry=feature_registry,
        family_registry=family_registry,
        family_pair_matrix=family_pair_matrix,
    )
    with target_file.open('r', encoding='utf-8-sig', newline='', buffering=1024*1024) as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if expected_header is not None and tuple(header) != tuple(expected_header):
            raise ValueError('Evaluation header differs from the frozen feature registry schema')
        if header.count('Label') != 1 or header.count('Attack') != 1:
            raise ValueError('Target file must have exactly one Label and Attack column')
        li, ai = header.index('Label'), header.index('Attack')
        batch: list[tuple[str, str]] = []
        batch_start = 0
        for row_number, row in enumerate(reader):
            if len(row) != len(header):
                raise ValueError(f'Malformed target row width at row {row_number + 2}')
            batch.append((row[li], row[ai]))
            if len(batch) == batch_size:
                yield batch_start, batch
                batch_start = row_number + 1
                batch = []
        if batch:
            yield batch_start, batch
