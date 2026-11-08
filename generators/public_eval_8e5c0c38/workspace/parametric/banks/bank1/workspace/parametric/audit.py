"""Finite lesson audit. Python rivals are hypotheses, not reference labels."""
from pathlib import Path
import importlib.util
import hashlib
import json
import sys

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_sym_audit_adapter_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:12],BASE/'adapter.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
RIVALS=('other_setting','identity','bbox_axis','rightmost_tie','horizontal_axis','canvas_axis','filled_bbox','largest_color_only','rowwise_axis','left_completion','right_completion')

def rival(grid,mode,name):
    if name=='other_setting':return a.sampler.predict(grid,'complete' if mode=='trim' else 'trim')
    if name=='identity':return [row[:] for row in grid]
    if name in ('bbox_axis','rightmost_tie','horizontal_axis','canvas_axis'):
        return a.sampler.predict(grid,mode,dict(bbox_axis='bbox',rightmost_tie='rightmost',horizontal_axis='horizontal',canvas_axis='canvas')[name])
    bg,parts=a.sampler.records(grid)
    out=[[bg]*len(grid[0]) for _ in grid]
    largest=max(parts,key=lambda p:len(p['cells']))['color']
    for part in parts:
        pts=set(map(tuple,part['cells']));k=part['axis_twice']
        if name=='largest_color_only':
            if part['color']==largest:
                mirrors={(r,k-c) for r,c in pts};chosen=pts&mirrors if mode=='trim' else pts|mirrors
            else:chosen=pts
        elif name=='filled_bbox':
            chosen={(r,c) for r in range(min(p[0] for p in pts),max(p[0] for p in pts)+1) for c in range(min(p[1] for p in pts),max(p[1] for p in pts)+1)}
        elif name=='rowwise_axis':
            chosen=set()
            for r in sorted({r for r,c in pts}):
                cols={c for rr,c in pts if rr==r}
                kk=max(range(2*len(grid[0])-1),key=lambda x:(sum(x-c in cols for c in cols),-x))
                mirrors={kk-c for c in cols};keep=cols&mirrors if mode=='trim' else cols|mirrors
                chosen.update((r,c) for c in keep)
        else:
            half={p for p in pts if (2*p[1]<=k if name=='left_completion' else 2*p[1]>=k)}
            chosen=half|{(r,k-c) for r,c in half}
        for r,c in chosen:
            if 0<=r<len(grid) and 0<=c<len(grid[0]):out[r][c]=part['color']
    return out

def audit(seeds=range(16),demo_counts=(2,3,6)):
    counts=dict(episodes=0,labeled_pairs=0,maximum_size_episodes=0)
    failures=[];equivalent={name:0 for name in RIVALS};rejected={name:0 for name in RIVALS}
    for seed in seeds:
        for demos in demo_counts:
            previous=None
            for mode in ('trim','complete'):
                e=a.generate(seed,{'repair_mode':mode},demos,4)
                inputs=[p['input'] for sp in ('train','test') for p in e[sp]]
                if previous is not None and inputs!=previous:failures.append(dict(seed=seed,error='input drift'))
                previous=inputs
                counts['episodes']+=1;counts['labeled_pairs']+=demos+4
                if len(e['test'][3]['input'])==30:counts['maximum_size_episodes']+=1
                for name in RIVALS:
                    survives=all(rival(p['input'],mode,name)==p['output'] for p in e['train'])
                    if survives:
                        bad=[i for i,p in enumerate(e['test']) if rival(p['input'],mode,name)!=p['output']]
                        if bad:failures.append(dict(seed=seed,demos=demos,mode=mode,rival=name,queries=bad))
                        else:equivalent[name]+=1
                    else:rejected[name]+=1
    return dict(schema='task-finite-rival-audit-v1',**counts,rivals=list(RIVALS),failures=failures,
                rejected_by_demos=rejected,query_equivalent_survivals=equivalent,
                limits='Finite Python hypotheses only; protected parity evidence is recorded separately. No universal uniqueness claim.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();result=audit(range(args.seeds));args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    raise SystemExit(bool(result['failures']))
