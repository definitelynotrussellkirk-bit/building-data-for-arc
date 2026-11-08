"""Bounded learnability audit for edge-seeded periodic rays.

This checks all supported short demonstration counts against explicit total
rivals. It uses Python claims; protected-Racket execution remains separate.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_periodic_audit_'+str(HERE),HERE/'adapter.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a);e=a.engine
RIVALS=('opposite_extent','ignore_markers','any_marker','keep_seed_color',
        'unit_spacing','fixed_spacing_two','fixed_spacing_three','gap_as_period',
        'erase_off_lattice','solid_interval','preserve_seed_color','horizontal_only',
        'vertical_only','phase_shift_one','identity')


def rival(grid,mode,name):
    plan=e.analyze(grid);g=[row[:] for row in grid];h,w=len(g),len(g[0])
    if name=='opposite_extent':return e.solve(g,e.SETTINGS[1-e.SETTINGS.index(mode)])
    if name=='identity' or name=='horizontal_only' and plan['side']>=2 or name=='vertical_only' and plan['side']<2:return g
    original=copy.deepcopy(plan)
    for ray in plan['rays']:
        marker=ray['marker']
        if name=='ignore_markers':ray['hit']=None
        elif name=='any_marker':ray['hit']=marker
        elif name=='keep_seed_color' and ray['hit'] is not None:ray['hit']=[ray['hit'][0],ray['color']]
        elif name in ('unit_spacing','fixed_spacing_two','fixed_spacing_three','gap_as_period'):
            ray['spacing']={'unit_spacing':1,'fixed_spacing_two':2,'fixed_spacing_three':3,'gap_as_period':max(1,ray['spacing']-1)}[name]
            ray['hit']=marker[:] if marker is not None and marker[0]%ray['spacing']==0 else None
        elif name=='erase_off_lattice' and marker is not None and ray['hit'] is None:
            r,c=e.coordinate(plan['side'],ray['line'],marker[0],h,w);g[r][c]=0
        elif name=='solid_interval':ray['spacing']=1
    if name=='phase_shift_one':
        out=[row[:] for row in g]
        for ray in plan['rays']:
            hit=ray['hit'];end=hit[0] if hit is not None and mode=='stop_at_hit' else plan['length']-1
            color=hit[1] if hit is not None else ray['color']
            for t in range(1,end+1,ray['spacing']):
                r,c=e.coordinate(plan['side'],ray['line'],t,h,w);out[r][c]=color
    else:out=e.render(g,plan,mode)
    if name=='preserve_seed_color':
        for ray in original['rays']:
            for t in (0,ray['spacing']):
                r,c=e.coordinate(plan['side'],ray['line'],t,h,w);out[r][c]=ray['color']
    return out


def audit(seeds=32):
    e.integer(seeds,1,4096,'seeds')
    failures=[];episodes=stress=differences=harmful=0;edges=set();counterexamples={};surviving={n:0 for n in RIVALS}
    for seed in range(seeds):
        for mode in e.SETTINGS:
            bank=a.generate(seed,{'extent':mode},6,4)
            other=a.generate(seed,{'extent':e.SETTINGS[1-e.SETTINGS.index(mode)]},6,4)
            pairs=bank['train']+bank['test']
            if [p['input'] for p in pairs]!=[p['input'] for sp in ('train','test') for p in other[sp]]:
                failures.append({'seed':seed,'problem':'setting-dependent input'})
            if len({json.dumps(p['input']) for p in pairs})!=10:failures.append({'seed':seed,'problem':'duplicate input'})
            differences+=sum(p['output']!=q['output'] for sp in ('train','test') for p,q in zip(bank[sp],other[sp]))
            for pair in pairs:edges.add(e.analyze(pair['input'])['side'])
            labels={n:[rival(p['input'],mode,n) for p in pairs] for n in RIVALS}
            for count in range(2,7):
                ep=a.generate(seed,{'extent':mode},count,4);episodes+=1
                if ep['train']!=bank['train'][:count] or ep['test']!=bank['test']:
                    failures.append({'seed':seed,'problem':'prefix drift'})
                for q in (1,2,3):
                    if a.generate(seed,{'extent':mode},count,q)['test']!=bank['test'][:q]:failures.append({'seed':seed,'problem':'query prefix drift'})
                last=ep['test'][3];g=last['input']
                if len(g)==len(g[0])==30 and sum(v!=0 for row in last['output'] for v in row)>=120:stress+=1
                else:failures.append({'seed':seed,'problem':'30x30 stress insufficient'})
                for name,outs in labels.items():
                    fits=all(outs[i]==pair['output'] for i,pair in enumerate(ep['train']))
                    if fits:
                        surviving[name]+=1
                        if any(outs[6+i]!=pair['output'] for i,pair in enumerate(ep['test'])):
                            harmful+=1;failures.append({'seed':seed,'mode':mode,'demos':count,'rival':name,'problem':'harmful survivor'})
                    elif name not in counterexamples:
                        i=next(i for i,pair in enumerate(ep['train']) if outs[i]!=pair['output'])
                        counterexamples[name]={'seed':seed,'settings':{'extent':mode},'demo_index':i,**ep['train'][i],'rival_output':outs[i]}
    source=[p for p in HERE.parents[1].rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.rkt') or p.name=='promotion.json')]
    return {'schema':'public-family-lesson-audit-v1','task_id':e.TASK_ID,'status':'passed' if not failures else 'failed',
            'seeds':seeds,'episodes':episodes,'exact_30x30_pairs':stress,'demonstration_counts':[2,3,4,5,6],
            'setting_answer_differences':differences,'observed_source_edges':sorted(edges),'rival_count':len(RIVALS),'rivals':list(RIVALS),
            'harmful_survivors':harmful,'surviving_lesson_counts':surviving,'counterexamples':counterexamples,'failures':failures[:32],
            'source_files':{p.relative_to(HERE.parents[1]).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source)},
            'limits':'Finite Python mirror/rival audit. Protected-Racket labels are separately replayed. No universal uniqueness or admission claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();r=audit(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:r[k] for k in ('status','episodes','rival_count','harmful_survivors','exact_30x30_pairs')}))
    raise SystemExit(0 if r['status']=='passed' else 1)
