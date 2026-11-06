"""Stage only the active UNSW source split for source-only E1 using disk-backed arrays."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'reports/nf_v3_audit/source_e1_config.json'
AUDIT=ROOT/'reports/nf_v3_audit/audit.json'
REPLACEMENTS=ROOT/'reports/nf_v3_audit/unsw_train_finite_replacements.json'
E0=ROOT/'reports/nf_v3_audit/e0_results.json'

def file_sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''): digest.update(block)
    return digest.hexdigest()

def digest_vector(row, indices):
    h=hashlib.sha256()
    for i in indices:
        h.update(row[i].encode('utf-8')); h.update(b'\x1f')
    return h.digest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,default=ROOT/'data/processed/source-e1-lock-1')
    args=ap.parse_args()
    if args.output.exists(): raise SystemExit(f'Refusing to overwrite existing staging directory: {args.output}')
    config=json.loads(CONFIG.read_text(encoding='utf-8'))
    audit=json.loads(AUDIT.read_text(encoding='utf-8'))
    finite=json.loads(REPLACEMENTS.read_text(encoding='utf-8'))
    e0=json.loads(E0.read_text(encoding='utf-8'))
    if config['target']['features_accessed'] or config['target']['labels_accessed']:
        raise SystemExit('Source staging config unexpectedly enables target access')
    ds=next(x for x in audit['datasets'] if x['dataset']=='NF-UNSW-NB15-v3')
    if ds['sha256']!=config['source_dataset']['sha256'] or finite['source_file_sha256']!=ds['sha256']:
        raise SystemExit('Source hash bindings disagree across audit/config/replacement artifacts')
    source=Path(ds['file'])
    if not source.is_file(): raise SystemExit(f'Audited source file not found: {source}')
    if file_sha256(source)!=ds['sha256']:
        raise SystemExit('Current UNSW source SHA-256 differs from the completed dataset audit')
    expected_features=audit['expected_features']
    input_features=config['features']['columns']
    if not set(input_features).issubset(expected_features): raise SystemExit('Configured model features are outside the audited 53-feature schema')
    counts=config['partition']['rows']
    partition_names=('train','calibration','source_test')
    expected_partition_counts=e0['partition_row_counts']
    for part in partition_names:
        expected=int(expected_partition_counts[f"NF-UNSW-NB15-v3:{part}"])
        if expected!=int(counts[part]): raise SystemExit(f'{part} count differs between E0 and locked config')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.mkdir()
    arrays={}
    for part in partition_names:
        n=int(counts[part])
        arrays[part]=(np.lib.format.open_memmap(args.output/f'{part}_X.npy',mode='w+',dtype=np.float32,shape=(n,len(input_features))),np.lib.format.open_memmap(args.output/f'{part}_y.npy',mode='w+',dtype=np.int8,shape=(n,)))
    medians=finite['replacement_values']
    replacement_cols=set(medians)
    rows_written={part:0 for part in partition_names}
    with source.open('r',encoding='utf-8-sig',newline='',buffering=1024*1024) as stream:
        reader=csv.reader(stream)
        header=next(reader)
        if len(header)!=len(set(header)): raise SystemExit('Duplicate source headers prevent safe staging')
        if set(expected_features).difference(header): raise SystemExit('Source file does not contain the audited 53-feature schema')
        index={name:i for i,name in enumerate(header)}
        hash_indices=[index[name] for name in expected_features]
        feature_indices=[index[name] for name in input_features]
        label_index=index['Label']
        for row_number,row in enumerate(reader):
            if len(row)!=len(header): raise ValueError(f'Malformed source row width at data row {row_number}')
            bucket=int.from_bytes(digest_vector(row,hash_indices)[:8],'big')%100
            part='train' if bucket<60 else 'calibration' if bucket<80 else 'source_test'
            pos=rows_written[part]
            if pos>=int(counts[part]): raise ValueError(f'Observed more {part} rows than the locked count')
            label=row[label_index].strip()
            if label not in ('0','1'): raise ValueError(f'Unexpected binary Label {label!r} at data row {row_number}')
            values=[]
            for name,i in zip(input_features,feature_indices):
                token=row[i].strip()
                try: value=float(token)
                except ValueError: value=float('nan')
                if not math.isfinite(value):
                    if name not in replacement_cols: raise ValueError(f'Unconfigured nonfinite value in {name} at data row {row_number}')
                    value=float(medians[name])
                values.append(value)
            x,y=arrays[part]
            x[pos,:]=values; y[pos]=int(label)
            rows_written[part]+=1
    if rows_written!={part:int(counts[part]) for part in partition_names}:
        raise ValueError(f'Observed split counts differ from lock: {rows_written}')
    for x,y in arrays.values(): x.flush(); y.flush()
    files={p.name:{'bytes':p.stat().st_size,'sha256':file_sha256(p)} for p in sorted(args.output.glob('*.npy'))}
    manifest={'configuration_id':config['configuration_id'],'source_dataset':config['source_dataset'],'source_file':str(source),'target_data_accessed':False,'target_label_accessed':False,'feature_order':input_features,'partition_rows':rows_written,'dtype':'float32 features; int8 Label','finite_replacements':medians,'files':files}
    (args.output/'stage_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'stage_dir':str(args.output),'partition_rows':rows_written,'feature_count':len(input_features),'staged_bytes':sum(x['bytes'] for x in files.values()),'target_accessed':False},indent=2))
if __name__=='__main__': main()
