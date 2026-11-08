"""Bounded, reproducible teaching/label/projection audit; not owner acceptance."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;HOME=HERE.parents[1];ROOT=HOME.parents[1]
_spec=importlib.util.spec_from_file_location('_a25697e4_audit_adapter',HERE/'adapter.py')
adapter=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=adapter;_spec.loader.exec_module(adapter)
RIVALS=('alternate_setting','always_exchange','opposite_handedness','rotation_only','plug_only','first_lock_only','identity')

def prediction(g,mode,name):
    if name=='alternate_setting':
        return adapter.model.solve(g,'preserve' if mode=='exchange' else 'exchange')
    return adapter.model.solve(g,mode,name)

def rival_program(mode,name):
    if name=='alternate_setting':
        return adapter.program({'reflection_colors':'preserve' if mode=='exchange' else 'exchange'})
    if name=='identity':return '(rule! (lambda (g) g))'
    p=adapter.program({'reflection_colors':mode})
    old,new={
        'always_exchange':('(and exchange-on-reflection (= flip 1))','#t'),
        'opposite_handedness':('(and exchange-on-reflection (= flip 1))','(= flip 0)'),
        'rotation_only':('(if (not item) out','(if (or (not item) (= (first item) 1)) out'),
        'plug_only':('(list flip (colors key) placed)','(list flip (colors key) (filter (lambda (p) (= (third p) plug)) placed))'),
        'first_lock_only':('((item placements))','((item (take placements 1)))'),
    }[name]
    if p.count(old)!=1:raise ValueError('rival source anchor drift')
    return p.replace(old,new)

def teaching_check(episode,mode):
    return [name for name in RIVALS if all(prediction(p['input'],mode,name)==p['output'] for p in episode['train'])]

def run(seeds=32):
    if type(seeds) is not int or not 1<=seeds<=256:raise ValueError('seeds must be 1..256')
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    findings=[];episodes=prefix_checks=views=evaluations=0;shapes=set();orders=set();rival_checks=0
    try:
        for seed in range(seeds):
            source=None
            for mode in adapter.model.MODES:
                e=adapter.generate(seed,{'reflection_colors':mode},6,4); episodes+=1
                current=[p['input'] for p in e['train']+e['test']]
                if source is not None and source!=current:findings.append({'seed':seed,'issue':'unmatched_input_stream'})
                source=current
                lesson={**e,'train':e['train'][:2]}
                survivors=teaching_check(lesson,mode);rival_checks+=len(RIVALS)
                if survivors:findings.append({'seed':seed,'setting':mode,'issue':'demo_survivors','rivals':survivors})
                for d in range(2,7):
                    for q in range(1,5):
                        short=adapter.generate(seed,{'reflection_colors':mode},d,q);prefix_checks+=1
                        if short['train']!=e['train'][:d] or short['test']!=e['test'][:q]:
                            findings.append({'seed':seed,'issue':'prefix_drift','demos':d,'queries':q})
                for qi in range(4):
                    public=adapter.public_view(lesson,qi);raw=public_challenge_bytes(public); views+=1
                    altered=deepcopy(lesson);altered['settings']={'not_public':seed};altered['program_solution']='not public';altered['seed']=seed+100
                    for j,p in enumerate(altered['test']):
                        p['output']=[[9]]
                        if j!=qi:p['input']=[[8]]
                    if raw!=public_challenge_bytes(adapter.public_view(altered,qi)):
                        findings.append({'seed':seed,'issue':'private_leak'})
                orders.add(tuple(adapter.model.query_order(seed)))
                for p in e['test']:
                    st=adapter.model.infer(p['input'])
                    shapes.add((len(p['input']),len(p['input'][0]),len(st['keys']),tuple(sorted(len(d['placed']) for d in st['docks']))))
                if seed in (0,17):
                    for p in lesson['train']+lesson['test']:
                        actual=apply(e['program_solution'],p['input']);evaluations+=1
                        if actual!=p['output']:findings.append({'seed':seed,'issue':'racket_label_mismatch'})
                    for name in RIVALS:
                        rp=rival_program(mode,name)
                        for p in lesson['train']+lesson['test']:
                            actual=apply(rp,p['input']);evaluations+=1
                            if actual!=prediction(p['input'],mode,name):findings.append({'seed':seed,'issue':'rival_racket_mismatch','rival':name})
    finally:
        bridge.close()
    return {'schema':'arcpuzzles-task-bounded-audit-v1','task_id':HOME.name,'status':'passed' if not findings else 'failed',
        'seeds':list(range(seeds)),'episodes':episodes,'prefix_checks':prefix_checks,'public_views':views,
        'rivals':list(RIVALS),'rival_lesson_checks':rival_checks,'racket_evaluations':evaluations,'racket':identity,
        'distinct_query_profiles':len(shapes),'distinct_query_orders':len(orders),'findings':findings,
        'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HOME.rglob('*')) if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts},
        'limits':'Finite named rivals and sampled seeds only; no universal uniqueness, owner acceptance or training admission.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError('choose a fresh audit output')
    report=run(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','racket','seeds')},sort_keys=True))
    return int(bool(report['findings']))
if __name__=='__main__':raise SystemExit(main())
