"""Finite region-composition lesson audit; no acceptance or uniqueness claim."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_region_audit_'+str(HERE),HERE/'adapter.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a);e=a.engine
RIVALS=('swap_roles','ink_only','omit_boundary','opaque_boundary','reverse_boundary_priority',
        'chosen_source_everywhere','other_source_everywhere','union_everywhere','intersection_everywhere',
        'first_region','last_region','smaller_region','larger_region','region_bbox',
        'eight_neighbor_flood','left_half','upper_half','identity')


def rival(g,mode,name):
    info=e.analyze(g);ph,pw=info['height'],info['width'];boundary=info['boundary'];bg=info['background']
    all_cells={(r,c) for r in range(ph) for c in range(pw)}
    chosen,other=info['panels'][1:3]
    if mode=='marked_third':chosen,other=other,chosen
    def paint(fn):
        out=[row[:] for row in g]
        for r in range(ph):
            for c in range(pw):out[info['top']+r][info['starts'][3]+c]=fn(r,c)
        return out
    if name=='identity':return [row[:] for row in g]
    if name=='swap_roles':return e.solve(g,e.SETTINGS[1-e.SETTINGS.index(mode)])
    if name=='ink_only':return e.render(g,info,mode,selected={info['marker']})
    if name=='omit_boundary':return e.render(g,info,mode,include_boundary=False)
    if name in ('opaque_boundary','reverse_boundary_priority'):
        out=e.render(g,info,mode)
        for r,c in boundary:
            value=chosen[r][c] if name=='opaque_boundary' else (other[r][c] if other[r][c]!=bg else chosen[r][c])
            out[info['top']+r][info['starts'][3]+c]=value
        return out
    if name=='chosen_source_everywhere':return paint(lambda r,c:chosen[r][c])
    if name=='other_source_everywhere':return paint(lambda r,c:other[r][c])
    if name=='union_everywhere':return paint(lambda r,c:chosen[r][c] if chosen[r][c]!=bg else other[r][c])
    if name=='intersection_everywhere':return paint(lambda r,c:chosen[r][c] if chosen[r][c]!=bg and other[r][c]!=bg else bg)
    if name=='first_region':selected=info['regions'][0]
    elif name=='last_region':selected=info['regions'][-1]
    elif name=='smaller_region':selected=min(info['regions'],key=len)
    elif name=='larger_region':selected=max(info['regions'],key=len)
    elif name=='region_bbox':
        rows=[r for r,c in info['selected']];cols=[c for r,c in info['selected']]
        selected={(r,c) for r in range(min(rows),max(rows)+1) for c in range(min(cols),max(cols)+1)}
    elif name=='eight_neighbor_flood':selected=next(reg for reg in e.groups(all_cells-boundary,8) if info['marker'] in reg)
    elif name=='left_half':selected={(r,c) for r,c in all_cells if c<pw//2}
    elif name=='upper_half':selected={(r,c) for r,c in all_cells if r<ph//2}
    else:raise ValueError(name)
    return e.render(g,info,mode,selected=selected)


def audit(seeds=32):
    e.integer(seeds,1,4096,'seeds');failures=[];episodes=stress=differences=harmful=0
    counterexamples={};surviving={n:0 for n in RIVALS}
    for seed in range(seeds):
        for mode in e.SETTINGS:
            bank=a.generate(seed,{'source':mode},6,4)
            other=a.generate(seed,{'source':e.SETTINGS[1-e.SETTINGS.index(mode)]},6,4)
            if [p['input'] for sp in ('train','test') for p in bank[sp]] != [p['input'] for sp in ('train','test') for p in other[sp]]:
                failures.append({'seed':seed,'problem':'setting-dependent input'})
            differences+=sum(x['output']!=y['output'] for sp in ('train','test') for x,y in zip(bank[sp],other[sp]))
            all_pairs=bank['train']+bank['test']
            if len({json.dumps(p['input']) for p in all_pairs})!=10:failures.append({'seed':seed,'problem':'duplicate inputs'})
            labels={n:[rival(p['input'],mode,n) for p in all_pairs] for n in RIVALS}
            for count in range(2,7):
                ep=a.generate(seed,{'source':mode},count,4);episodes+=1
                if ep['train']!=bank['train'][:count] or ep['test']!=bank['test']:failures.append({'seed':seed,'problem':'prefix drift'})
                for q in (1,2,3):
                    if a.generate(seed,{'source':mode},count,q)['test']!=bank['test'][:q]:failures.append({'seed':seed,'problem':'query count leak'})
                g=ep['test'][3]['input'];info=e.analyze(g)
                if len(g)==len(g[0])==30 and sum(v!=info['background'] for row in g for v in row)>250:stress+=1
                else:failures.append({'seed':seed,'problem':'30x30 stress missing'})
                for name,values in labels.items():
                    fits=all(values[i]==p['output'] for i,p in enumerate(ep['train']))
                    if fits:
                        surviving[name]+=1
                        if any(values[6+i]!=p['output'] for i,p in enumerate(ep['test'])):
                            harmful+=1;failures.append({'seed':seed,'mode':mode,'demos':count,'rival':name,'problem':'harmful survivor'})
                    elif name not in counterexamples:
                        i=next(i for i,p in enumerate(ep['train']) if values[i]!=p['output'])
                        counterexamples[name]={'seed':seed,'settings':{'source':mode},'demo_index':i,**ep['train'][i],'rival_output':values[i]}
    sources=[p for p in HERE.parents[1].rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.rkt') or p.name=='promotion.json')]
    return {'schema':'public-family-lesson-audit-v1','task_id':e.TASK_ID,'status':'passed' if not failures else 'failed','seeds':seeds,
            'demonstration_counts':[2,3,4,5,6],'episodes':episodes,'exact_30x30_pairs':stress,'setting_answer_differences':differences,
            'rival_count':len(RIVALS),'rivals':list(RIVALS),'harmful_survivors':harmful,'surviving_lesson_counts':surviving,
            'counterexamples':counterexamples,'failures':failures[:32],
            'source_files':{p.relative_to(HERE.parents[1]).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},
            'limits':'Finite Python rival audit only; independent protected-Racket receipts separate. No universal uniqueness or training claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();r=audit(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:r[k] for k in ('status','episodes','rival_count','harmful_survivors','exact_30x30_pairs')}))
    raise SystemExit(0 if r['status']=='passed' else 1)
