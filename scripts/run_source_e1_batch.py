"""Run source-only RF seeds with bounded parallelism and persistent logs."""
from __future__ import annotations
import argparse, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/'scripts/run_source_rf_pilot.py'
DATA=ROOT/'data/processed/source-e1-lock-1'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seeds',nargs='+',type=int,required=True)
    ap.add_argument('--parallel',type=int,default=3)
    a=ap.parse_args()
    if a.parallel<1: raise SystemExit('--parallel must be positive')
    if len(a.seeds)!=len(set(a.seeds)) or any(s not in range(10) for s in a.seeds):
        raise SystemExit('Seeds must be unique integers in 0..9')
    if not (DATA/'stage_manifest.json').is_file(): raise SystemExit('Source E1 arrays are not staged')
    logs=DATA/'runlogs'; logs.mkdir(exist_ok=True)
    pending=list(a.seeds); active={}
    def start(seed):
        out=(logs/f'seed-{seed}.stdout.log').open('w',encoding='utf-8')
        err=(logs/f'seed-{seed}.stderr.log').open('w',encoding='utf-8')
        proc=subprocess.Popen([sys.executable,str(RUNNER),'--seed',str(seed)],cwd=ROOT,stdout=out,stderr=err)
        active[seed]=(proc,out,err)
        print(f'started seed {seed}, pid={proc.pid}',flush=True)
    while pending and len(active)<a.parallel: start(pending.pop(0))
    failed=[]
    while active:
        for seed,(proc,out,err) in list(active.items()):
            code=proc.poll()
            if code is None: continue
            out.close(); err.close(); del active[seed]
            result=DATA/f'seed-{seed}'/'metrics.json'
            if code==0 and result.is_file(): print(f'completed seed {seed}',flush=True)
            else:
                failed.append((seed,code))
                print(f'FAILED seed {seed}, exit={code}; see runlogs/seed-{seed}.stderr.log',flush=True)
                for other,(p,o,e) in active.items(): p.terminate()
                for other,(p,o,e) in list(active.items()): p.wait(); o.close(); e.close()
                active.clear(); pending.clear(); break
        while pending and len(active)<a.parallel and not failed: start(pending.pop(0))
        if active: time.sleep(2)
    if failed: raise SystemExit(f'Source E1 seed failures: {failed}')
    print('requested seeds completed',flush=True)
if __name__=='__main__': main()
