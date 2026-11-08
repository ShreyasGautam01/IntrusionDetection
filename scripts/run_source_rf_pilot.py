"""Run one locked, source-only UNSW RF pilot seed; never opens CIC2018."""
from __future__ import annotations
import argparse, json, hashlib, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss, accuracy_score

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed/source-e1-lock-1'
CONFIG=ROOT/'reports/nf_v3_audit/source_e1_config.json'

def cal_split(row):
    h=hashlib.sha256(b'source-e1-cal-v1\x00'+row.tobytes()).digest()
    return int.from_bytes(h[:8],'big')%100 < 50

def risk_metrics(y, score, yhat, disagreement):
    errors=(yhat!=y)
    miss=(y==1)&(yhat==0)
    result={
      'detector':{
        'accuracy':float(accuracy_score(y,yhat)),
        'attack_auprc':float(average_precision_score(y,score)),
        'attack_auroc':float(roc_auc_score(y,score)),
        'attack_miss_rows':int(miss.sum()),
        'generic_error_rows':int(errors.sum()),
        'brier_score':float(brier_score_loss(y,score)),
      },
      'reliability':{}
    }
    for name,risk in [('confidence',1.0-np.maximum(score,1.0-score)),('rf_disagreement',disagreement)]:
        entry={'generic_error_auprc':float(average_precision_score(errors.astype(np.uint8),risk)),
               'attack_miss_auprc':float(average_precision_score(miss.astype(np.uint8),risk)),
               'attack_miss_capture':{}}
        order=np.argsort(-risk,kind='mergesort')
        for budget in (0.01,0.05,0.10):
            n=max(1,int(np.ceil(len(y)*budget)))
            entry['attack_miss_capture'][str(budget)]=float(miss[order[:n]].sum()/max(1,int(miss.sum())))
        result['reliability'][name]=entry
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,required=True,choices=range(10))
    args=ap.parse_args(); seed=args.seed
    out=ROOT/f'data/processed/source-e1-lock-1/seed-{seed}'
    if out.exists(): raise SystemExit(f'Refusing to overwrite {out}')
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
    if cfg['target']['features_accessed'] or cfg['target']['labels_accessed']:
        raise SystemExit('Target access is enabled in configuration')
    xtr=np.load(DATA/'train_X.npy',mmap_mode='r'); ytr=np.load(DATA/'train_y.npy',mmap_mode='r')
    xcal=np.load(DATA/'calibration_X.npy',mmap_mode='r'); ycal=np.load(DATA/'calibration_y.npy',mmap_mode='r')
    xte=np.load(DATA/'source_test_X.npy',mmap_mode='r'); yte=np.load(DATA/'source_test_y.npy',mmap_mode='r')
    mask=np.fromiter((cal_split(row) for row in xcal),dtype=np.bool_,count=len(xcal))
    if mask.all() or not mask.any(): raise SystemExit('Calibration split produced an empty partition')
    estimator=RandomForestClassifier(n_estimators=200,min_samples_leaf=5,criterion='gini',max_depth=None,
        min_samples_split=2,min_weight_fraction_leaf=0.0,max_features='sqrt',max_leaf_nodes=None,
        min_impurity_decrease=0.0,bootstrap=True,oob_score=False,n_jobs=1,random_state=seed,
        verbose=0,warm_start=False,class_weight=None,ccp_alpha=0.0,max_samples=None)
    started=time.monotonic()
    estimator.fit(xtr,ytr)
    train_seconds=time.monotonic()-started
    raw_cal=estimator.predict_proba(xcal[mask])[:,1]
    raw_cal=np.clip(raw_cal,1e-7,1-1e-7)
    cal_logits=np.log(raw_cal/(1-raw_cal)).reshape(-1,1)
    calibrator=LogisticRegression(C=1.0,solver='lbfgs',max_iter=1000,random_state=seed)
    calibrator.fit(cal_logits,ycal[mask])
    raw_test=estimator.predict_proba(xte)[:,1]
    clipped=np.clip(raw_test,1e-7,1-1e-7)
    logits=np.log(clipped/(1-clipped)).reshape(-1,1)
    calibrated=calibrator.predict_proba(logits)[:,1]
    yhat=(calibrated>=0.5).astype(np.uint8)
    votes=np.zeros((len(yte),2),dtype=np.uint8)
    for tree in estimator.estimators_:
        prediction=tree.predict(xte).astype(np.uint8,copy=False)
        