"""Bounded executable-rival, label, count-prefix and projection audit."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;HOME=HERE.parents[1];ROOT=HOME.parents[1]
_spec=importlib.util.spec_from_file_location('_2ba387bc_audit_adapter',HERE/'adapter.py')
adapter=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=adapter;_spec.loader.exec_module(adapter)
RIVALS=adapter.model.RIVALS

def prediction(g,mode,name):return adapter.model.solve(g,mode,name)

def teaching_check(episode,mode):
    return [name for name in RIVALS if all(prediction(p['input'],mode,name)==p['output'] for p in episode['train'])]

def rival_program(mode,name):
    if name=='alternate_axis':return adapter.program({'order_axis':'column' if mode=='row' else 'row'})
    program=adapter.program({'order_axis':mode})
    replacements={
        'reverse_order':('(sort xs before?)','(reverse (sort xs before?))'),
        'color_ascending':('(sort xs before?)','(sort xs (lambda (a b) (< (obj-color a) (obj-color b))))'),
        'color_descending':('(sort xs before?)','(sort xs (lambda (a b) (> (obj-color a) (obj-color b))))'),
        'swap_classes':('(list frames solids)','(list solids frames)'),
        'truncate_shorter':('(max (length (first buckets)) (length (second buckets)))','(min (length (first buckets)) (length (second buckets)))'),
        'solidify':('(subgrid g (obj-r1 block) (obj-c1 block) (obj-r2 block) (obj-c2 block))','(empty-grid size size (obj-color block))'),
        'serial_packing':('(list frames solids)',
            '(list (for/list ((i (range 0 (length blocks))) #:when (= (modulo i 2) 0)) (nth (ordered blocks) i)) (for/list ((i (range 0 (length blocks))) #:when (= (modulo i 2) 1)) (nth (ordered blocks) i)))'),
        'six_block_budget':('(define blocks (objects g bg))','(define blocks (take (objects g bg) (min 6 (length (objects g bg)))))')}
    old,new=replacements[name]
    if program.count(old)!=1:raise ValueError('rival anchor drift')
    return program.replace(old,new)

def run(seeds=32):
    if type(seeds) is not int or not 1<=seeds<=256:raise ValueError('seeds must be 1..256')
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    findings=[];episodes=prefix_checks=views=evaluations=rival_checks=0;profiles=set();orders=set()
    try:
        for seed in range(seeds):
            source=None
            for mode in adapter.model.MODES:
                e=adapter.generate(seed,{'order_axis':mode},6,4);episodes+=1
                current=[p['input'] for p in e['train']+e['test']]
                if source is not None and source!=current:findings.append({'seed':seed,'issue':'unmatched_input_stream'})
                source=current;lesson={**e,'train':e['train'][:2]}
                survivors=teaching_check(lesson,mode);rival_checks+=len(RIVALS)
                if survivors:findings.append({'seed':seed,'setting':mode,'issue':'demo_survivors','rivals':survivors})
                for d in range(2,7):
                    for q in range(1,5):
                        short=adapter.generate(seed,{'order_axis':mode},d,q);prefix_checks+=1
                        if short['train']!=e['train'][:d] or short['test']!=e['test'][:q]:findings.append({'seed':seed,'issue':'prefix_drift','demos':d,'queries':q})
                for qi in range(4):
                    raw=public_challenge_bytes(adapter.public_view(lesson,qi));views+=1
                    altered=deepcopy(lesson);altered['settings']={'secret':seed};altered['program_solution']='private';altered['seed']=seed+100
                    for j,p in enumerate(altered['test']):
                        p['output']=[[9]]
                        if j!=qi:p['input']=[[8]]
                    if raw!=public_challenge_bytes(adapter.public_view(altered,qi)):findings.append({'seed':seed,'issue':'private_leak'})
                orders.add(tuple(adapter.model.query_order(seed)))
                for p in e['test']:
                    st=adapter.model.infer(p['input']);b=adapter.model.ordered_buckets(st,mode)
                    profiles.add((len(p['input']),len(p['input'][0]),st['size'],len(b[0]),len(b[1])))
                if seed in (0,17):
                    for p in lesson['train']+lesson['test']:
                        actual=apply(e['program_solution'],p['input']);evaluations+=1
                        if actual!=p['output']:findings.append({'seed':seed,'issue':'racket_label_mismatch'})
                    for name in RIVALS:
                        rp=rival_program(mode,name)
                        for p in lesson['train']+lesson['test']:
                            actual=apply(rp,p['input']);evaluations+=1
                            if actual!=prediction(p['input'],mode,name):findings.append({'seed':seed,'issue':'rival_racket_mismatch','rival':name})
    finally:bridge.close()
    return {'schema':'arcpuzzles-task-bounded-audit-v1','task_id':HOME.name,'status':'passed' if not findings else 'failed',
        'seeds':list(range(seeds)),'episodes':episodes,'prefix_checks':prefix_checks,'public_views':views,
        'rivals':list(RIVALS),'rival_lesson_checks':rival_checks,'racket_evaluations':evaluations,'racket':identity,
        'distinct_query_profiles':len(profiles),'distinct_query_orders':len(orders),'findings':findings,
        'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HOME.rglob('*')) if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts},
        'limits':'Finite named rivals and seeds only, not universal uniqueness, owner acceptance or training admission.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError('choose fresh output')
    report=run(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','racket','seeds')},sort_keys=True))
    return int(bool(report['findings']))
if __name__=='__main__':raise SystemExit(main())
