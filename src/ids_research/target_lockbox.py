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
    source_file: Path,
    target_file: Path,
    config_file: Path,
    feature_registry: Path,
) -> dict:
    """Validate that the lock record is committed and binds exact inputs."""
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    required = ('status', 'lock_commit', 'source_sha256', 'target_sha256', 'config_sha256',
                'feature_registry_sha256', 'source_dataset', 'target_dataset')
    missing = [key for key in required if not manifest.get(key)]
    if missing:
        raise ValueError(f'Freeze manifest lacks required fields: {missing}')
    if manifest['status'] != 'frozen':
        raise ValueError('Target labels remain sealed until status is frozen')
    if sha256_file(source_file) != manifest['source_sha256']:
        raise ValueError('Source dataset hash differs from the frozen manifest')
    if sha256_file(target_file) != manifest['target_sha256']:
        raise ValueError('Target dataset hash differs from the frozen manifest')
    if sha256_file(config_file) != manifest['config_sha256']:
        raise ValueError('Experiment configuration differs from the frozen manifest')
    if sha256_file(feature_registry) != manifest['feature_registry_sha256']:
        raise ValueError('Feature registry differs from the frozen manifest')
    root = repository_root.resolve()
    manifest_abs = manifest_path.resolve()
    try:
        manifest_rel = manifest_abs.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError('Freeze manifest must be stored inside the repository') from exc
    head = _git(root, 'rev-parse', 'HEAD')
    committed_manifest = _git(root, 'show', f'HEAD:{manifest_rel}')
    if _git(root, 'status', '--porcelain', '--', manifest_rel):
        raise ValueError('Freeze manifest is uncommitted or differs from the committed record')
    if json.loads(committed_manifest) != manifest:
        raise ValueError('Freeze manifest differs from its committed version')
    _git(root, 'merge-base', '--is-ancestor', manifest['lock_commit'], head)
    return manifest


def iter_target_features(
    target_file: Path,
    feature_columns: Sequence[str],
) -> Iterator[tuple[int, dict[str, str]]]:
    """Yield row number and features only; target columns are never returned."""
    selected = tuple(feature_columns)
    if not selected:
        raise ValueError('At least one explicit feature column is required')
    forbidden = TARGET_COLUMNS.intersection(selected)
    if forbidden:
        raise ValueError(f'Target columns cannot enter prediction features: {sorted(forbidden)}')
    with target_file.open('r', encoding='utf-8-sig', newline='', buffering=1024*1024) as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if len(header) != len(set(header)):
            raise ValueError('Duplicate input column names prevent safe selection')
        absent = set(selected).difference(header)
        if absent:
            raise ValueError(f'Requested feature columns are absent: {sorted(absent)}')
        indices = [header.index(name) for name in selected]
        for row_number, row in enumerate(reader):
            if len(row) != len(header):
                raise ValueError(f'Malformed row width at row {row_number + 2}')
            yield row_number, dict(zip(selected, (row[i] for i in indices)))


def iter_final_evaluation_labels(
    target_file: Path,
    *,
    manifest_path: Path,
    repository_root: Path,
    source_file: Path,
    config_file: Path,
    feature_registry: Path,
) -> Iterator[tuple[int, str, str]]:
    """Yield target labels only after a matching committed freeze record."""
    verify_freeze_manifest(
        manifest_path,
        repository_root=repository_root,
        source_file=source_file,
        target_file=target_file,
        config_file=config_file,
        feature_registry=feature_registry,
    )
    with target_file.open('r', encoding='utf-8-sig', newline='', buffering=1024*1024) as stream:
        reader = csv.reader(stream)
        header = next(reader)
        if header.count('Label') != 1 or header.count('Attack') != 1:
            raise ValueError('Target file must have exactly one Label and Attack column')
        li, ai = header.index('Label'), header.index('Attack')
        for row_number, row in enumerate(reader):
            if len(row) != len(header):
                raise ValueError(f'Malformed target row width at row {row_number + 2}')
            yield row_number, row[li], row[ai]
