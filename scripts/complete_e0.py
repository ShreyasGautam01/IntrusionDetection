"""Bounded-memory E0 checks for the active UNSW/CIC2018 NF-v3 pair."""
from __future__ import annotations
import argparse, csv, hashlib, heapq, json, shutil, tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

CHUNK = 250_000

def vector_key(row, indices):
    h=hashlib.sha256()
    for i in indices:
        h.update(row[i].encode('utf-8')); h.update(b'\x1f')
    return h.hexdigest()

def write_chunk(records, folder, prefix, number):
    records.sort()
    path=folder/f'{prefix}_{number:05d}.jsonl'
    with path.open('w',encoding='utf-8',newline='\n') as f:
        for rec in records: f.write(json.dumps(rec,separators=(',',':'))+'\n')
    records.clear(); return path

def merged(paths):
    def gen(path):
        with path.open('r',encoding='utf-8') as f:
            for line in f: yield tuple(json.loads(line))
    streams=[gen(p) for p in paths]
    yield from heapq.merge(*streams)

def temporal_episodes(paths):
    count=rows=0; sizes=Counter(); previous_end=None
    for t,e in merged(paths):
        t=int(t); e=int(e)
        if previous_end is None or t-previous_end>60_000:
            if previous_end is not None: count+=1; sizes[rows]+=1
            rows=1
        else: rows+=1
        previous_end=max(e,previous_end or e)
    if previous_end is not None: count+=1; sizes[rows]+=1
    return {'gap_threshold_seconds':60,'episode_count':count,'episode_size_histogram_rows_per_episode':{str(k):v for k,v in sorted(sizes.items())}}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--audit-dir',type=Path,default=Path('reports/nf_v3_audit'))
    ap.add_argument('--work-dir',type=Path,default=None)
    a=ap.parse_args(); root=a.audit_dir
    inv=json.loads((root/'audit.json').read_text(encoding='utf-8'))
    active=('NF-UNSW-NB15-v3','NF-CSE-CIC-IDS2018-v3')
    ds={x['dataset']:x for x in inv['datasets'] if x['dataset'] in active}; feats=inv['expected_features']
    temp=Path(tempfile.mkdtemp(prefix='e0-sort-',dir=str(a.work_dir or root)))
    try:
        daily={n:defaultdict(Counter) for n in active}; temporal={}; split_rows=Counter(); all_members={}; cic_labels=[]; attack_chunks={}
        for name in active:
            file=Path(ds[name]['file']); ix=None; members=[]; labels=[]; attacks=[]; mn=mx=None; ordered=True; prev=None; chunk_no=0; attack_chunk_no=0
            with file.open('r',encoding='utf-8-sig',newline='',buffering=1024*1024) as f:
                reader=csv.reader(f); header=next(reader); ix={x:i for i,x in enumerate(header)}; fi=[ix[x] for x in feats]
                for row in reader:
                    if len(row)!=len(header): continue
                    try: t=int(float(row[ix['FLOW_START_MILLISECONDS']])); end=int(float(row[ix['FLOW_END_MILLISECONDS']]))
                    except (ValueError,OverflowError): continue
                    if prev is not None and t<prev: ordered=False
                    prev=t; mn=t if mn is None else min(mn,t); mx=t if mx is None else max(mx,t)
                    day=datetime.fromtimestamp(t/1000,tz=timezone.utc).strftime('%Y-%m-%d')
                    label=row[ix['Label']].strip(); attack=row[ix['Attack']].strip(); benign=(label=='0' or attack.lower()=='benign')
                    daily[name][day]['rows']+=1; daily[name][day]['benign' if benign else 'attack']+=1
                    key=vector_key(row,fi)
                    if name=='NF-UNSW-NB15-v3':
                        bucket=int.from_bytes(bytes.fromhex(key[:16]),'big')%100
                        part='train' if bucket<60 else 'calibration' if bucket<80 else 'source_test'
                    else: part='target_lockbox'
                    members.append((key,part)); split_rows[(name,part)]+=1
                    if name=='NF-CSE-CIC-IDS2018-v3': labels.append((key,label,attack))
                    if not benign: attacks.append((t,end))
                    if len(members)>=CHUNK:
                        write_chunk(members,temp,f'member_{name}',chunk_no); chunk_no+=1
                    if len(labels)>=CHUNK:
                        write_chunk(labels,temp,'cic_labels',len(list(temp.glob('cic_labels_*.jsonl'))));
                    if len(attacks)>=CHUNK:
                        write_chunk(attacks,temp,f'attack_{name}',attack_chunk_no); attack_chunk_no+=1
            member_paths=sorted(temp.glob(f'member_{name}_*.jsonl'))
            if members: write_chunk(members,temp,f'member_{name}',chunk_no)
            if labels: write_chunk(labels,temp,'cic_labels',len(list(temp.glob('cic_labels_*.jsonl'))))
            if attacks: write_chunk(attacks,temp,f'attack_{name}',attack_chunk_no)
            all_members[name]=sorted(temp.glob(f'member_{name}_*.jsonl'))
            temporal[name]={'start_min_ms':mn,'start_max_ms':mx,'start_min_utc':datetime.fromtimestamp(mn/1000,tz=timezone.utc).isoformat(),'start_max_utc':datetime.fromtimestamp(mx/1000,tz=timezone.utc).isoformat(),'input_order_nondecreasing':ordered,'daily_capture_blocks':[{'date':d,**dict(c)} for d,c in sorted(daily[name].items())]}
            temporal[name].update(temporal_episodes(sorted(temp.glob(f'attack_{name}_*.jsonl'))))
        # Conflict groups: sorted unique triples let us count distinct labels
        # per feature vector without retaining the table in RAM.
        groups=Counter(); prevkey=None; ls=set(); ats=set()
        for key,label,attack in merged(sorted(temp.glob('cic_labels_*.jsonl'))):
            if prevkey is not None and key!=prevkey:
                if len(ls)>1: groups['Label']+=1
                if len(ats)>1: groups['Attack']+=1
                if len(ls)>1 or len(ats)>1: groups['either']+=1
                ls=set(); ats=set()
            prevkey=key; ls.add(label); ats.add(attack)
        if prevkey is not None:
            if len(ls)>1: groups['Label']+=1
            if len(ats)>1: groups['Attack']+=1
            if len(ls)>1 or len(ats)>1: groups['either']+=1
        # Merge sorted membership streams to count unique exact vectors shared
        # across source partitions or with the complete target lockbox.
        src=iter(merged(all_members['NF-UNSW-NB15-v3'])); tgt=iter(merged(all_members['NF-CSE-CIC-IDS2018-v3']))
        overlaps=Counter(); next_src=next(src,None); next_tgt=next(tgt,None)
        while next_src is not None:
            k=next_src[0]; parts=set()
            while next_src is not None and next_src[0]==k:
                parts.add(next_src[1]); next_src=next(src,None)
            if len(parts)>1: overlaps['UNSW_cross_partition']+=1
            while next_tgt is not None and next_tgt[0]<k:
                target_key=next_tgt[0]
                while next_tgt is not None and next_tgt[0]==target_key: next_tgt=next(tgt,None)
            if next_tgt is not None and next_tgt[0]==k:
                overlaps['UNSW_source_to_CIC_lockbox']+=1
                for p in parts: overlaps[f'{p}__CIC_lockbox']+=1
                while next_tgt is not None and next_tgt[0]==k: next_tgt=next(tgt,None)
        for key in ('Label','Attack','either'): groups.setdefault(key,0)
        overlap_names=['UNSW_cross_partition','UNSW_source_to_CIC_lockbox','train__CIC_lockbox','calibration__CIC_lockbox','source_test__CIC_lockbox']
        for key in overlap_names: overlaps.setdefault(key,0)
        result={'generated_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':{n:ds[n]['sha256'] for n in active},'split_assignment':'Label-blind SHA-256 of canonical raw 53-feature strings. UNSW first 8 digest bytes modulo 100: 0-59 train, 60-79 calibration, 80-99 source_test. CIC all rows target_lockbox.','partition_row_counts':{f'{n}:{p}':c for (n,p),c in sorted(split_rows.items())},'temporal':temporal,'CIC_duplicate_feature_vector_conflict_groups':dict(groups),'exact_feature_vector_overlap_unique_vectors':dict(overlaps)}
        (root/'e0_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    finally: shutil.rmtree(temp,ignore_errors=True)
if __name__=='__main__': main()
