"""Audit temporal, session, host, and repeated flow-key controls for UNSW-v3."""
import argparse,csv,hashlib,heapq,json,shutil,tempfile
from array import array
from collections import Counter
from datetime import date,datetime,timezone
from pathlib import Path

CHUNK=250_000
def hash_parts(parts):
    h=hashlib.sha256()
    for p in parts: h.update(str(p).encode('utf-8')); h.update(b'\x1f')
    return h.digest()
def split_hash(key):
    b=int.from_bytes(key[:8],'big')%100
    return 'train' if b<60 else 'calibration' if b<80 else 'source_test'
def dump_chunk(items,folder,prefix,n):
    items.sort(); p=folder/f'{prefix}_{n:04d}.jsonl'
    with p.open('w',encoding='utf-8',newline='\n') as f:
        for x in items: f.write(json.dumps(x,separators=(',',':'))+'\n')
    items.clear()
def merged(paths):
    def gen(p):
        with p.open(encoding='utf-8') as f:
            for line in f: yield tuple(json.loads(line))
    yield from heapq.merge(*(gen(p) for p in paths))
def duplicate_summary(paths):
    groups=extra=0; previous=None; count=0
    for row in merged(paths):
        key=row[0]
        if previous is not None and key!=previous:
            if count>1: groups+=1; extra+=count-1
            count=0
        previous=key; count+=1
    if previous is not None and count>1: groups+=1; extra+=count-1
    return {'duplicate_groups':groups,'rows_beyond_first':extra}
