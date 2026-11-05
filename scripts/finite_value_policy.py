"""Source-only finite-value policy for the active UNSW/CIC2018 pilot.

This module fits replacement statistics from UNSW training membership only.
The same serialized mapping is passed to calibration, source-test, and target
inference. It does not read labels or write transformed datasets.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from pathlib import Path

REPLACEMENT_COLUMNS=('SRC_TO_DST_SECOND_BYTES','DST_TO_SRC_SECOND_BYTES')

def row_digest(row, indices):
    h=hashlib.sha256()
    for i in indices:
        h.update(row[i].encode('utf-8')); h.update(b'\x1f')
    return h.digest()

def missing_kind(value):
    if value is None or value.strip()=='': return 'empty'
    token=value.strip().casefold()
    if token in ('na','n/a','null','none','<na>'): return 'null_marker'
    if token in ('nan','+nan','-nan'): return 'nan'
    if token in ('inf','+inf','infinity','+infinity'): return 'positive_inf'
    if token in ('-inf','-infinity'): return 'negative_inf'
    return None

def parse_finite(value):
    if missing_kind(value) is not None: return None
    try: number=float(value)
    except ValueError: raise ValueError(f'Invalid numeric token: {value!r}')
    return number if math.isfinite(number) else None

def fit_from_unsw_csv(path: Path, expected_sha256: str):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): digest.update(block)
    if digest.hexdigest()!=expected_sha256: raise ValueError('UNSW source SHA-256 does not match the audited file')
    values={c:[] for c in REPLACEMENT_COLUMNS}; missing={c:{k:0 for k in ('empty','null_marker','nan','positive_inf','negative_inf','other_nonfinite')} for c in REPLACEMENT_COLUMNS}; train_rows=0
    with path.open('r',encoding='utf-8-sig',newline='',buffering=1024*1024) as f:
        reader=csv.reader(f); header=next(reader); ix={v:i for i,v in enumerate(header)}
        fi=[ix[x] for x in __import__('json').loads(Path('reports/nf_v3_audit/audit.json').read_text(encoding='utf-8'))['expected_features']]
        cols={c:ix[c] for c in REPLACEMENT_COLUMNS}
        for row in reader:
            if len(row)!=len(header): continue
            bucket=int.from_bytes(row_digest(row,fi)[:8],'big')%100
            if bucket>=60: continue
            train_rows+=1
            for col,i in cols.items():
                x=parse_finite(row[i])
                if x is None:
                    kind=missing_kind(row[i]) or 'other_nonfinite'; missing[col][kind]+=1
                else: values[col].append(x)
    medians={}
    for col,xs in values.items():
        medians[col]=float(statistics.median(xs)) if xs else 0.0
    return {'policy':'empty, null markers, NaN, and +/-Inf -> finite-value median fitted on deterministic UNSW train partition; all-empty fallback 0.0','source_file_sha256':expected_sha256,'source_dataset':'NF-UNSW-NB15-v3','split_rule':'SHA-256 of canonical raw 53 feature strings; first 8 digest bytes modulo 100; 0-59 train, 60-79 calibration, 80-99 source_test','source_train_rows':train_rows,'target_labels_read':False,'replacement_values':medians,'source_train_nonfinite_or_empty_counts':missing,'fallback_used':{c:(len(values[c])==0) for c in REPLACEMENT_COLUMNS}}

def apply_value(raw: str, replacement: float) -> float:
    """Use the frozen fitted replacement; never estimate from inference rows."""
    x=parse_finite(raw)
    return replacement if x is None else x

def main():
    p=argparse.ArgumentParser(); p.add_argument('--source',type=Path,default=None); p.add_argument('--output',type=Path,default=Path('reports/nf_v3_audit/unsw_train_finite_replacements.json')); a=p.parse_args()
    inv=json.loads(Path('reports/nf_v3_audit/audit.json').read_text(encoding='utf-8'))
    ds=next(x for x in inv['datasets'] if x['dataset']=='NF-UNSW-NB15-v3')
    result=fit_from_unsw_csv(a.source or Path(ds['file']),ds['sha256'])
    a.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
if __name__=='__main__': main()
