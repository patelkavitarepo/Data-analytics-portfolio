"""Independent NumPy/manual discovery check; run from project root with PYTHONPATH=.

First argument is the existing D003 clean run; stdout is JSON, never pair ranks.
"""
import sys
import json,math
from pathlib import Path
import numpy as np,pandas as pd
from daily_study.feasibility import stress_states,potential_context,pair_count_summary,verify_inputs
from daily_study.declines import Context
root=Path(sys.argv[1])
design=json.loads(Path('research/declines-D004/design.json').read_text())
frame=pd.read_parquet(root/'conservative.parquet',columns=['date','stock','log_return'],filters=[('date','<=',pd.Timestamp('2015-12-31')),('date','>=',pd.Timestamp('2013-02-08'))]).pivot(index='date',columns='stock',values='log_return').sort_index()
columns=np.flatnonzero(frame.notna().any().to_numpy()); selected=columns[np.linspace(0,len(columns)-1,4,dtype=int)]
values=frame.abs(); checks=0
manual_primary=None
for h in [60,252]:
 for q in [.9,.95]:
  for coverage in [1.,.8]:
   production=stress_states(values,h,q,coverage)
   manual_valid=np.zeros((len(frame),len(selected)),bool); manual_stress=manual_valid.copy()
   for j,col in enumerate(selected):
    x=values.iloc[:,col].to_numpy()
    for t,current in enumerate(x):
     history=x[max(0,t-h):t];history=history[np.isfinite(history)]
     if len(history)>=math.ceil(h*coverage) and np.isfinite(current):
      threshold=np.quantile(history,q,method='linear')
      if threshold>0:
       manual_valid[t,j]=True;manual_stress[t,j]=current>threshold
     assert manual_valid[t,j]==production['valid'][t,col]
     assert manual_stress[t,j]==production['stress'][t,col]
     checks+=1
   if (h,q,coverage)==(60,.9,1.):manual_primary=(manual_valid,manual_stress,production)
context=Context(frame.to_numpy(),design);pair=potential_context(context,selected)
v,s,production=manual_primary
points=[]
for a,b in zip(pair['local_i'],pair['local_j']):
 donors=np.delete(np.expm1(frame.to_numpy()),selected[[a,b]],axis=1)
 valid=np.isfinite(donors);count=valid.sum(axis=1)
 decline=(count>=250)&(((donors<=-.01+1e-12)&valid).sum(axis=1)>=.6*count-1e-12)
 eligible=decline&v[:,a]&v[:,b]
 points.append((int(eligible.sum()),int((eligible&s[:,a]&s[:,b]).sum())))
_,global_decline,_,median=context.states();cut=float(np.median(median[global_decline]))
summary=pair_count_summary(production,pair,cut,5)
for index,key in [(0,'paired_decline_dates'),(1,'joint_stress_dates')]:
 expected=np.quantile([x[index] for x in points],[0,.1,.25,.5,.75,.9,1])
 np.testing.assert_allclose(list(summary[key]['quantiles'].values()),expected)
result=dict(label='actual discovery-only independent verification; no pair ranking or CVRs',
 stock_indices=selected.tolist(),numpy_versus_pandas_state_checks=checks,
 independent_leave_two_out_pair_count_checks=len(points),cleaning_artifact_hashes_verified=verify_inputs(root),
 later_observations_read=False,target_columns_read=False)
print(json.dumps(result,indent=2))