def cross_part_overlap(paths):
    groups=0; previous=None; parts=set()
    for row in merged(paths):
        key,part=row
        if previous is not None and key!=previous:
            if len(parts)>1: groups+=1
            parts=set()
        previous=key; parts.add(part)
    if previous is not None and len(parts)>1: groups+=1
    return groups
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--audit-dir',type=Path,default=Path('reports/nf_v3_audit')); ap.add_argument('--work-dir',type=Path,default=None); a=ap.parse_args()
    root=a.audit_dir; inv=json.loads((root/'audit.json').read_text(encoding='utf-8')); ds=next(x for x in inv['datasets'] if x['dataset']=='NF-UNSW-NB15-v3'); path=Path(ds['file']); features=inv['expected_features']
    # Exact empirical order-statistic boundaries on timestamps only.
    starts=array('Q')
    with path.open(encoding='utf-8-sig',newline='',buffering=1024*1024) as f:
        r=csv.reader(f); h=next(r); ix={x:i for i,x in enumerate(h)}
        for row in r:
            if len(row)!=len(h): continue
            try: starts.append(int(float(row[ix['FLOW_START_MILLISECONDS']])))
            except (ValueError,OverflowError): pass
    starts=sorted(starts); n=len(starts); b1=starts[int(.60*n)]; b2=starts[int(.80*n)]
    tmp=Path(tempfile.mkdtemp(prefix='e0-source-',dir=str(a.work_dir or root)))
    try:
        counters=Counter(); daily=Counter(); temporal_chunks=[]; session_chunks=[]; flow_chunks=[]; hosts={'train':set(),'calibration':set(),'source_test':set()}
        tids=sids=fids=0; rowcount=0
        with path.open(encoding='utf-8-sig',newline='',buffering=1024*1024) as f:
            r=csv.reader(f); h=next(r); ix={x:i for i,x in enumerate(h)}; fi=[ix[x] for x in features]
            src_i,dst_i=ix['IPV4_SRC_ADDR'],ix['IPV4_DST_ADDR']; sp_i,dp_i,pr_i=ix['L4_SRC_PORT'],ix['L4_DST_PORT'],ix['PROTOCOL']; si,ei=ix['FLOW_START_MILLISECONDS'],ix['FLOW_END_MILLISECONDS']
            for row in r:
                if len(row)!=len(h): continue
                try: st=int(float(row[si])); en=int(float(row[ei]))
                except (ValueError,OverflowError): continue
                rowcount+=1; day=date.fromordinal(date(1970,1,1).toordinal()+st//86_400_000).isoformat(); daily[day]+=1
                # Time control: complete intervals plus 60-second embargo.
                if st < b1-60_000 and en < b1-60_000: tp='train'
                elif st >= b1+60_000 and en < b2-60_000: tp='calibration'
                elif st >= b2+60_000: tp='source_test'
                else: tp='embargo_excluded'
                counters['temporal_'+tp]+=1
                fk=hash_parts([row[i] for i in fi]).hex(); temporal_chunks.append((fk,tp))
                aep=(row[src_i],row[sp_i]); bep=(row[dst_i],row[dp_i]); endpoints=sorted((aep,bep)); proto=row[pr_i]
                sess=hash_parts([endpoints[0][0],endpoints[0][1],endpoints[1][0],endpoints[1][1],proto]).hex(); sess_part=split_hash(bytes.fromhex(sess)); session_chunks.append((sess,sess_part)); counters['session_rows_'+sess_part]+=1
                flow=hash_parts([*endpoints[0],*endpoints[1],proto,row[si],row[ei]]).hex(); flow_chunks.append((flow,))
                # Host-disjoint sensitivity: hash each endpoint independently;
                # retain only flows whose endpoints land in the same partition.
                hparts=[]
                for ip in (row[src_i],row[dst_i]):
                    hb=int.from_bytes(hash_parts(['e0-host-v1',ip])[:8],'big')%100
                    hparts.append('train' if hb<60 else 'calibration' if hb<80 else 'source_test')
                if hparts[0]==hparts[1]:
                    counters['host_retained_'+hparts[0]]+=1; hosts[hparts[0]].update((row[src_i],row[dst_i]))
                else: counters['host_cross_partition_excluded']+=1
                if len(temporal_chunks)>=CHUNK:
                    dump_chunk(temporal_chunks,tmp,'temporal',tids); tids+=1
                    dump_chunk(session_chunks,tmp,'session',sids); sids+=1
                    dump_chunk(flow_chunks,tmp,'flowkey',fids); fids+=1
        for items,prefix,count in ((temporal_chunks,'temporal',tids),(session_chunks,'session',sids),(flow_chunks,'flowkey',fids)):
            if items: dump_chunk(items,tmp,prefix,count)
        temporal_summary=cross_part_overlap(sorted(tmp.glob('temporal_*.jsonl')))
        session_summary=duplicate_summary(sorted(tmp.glob('session_*.jsonl')))
        flow_summary=duplicate_summary(sorted(tmp.glob('flowkey_*.jsonl')))
        result={'input_sha256':ds['sha256'],'source_rows':rowcount,'temporal_control':{'boundary_method':'start-time order statistics at floor(0.60N) and floor(0.80N), labels not read','b1_ms':b1,'b2_ms':b2,'b1_utc':datetime.fromtimestamp(b1/1000,tz=timezone.utc).isoformat(),'b2_utc':datetime.fromtimestamp(b2/1000,tz=timezone.utc).isoformat(),'embargo_seconds':60,'row_counts':{k:v for k,v in counters.items() if k.startswith('temporal_')},'feature_vector_groups_crossing_temporal_partitions':temporal_summary,'utc_day_row_counts':dict(sorted(daily.items()))},'session_control':{'key':'direction-canonicalized observed endpoint IP/port pairs plus PROTOCOL','split_assignment':'SHA-256 of canonical session key modulo 100 with 60/20/20 thresholds','row_counts_by_split':{k:v for k,v in counters.items() if k.startswith('session_rows_')},'duplicate_session_groups':session_summary['duplicate_groups'],'rows_beyond_first_in_repeated_session_groups':session_summary['rows_beyond_first']},'exact_flow_key_control':{'key':'canonical endpoint IP/port pairs plus PROTOCOL and exact start/end timestamp strings','duplicate_flow_key_groups':flow_summary['duplicate_groups'],'rows_beyond_first_in_duplicate_flow_keys':flow_summary['rows_beyond_first']},'host_disjoint_sensitivity':{'assignment':'SHA-256 of e0-host-v1 salt plus observed IP; modulo 100 with 60/20/20 thresholds; retain flow only if both endpoint IPs map to same partition','retained_row_counts':{k:v for k,v in counters.items() if k.startswith('host_retained_')},'cross_partition_endpoint_flows_excluded':counters['host_cross_partition_excluded'],'distinct_hosts_retained_by_partition':{k:len(v) for k,v in hosts.items()},'host_disjoint_by_construction':True}}
        (root/'e0_source_controls.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    finally: shutil.rmtree(tmp,ignore_errors=True)
if __name__=='__main__': main()
