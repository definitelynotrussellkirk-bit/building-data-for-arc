"""Bounded lesson audit, including whole-color and eight-connected shortcuts.

Python labels are claim/rival computations, not acceptance. Independent Racket
original/preflight/causal evidence is required separately. Source-bound JSON
retains one concrete teaching counterexample per declared rival.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_settle_audit_'+str(HERE),HERE/'adapter.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a);e=a.engine
RIVALS=('opposite_gravity','keep_original_color','last_band_only','reverse_band_lookup',
        'whole_color_group','eight_connected','flatten_shape','bounding_box_fill',
        'keep_staging_objects','cascade_recolor','band_midpoint','identity')


def rival(g,mode,name):
    info=e.analyze(g);lookup={b['color']:dict(b) for b in info['bands']}
    if name=='opposite_gravity':return e.solve(g,e.SETTINGS[1-e.SETTINGS.index(mode)])
    if name=='identity':return [row[:] for row in g]
    if name=='keep_original_color':return e.render(g,info,mode,recolor=False)
    if name=='last_band_only':
        lookup={b['color']:info['bands'][-1] for b in info['bands']}
    elif name=='reverse_band_lookup':
        lookup={b['color']:t for b,t in zip(info['bands'],reversed(info['bands']))}
    elif name=='whole_color_group':
        objs=[]
        for color in lookup:
            cells=[p for obj in info['components'] if obj['color']==color for p in obj['cells']]
            if cells:objs.append({'color':color,'cells':cells})
        return e.render(g,info,mode,objects=objs)
    elif name=='eight_connected':
        return e.render(g,info,mode,objects=e.components(g[:info['stage_end']],info['background'],8))
    elif name=='flatten_shape':return e.render(g,info,mode,flatten=True)
    elif name=='bounding_box_fill':return e.render(g,info,mode,box=True)
    elif name=='keep_staging_objects':return e.render(g,info,mode,erase=False)
    elif name=='cascade_recolor':
        for band in lookup.values():
            if band['marker'] in lookup:band['marker']=next(b['marker'] for b in info['bands'] if b['color']==band['marker'])
    elif name=='band_midpoint':return e.render(g,info,mode,center=True)
    return e.render(g,info,mode,targets=lookup)


def audit(seeds=32):
    e.integer(seeds,1,4096,'seeds');failures=[];episodes=stress=differences=harmful=0
    counterexamples={};surviving={n:0 for n in RIVALS}
    for seed in range(seeds):
        for mode in e.SETTINGS:
            bank=a.generate(seed,{'settle':mode},6,4)
            other=a.generate(seed,{'settle':e.SETTINGS[1-e.SETTINGS.index(mode)]},6,4)
            if [p['input'] for sp in ('train','test') for p in bank[sp]] != [p['input'] for sp in ('train','test') for p in other[sp]]:
                failures.append({'seed':seed,'problem':'setting-dependent input'})
            differences+=sum(x['output']!=y['output'] for sp in ('train','test') for x,y in zip(bank[sp],other[sp]))
            all_pairs=bank['train']+bank['test']
            if len({json.dumps(p['input']) for p in all_pairs})!=10:failures.append({'seed':seed,'problem':'duplicate inputs'})
            labels={n:[rival(p['input'],mode,n) for p in all_pairs] for n in RIVALS}
            for count in range(2,7):
                ep=a.generate(seed,{'settle':mode},count,4);episodes+=1
                if ep['train']!=bank['train'][:count] or ep['test']!=bank['test']:failures.append({'seed':seed,'problem':'prefix drift'})
                for q in (1,2,3):
                    if a.generate(seed,{'settle':mode},count,q)['test']!=bank['test'][:q]:failures.append({'seed':seed,'problem':'query count leak'})
                g=ep['test'][3]['input'];info=e.analyze(g)
                if len(g)==len(g[0])==30 and sum(v!=info['background'] for row in g for v in row)>200:stress+=1
                else:failures.append({'seed':seed,'problem':'30x30 stress missing'})
                for name,values in labels.items():
                    fits=all(values[i]==p['output'] for i,p in enumerate(ep['train']))
                    if fits:
                        surviving[name]+=1
                        if any(values[6+i]!=p['output'] for i,p in enumerate(ep['test'])):
                            harmful+=1;failures.append({'seed':seed,'mode':mode,'demos':count,'rival':name,'problem':'harmful survivor'})
                    elif name not in counterexamples:
                        i=next(i for i,p in enumerate(ep['train']) if values[i]!=p['output'])
                        counterexamples[name]={'seed':seed,'settings':{'settle':mode},'demo_index':i,**ep['train'][i],'rival_output':values[i]}
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
