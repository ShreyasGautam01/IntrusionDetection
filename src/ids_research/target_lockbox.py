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
from pathlib import Path
from typing import Iterator, Sequence

TARGET_COLUMNS = frozenset({'Label', 'Attack'})


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
        'feature_registry_sha256', 'family_registry_sha256',
        'family_pair_matrix_sha256', 'source_dataset', 'target_dataset',
        'feature_order', 'target_labels_read', 'software', 'benchmarks',
    )
    missing = [key for key in required if key not in manifest
               or manifest[key] is None or manifest[key] == '']
    if missing:
        raise ValueError(f'Freeze manifest lacks required fields: {missing}')
    if manifest['status'] != 'frozen':
        raise ValueError('Target labels remain sealed until status is frozen')
    if manifest['direction'] != direction:
        raise ValueError('Freeze manifest direction differs from the requested direction')
    if manifest['target_labels_read'] is not False:
        raise ValueError('Freeze manifest reports target-label access before the lock')
    if sha256_file(source_file) != manifest['source_sha256']:
        raise ValueError('Source dataset hash differs from the frozen manifest')
    if sha256_file(target_file) != manifest['target_sha256']:
        raise ValueError('Target dataset hash differs from the frozen manifest')
    bound_files = (
        (config_file, 'config_sha256', 'Experiment configuration'),
        (source_stage_manifest, 'source_stage_manifest_sha256', 'Source stage manifest'),
        (source_e1_manifest, 'source_e1_manifest_sha256', 'Source E1 manifest'),
        (source_e1_results, 'source_e1_results_sha256', 'Source E1 results'),
        (feature_registry, 'feature_registry_sha256', 'Feature registry'),
        (family_registry, 'family_registry_sha256', 'Family registry'),
        (family_pair_matrix, 'family_pair_matrix_sha256', 'Family pair matrix'),
    )
    for path, key, description in bound_files:
        if sha256_file(path) != manifest[key]:
            raise ValueError(f'{description} differs from the frozen manifest')

    config = json.loads(config_file.read_text(encoding='utf-8'))
    stage = json.loads(source_stage_manifest.read_text(encoding='utf-8'))
    source_manifest = json.loads(source_e1_manifest.read_text(encoding='utf-8'))
    source_results = json.loads(source_e1_results.read_text(encoding='utf-8'))
    if (manifest['source_dataset'] != config['source_dataset']['name']
            or manifest['target_dataset'] != config['target']['dataset']):
        raise ValueError('Freeze manifest source/target dataset names differ from direction config')
    if manifest['feature_order'] != config['features']['columns'] or len(manifest['feature_order']) != 46:
        raise ValueError('Freeze manifest feature order differs from the frozen E1 configuration')
    stage_target_read = stage.get('target_file_read', stage.get('target_data_accessed', False))
    stage_labels_read = stage.get('target_labels_read', stage.get('target_label_accessed', False))
    if (stage.get('configuration_id') != config['configuration_id']
            or stage.get('configuration_sha256') != manifest['config_sha256']
            or stage.get('feature_order') != manifest['feature_order']
            or stage_target_read is not False or stage_labels_read is not False):
        raise ValueError('Source-stage provenance differs from the direction configuration')
    source_feature_order = source_manifest.get('feature_order')
    if source_feature_order is None:
        source_feature_order = source_manifest.get('features', {}).get('order')
    source_dataset_info = source_manifest.get('source_dataset', {})
    if (source_manifest.get('configuration_id') != config['configuration_id']
            or source_manifest.get('configuration_sha256') != manifest['config_sha256']
            or source_feature_order != manifest['feature_order']
            or source_dataset_info.get('name') != manifest['source_dataset']
            or source_dataset_info.get('sha256') != manifest['source_sha256']):
        raise ValueError('Source E1 manifest differs from the direction configuration')
    if (source_results.get('direction') != direction
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

    with feature_registry.open('r', encoding='utf-8-sig', newline='') as stream:
        registry_rows = list(csv.DictReader(stream))
    for dataset in (manifest['source_dataset'], manifest['target_dataset']):
        rows = [r for r in registry_rows if r['dataset'] == dataset]
        predictors = sorted((r for r in rows if r['transfer_role'] == 'predictor'),
                            key=lambda r: int(r['e1_feature_order']))
        if [r['raw_column'] for r in predictors] != manifest['feature_order']:
            raise ValueError(f'Feature registry predictor order differs for {dataset}')
        if any(r['used_for_prediction'] not in ('yes', 'no') for r in rows):
            raise ValueError(f'Feature registry contains an invalid prediction role for {dataset}')
    with family_registry.open('r', encoding='utf-8-sig', newline='') as stream:
        families = list(csv.DictReader(stream))
    if not families or any(r['unseen_family_claim'] != 'withheld' for r in families):
        raise ValueError('Family registry makes an unreviewed unseen-family claim')

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
    _git(root, 'merge-base', '--is-ancestor', manifest['lock_commit'], head)
    if _git(root, 'status', '--porcelain'):
        raise ValueError('Freeze manifest validation requires a clean tracked checkout')
    return manifest


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
    feature_registry: Path,
    family_registry: Path,
    family_pair_matrix: Path,
    expected_header: Sequence[str] | None = None,
) -> Iterator[tuple[int, str, str]]:
    """Yield target labels only after a matching committed freeze record."""
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
        for row_number, row in enumerate(reader):
            if len(row) != len(header):
                raise ValueError(f'Malformed target row width at row {row_number + 2}')
            yield row_number, row[li], row[ai]
