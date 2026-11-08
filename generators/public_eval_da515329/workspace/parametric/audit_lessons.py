"""Finite teachability audit; Python claim checks, not acceptance or uniqueness.

Usage under review.py run: python generators/TASK/workspace/parametric/audit_lessons.py
--seeds 32 --out ../checks/TASK/audit.json. No source setting or future query is public.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_spiral_audit_adapter_'+str(HERE),HERE/'adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
e=a.engine
RIVALS=('opposite_turn','fixed_radius_2','fixed_radius_3','fixed_radius_4',
        'canvas_center','swapped_center','raw_radius_without_spacing_floor',
        'stop_on_first_exit','growth_two','all_ink_eight','fill_center','identity')


def alternate_trace(g,mode,*,raw=False,stop=False,growth=4):
    p=e.analyze(g);h,w=len(g),len(g[0]);k=p['arm_length'] if raw else max(2,p['arm_length'])
    out=[[0]*w for _ in range(h)];sign=1 if mode=='clockwise' else -1
    for arm in range(4):
        r,c=p['center'];alive=True
        d=arm
        steps=[(d,k)]
        d+=sign
        for n in range(h+w):
            steps.extend(((d,2+growth*n),(d+sign,max(0,k-2)),(d,k)))
            d+=sign
        for d,n in steps:
            dr,dc=e.DIRECTIONS[d%4]
            for _ in range(n):
                r+=dr;c+=dc
                if 0<=r<h and 0<=c<w:out[r][c]=p['color']
                elif stop:alive=False;break
            if not alive:break
    return out


def rival(g,mode,name):
    p=e.analyze(g);h,w=len(g),len(g[0]);center=p['center'];k=p['arm_length'];ink=p['color']
    if name=='opposite_turn':return e.solve(g,e.SETTINGS[1-e.SETTINGS.index(mode)])
    if name.startswith('fixed_radius_'):k=int(name[-1])
    elif name=='canvas_center':center=[(h-1)//2,(w-1)//2]
    elif name=='swapped_center':center=center[::-1]
    elif name=='raw_radius_without_spacing_floor':return alternate_trace(g,mode,raw=True)
    elif name=='stop_on_first_exit':return alternate_trace(g,mode,stop=True)
    elif name=='growth_two':return alternate_trace(g,mode,growth=2)
    elif name=='all_ink_eight':ink=8
    elif name=='identity':return [row[:] for row in g]
    out=e.render(h,w,center,k,ink,mode)
    if name=='fill_center':out[p['center'][0]][p['center'][1]]=ink
    return out


def audit(seeds=32):
    e.integer(seeds,1,4096,'seeds')
    failures=[];episodes=stress=differences=harmful=0;counterexamples={};surviving={n:0 for n in RIVALS}
    for seed in range(seeds):
        for mode in e.SETTINGS:
            bank=a.generate(seed,{'turn':mode},6,4)
            other=a.generate(seed,{'turn':e.SETTINGS[1-e.SETTINGS.index(mode)]},6,4)
            if [p['input'] for s in ('train','test') for p in bank[s]] != [p['input'] for s in ('train','test') for p in other[s]]:
                failures.append({'seed':seed,'problem':'setting-dependent inputs'})
            differences+=sum(x['output']!=y['output'] for s in ('train','test') for x,y in zip(bank[s],other[s]))
            all_pairs=bank['train']+bank['test']
            if len({json.dumps(p['input']) for p in all_pairs})!=10:failures.append({'seed':seed,'problem':'duplicate inputs'})
            # Cache rival labels per bank, not per overlapping lesson window.
            rival_labels={n:[rival(p['input'],mode,n) for p in all_pairs] for n in RIVALS}
            for count in range(2,7):
                ep=a.generate(seed,{'turn':mode},count,4);episodes+=1
                if ep['train']!=bank['train'][:count] or ep['test']!=bank['test']:
                    failures.append({'seed':seed,'count':count,'problem':'prefix drift'})
                for q in (1,2,3):
                    if a.generate(seed,{'turn':mode},count,q)['test']!=bank['test'][:q]:
                        failures.append({'seed':seed,'problem':'query count leak'})
                last=ep['test'][-1];g=last['input']
                if len(g)==len(g[0])==30 and sum(v!=0 for row in last['output'] for v in row)>300:stress+=1
                else:failures.append({'seed':seed,'problem':'30x30 stress absent'})
                for name,labels in rival_labels.items():
                    fits=all(labels[i]==p['output'] for i,p in enumerate(ep['train']))
                    if fits:
                        surviving[name]+=1
                        if any(labels[6+i]!=p['output'] for i,p in enumerate(ep['test'])):
                            harmful+=1;failures.append({'seed':seed,'mode':mode,'demos':count,'rival':name,'problem':'harmful survivor'})
                    elif name not in counterexamples:
                        i=next(i for i,p in enumerate(ep['train']) if labels[i]!=p['output'])
                        counterexamples[name]={'seed':seed,'settings':{'turn':mode},'demo_index':i,**ep['train'][i],'rival_output':labels[i]}
    sources=[p for p in HERE.parents[1].rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.rkt') or p.name=='promotion.json')]
    return {'schema':'public-family-lesson-audit-v1','task_id':e.TASK_ID,'status':'passed' if not failures else 'failed',
            'seeds':seeds,'demonstration_counts':[2,3,4,5,6],'episodes':episodes,'exact_30x30_pairs':stress,
            'setting_answer_differences':differences,'rival_count':len(RIVALS),'rivals':list(RIVALS),
            'harmful_survivors':harmful,'surviving_lesson_counts':surviving,'counterexamples':counterexamples,'failures':failures[:32],
            'source_files':{p.relative_to(HERE.parents[1]).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},
            'limits':'Finite Python mirror/rival audit only. Protected-Racket original/preflight/causal evidence is separate. No uniqueness or training claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();r=audit(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:r[k] for k in ('status','episodes','rival_count','harmful_survivors','exact_30x30_pairs')}))
    raise SystemExit(0 if r['status']=='passed' else 1)
