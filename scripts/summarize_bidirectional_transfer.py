from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from scipy.stats import wilcoxon
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/'reports/nf_v3_audit'; OUT=ROOT/'reports/nf_v3_transfer_analysis_v1'
SIGNALS=('confidence','random_forest_disagreement','feature_space_distance','split_conformal','isolation_forest'); BUDGETS=('0.01','0.05','0.1')
def boot_ci(x,seed=20261117,n=20000):
 x=np.asarray(x,float); g=np.random.default_rng(seed); means=x[g.integers(0,len(x),(n,len(x)))].mean(1); return [float(np.quantile(means,.025)),float(np.quantile(means,.975))]
def summary(x):
 x=np.asarray(x,float); return {'n':len(x),'mean':float(x.mean()),'median':float(np.median(x)),'sd':float(x.std(ddof=1)),'min':float(x.min()),'max':float(x.max()),'bootstrap_mean_95ci':boot_ci(x)}
reports={d:json.loads((A/f'target_transfer_evaluation_{d.replace("-","_")}.json').read_text()) for d in ('unsw-to-cic','cic-to-unsw')}
per=[]
for d,rep in reports.items():
 for row in rep['per_seed']:
  seed=row['seed']; det=row['detector']
  for sig in SIGNALS:
   rel=row['reliability'][sig]; per.append({'direction':d,'seed':seed,'signal':sig,'attack_miss_auprc':rel['attack_miss_auprc'],'generic_error_auprc':rel['generic_error_auprc'],**{f'capture_{b}':rel['review_budgets'][b]['attack_miss_capture'] for b in BUDGETS},**{f'captured_{b}':rel['review_budgets'][b]['attack_miss_rows_captured'] for b in BUDGETS},'attack_miss_rows':rel['attack_miss_rows'],'generic_error_rows':det['generic_error_rows'],'attack_rows':det['attack_rows']})
summary_rows=[]
for d in reports:
 for sig in SIGNALS:
  rows=[x for x in per if x['direction']==d and x['signal']==sig]
  for met in ('attack_miss_auprc','generic_error_auprc','capture_0.01','capture_0.05','capture_0.1'):
   vals=[x[met] for x in rows if x[met] is not None]
   summary_rows.append({'direction':d,'signal':sig,'metric':met,**summary(vals)})
paired=[]
for d in reports:
 for sig in SIGNALS[1:]:
  x=np.array([next(z['attack_miss_auprc'] for z in per if z['direction']==d and z['signal']==sig and z['seed']==s) for s in range(10)])
  y=np.array([next(z['attack_miss_auprc'] for z in per if z['direction']==d and z['signal']=='confidence' and z['seed']==s) for s in range(10)])
  dif=x-y
  try: test=wilcoxon(dif,alternative='two-sided',method='auto'); stat=float(test.statistic); p=float(test.pvalue)
  except ValueError: stat=None;p=1.0
  paired.append({'direction':d,'metric':'attack_miss_auprc','contrast':f'{sig} minus confidence','paired_differences':dif.tolist(),'mean_difference':float(dif.mean()),'median_difference':float(np.median(dif)),'bootstrap_mean_95ci':boot_ci(dif,seed=20261200+SIGNALS.index(sig)),'wilcoxon_statistic':stat,'wilcoxon_p_unadjusted':p})
for sig in SIGNALS:
 x=np.array([next(z['attack_miss_auprc'] for z in per if z['direction']=='cic-to-unsw' and z['signal']==sig and z['seed']==s) for s in range(10)])
 y=np.array([next(z['attack_miss_auprc'] for z in per if z['direction']=='unsw-to-cic' and z['signal']==sig and z['seed']==s) for s in range(10)])
 paired.append({'direction':'paired-directions','metric':'attack_miss_auprc','contrast':f'cic-to-unsw minus unsw-to-cic: {sig}','paired_differences':(x-y).tolist(),'mean_difference':float((x-y).mean()),'median_difference':float(np.median(x-y)),'bootstrap_mean_95ci':boot_ci(x-y,seed=20261300+SIGNALS.index(sig))})
report={'report_id':'bidirectional-transfer-primary-summary-v1','primary_endpoint':'attack_miss_auprc','operational_primary':'attack_miss_capture at 5%','directions':list(reports),'n_matched_seeds':10,'per_seed':per,'summaries':summary_rows,'paired_comparisons':paired,'cautions':['Seeds, not rows, are the comparison units.','Ten seeds provide limited inferential precision; treat tests and intervals as descriptive.','Generic-error AUROC, family-level, target calibration, conformal coverage and selective residual diagnostics require supplemental analysis.'],'target_labels_used_only_for_offline_evaluation':True}
(OUT/'primary_results_v1.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
import csv
with (OUT/'primary_results_per_seed.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=list(per[0]));w.writeheader();w.writerows(per)
print('wrote',len(per),'seed-signal rows and',len(summary_rows),'summary rows')
for d in reports:
 vals=[(s,round(next(x['attack_miss_auprc'] for x in per if x['direction']==d and x['signal']==s and x['seed']==0),4)) for s in SIGNALS]
 print(d, vals)
