"""Finite demonstration-only rival audit. No crash is a refutation.

Python competitors are explicit hypotheses, not Racket execution claims. The
separate authoring preflight, boundary and causal receipts run protected Racket.
"""
from pathlib import Path
import importlib.util
import hashlib
import sys
import json
from copy import deepcopy
import argparse

BASE=Path(__file__).resolve().parent
p=BASE/'adapter.py';s=importlib.util.spec_from_file_location('_selective_audit_'+hashlib.sha256(str(p).encode()).hexdigest(),p)
A=importlib.util.module_from_spec(s);sys.modules[s.name]=A;s.loader.exec_module(A)
R=A.R

SELECTORS=('most_cells','fewest_cells','largest_bbox','damage_fraction','least_damage',
           'first_color','last_color','first_maximum_only','nonminimum_damage')

def rival_names(mode):
    return ['rule_'+m for m in A.MODES if m!=mode]+[
        'identity','bbox_axis','canvas_axis','rightmost_axis','horizontal_axis',
        'fill_repaired_boxes','largest_color_only']+(list(SELECTORS) if mode=='complete_most_damaged' else [])

def predict(grid,mode,name):
    if name.startswith('rule_'):return R.solve(grid,name[5:])
    if name=='identity':return deepcopy(grid)
    if name=='horizontal_axis':return list(map(list,zip(*R.solve(list(map(list,zip(*grid))),mode))))
    bg,records=R.analyze(grid);out=deepcopy(grid)
    if name=='fill_repaired_boxes':
        answer=R.solve(grid,mode)
        for color in sorted({v for row in answer for v in row}-{bg}):
            pts=[(r,c) for r,row in enumerate(answer) for c,v in enumerate(row) if v==color]
            for r in range(min(p[0] for p in pts),max(p[0] for p in pts)+1):
                for c in range(min(p[1] for p in pts),max(p[1] for p in pts)+1):answer[r][c]=color
        return answer
    if name in ('bbox_axis','canvas_axis','rightmost_axis'):
        for rec in records:
            pts=rec['cells']
            rec['axis2']=(min(c for r,c in pts)+max(c for r,c in pts) if name=='bbox_axis'
                          else len(grid[0])-1 if name=='canvas_axis' else max(rec['maximizers']))
            rec['damage']=sum((r,rec['axis2']-c)not in pts for r,c in pts)
    maxdamage=max((r['damage'] for r in records),default=0)
    selected={r['color'] for r in records if r['damage']==maxdamage and maxdamage>0}
    if name in SELECTORS and records:
        def area(r):
            return (max(x for x,y in r['cells'])-min(x for x,y in r['cells'])+1)*(max(y for x,y in r['cells'])-min(y for x,y in r['cells'])+1)
        fn={'most_cells':lambda r:len(r['cells']),'fewest_cells':lambda r:-len(r['cells']),
            'largest_bbox':area,'damage_fraction':lambda r:r['damage']/len(r['cells']),
            'least_damage':lambda r:-r['damage'],'first_color':lambda r:-r['color'],
            'last_color':lambda r:r['color']}.get(name)
        if fn:
            best=max(fn(r) for r in records);selected={r['color'] for r in records if fn(r)==best}
        elif name=='first_maximum_only':selected=set(sorted(selected)[:1])
        else:selected={r['color'] for r in records if r['damage']>min(x['damage'] for x in records)}
    if name=='largest_color_only' and records:records=[max(records,key=lambda r:len(r['cells']))]
    for rec in records:
        cells,axis,color=rec['cells'],rec['axis2'],rec['color']
        complete=mode=='complete' or (mode=='complete_most_damaged' and color in selected)
        for r,c in sorted(cells):
            cc=axis-c
            if complete:
                if 0<=cc<len(grid[0]) and grid[r][cc]==bg:out[r][cc]=color
            elif (r,cc)not in cells:out[r][c]=bg
    return out

def audit(seeds=tuple(range(24)),demo_counts=(2,3,6)):
    seeds=list(seeds);demo_counts=list(demo_counts)
    failures=[];lessons=[];pairs=0;maxima=0
    for seed in seeds:
        for mode in A.MODES:
            ep=A.generate(seed,{'rule':mode},6,4)
            allpairs=ep['train']+ep['test']
            candidates={n:[predict(p['input'],mode,n) for p in allpairs] for n in rival_names(mode)}
            for demos in demo_counts:
                if type(demos)is not int or not 2<=demos<=6:raise ValueError('invalid demo count')
                refuted=[];equivalent=[]
                for name,ys in candidates.items():
                    if any(ys[i]!=ep['train'][i]['output'] for i in range(demos)):
                        refuted.append(name);continue
                    disagreements=[i for i in range(4) if ys[6+i]!=ep['test'][i]['output']]
                    if disagreements:
                        failures.append({'seed':seed,'mode':mode,'demos':demos,'rival':name,
                            'query_indices':disagreements,'episode':{'train':ep['train'][:demos],'test':ep['test'],'program_solution':ep['program_solution']}})
                    else:equivalent.append(name)
                lessons.append({'seed':seed,'mode':mode,'demos':demos,'refuted':refuted,'query_equivalent_survivors':equivalent})
                pairs+=demos+4
                maxima+=sum(len(p['input'])==len(p['input'][0])==30 for p in ep['test'])
    return {'status':'failed' if failures else 'passed','seeds':seeds,'demo_counts':demo_counts,
            'episodes':len(lessons),'labeled_pairs':pairs,'maximum_query_cases':maxima,
            'rivals':{m:rival_names(m) for m in A.MODES},'lessons':lessons,'harmful_survivors':failures,
            'scope':'Finite Python candidate rules and listed seeds only. No failed execution counts as a refutation. Not universal uniqueness.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seeds',type=int,default=24)
    args=parser.parse_args();report=audit(range(args.seeds))
    if args.out.exists():raise FileExistsError(args.out)
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pairs','maximum_query_cases')}))
    if report['harmful_survivors']:raise SystemExit(1)
