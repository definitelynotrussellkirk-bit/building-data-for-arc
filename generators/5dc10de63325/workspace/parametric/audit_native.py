#!/usr/bin/env python3
"""Bounded family audit; execute through review.py with the protected runtime."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cyan_audit_adapter',HERE/'adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)

def run(seeds=16):
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    if type(seeds) is not int or not 1 <= seeds <= 64: raise ValueError('seeds must be in 1..64')
    root=find_root(__file__); failures=[]; episodes=0; pairs=0; unique=set(); buckets=set(); sizes=set(); policies=set()
    for seed in range(seeds):
        for demos in (4,5,6):
            for setting in A.SETTINGS:
                ep=A.generate(seed,{'fill_order':setting},demos,4)
                check=A.teaching(ep); policies.add(check['policies']); episodes+=1
                if not check['passed']: failures.append({'seed':seed,'demos':demos,'setting':setting,'teaching':check})
                for split in ('train','test'):
                    for p in ep[split]:
                        g=p['input']; pairs+=1; unique.add(hashlib.sha256(json.dumps(g).encode()).hexdigest()); sizes.add((len(g),len(g[0])))
                        buckets.add((sum(v==8 for row in g for v in row)//4,max(A.cyan_sizes(g),default=0)//4))
                for i in range(4):
                    view=A.public_turn(ep,i)
                    if set(view)!= {'train','test'} or len(view['test'])!=1 or set(view['test'][0])!= {'input'}:
                        failures.append({'kind':'public projection'})
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');executions=[]
    try:
        for setting in A.SETTINGS:
            ep=A.generate(17,{'fill_order':setting},4,4)
            for split in ('train','test'):
                for i,p in enumerate(ep[split]):
                    actual=apply(ep['program_solution'],p['input'])
                    if actual != p['output']: failures.append({'kind':'racket_parity','setting':setting,'split':split,'pair':i})
                    executions.append({'setting':setting,'split':split,'index':i,'input':p['input'],'output':actual})
        ep=A.generate(0,{'fill_order':'largest_component_count'},4,4)
        direct=A.program({'fill_order':'bottom_row_first'}); relay=ep['program_solution']; regression=[]
        for split,ix in [('train',0),('train',1),('train',2),('train',3),('test',1)]:
            p=ep[split][ix]; a=apply(direct,p['input']); b=apply(relay,p['input'])
            regression.append({'split':split,'index':ix,'input':p['input'],'global':a,'largest_component':b,'equal':a==b})
        if not all(x['equal'] for x in regression[:3]) or regression[3]['equal'] or regression[4]['equal']:
            failures.append({'kind':'teaching_regression'})
    finally: bridge.close()
    return {'schema':'task-native-cyan-audit-v1','task_id':A.TASK,'seeds':seeds,'demo_counts':[4,5,6],
            'episodes':episodes,'labeled_pair_claims':pairs,'distinct_input_grids':len(unique),'policies':sorted(policies),
            'sizes':sorted(sizes),'global_largest_buckets':sorted(buckets),'failures':failures,'passed':not failures,
            'racket':identity,'racket_evaluations':len(executions)+2*len(regression),'executions':executions,
            'minimum_lesson_regression':regression,
            'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'adapter.py',HERE/'prototype.py',HERE/'promotion.json']},
            'limits':'Finite policies and sampled seeds only. Native API 4–6 demos; legacy API retained separately. No owner acceptance or training admission.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists(): raise FileExistsError(a.out)
    report=run(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('passed','episodes','labeled_pair_claims','distinct_input_grids','policies','racket_evaluations','failures')}))
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
