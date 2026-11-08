"""Bounded self-audit for 0934a4d8 teaching, privacy and Racket parity."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;HOME=HERE.parents[1];ROOT=HOME.parents[1]
_spec=importlib.util.spec_from_file_location('_public_eval_0934a4d8_audit_adapter',HERE/'adapter.py')
adapter=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=adapter;_spec.loader.exec_module(adapter)


def teaching_check(episode,mode):
    findings=[]
    for rival in adapter.model.RIVALS:
        if all(adapter.model.solve(p['input'],mode,rival)==p['output'] for p in episode['train']):
            findings.append({'issue':'rival_fits_all_demonstrations','rival':rival})
    other='marker_bbox' if mode=='patch' else 'patch'
    if all(adapter.model.solve(p['input'],other)==p['output'] for p in episode['train']):
        findings.append({'issue':'other_setting_fits_all_demonstrations','other':other})
    return findings


def run(seeds=24):
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    findings=[];episodes=0;views=0;racket_evaluations=0;orders=set();sizes=set()
    try:
        for seed in range(seeds):
            orders.add(tuple(adapter.model.query_order(seed)))
            for mode in adapter.model.MODES:
                episode=adapter.generate(seed,{'output_mode':mode},2,4);episodes+=1
                findings.extend({'seed':seed,'mode':mode,**row} for row in teaching_check(episode,mode))
                public=[]
                for i in range(4):
                    view=adapter.public_view(episode,i);views+=1
                    if set(view)!={'train','test'} or len(view['test'])!=1 or set(view['test'][0])!={'input'}:
                        findings.append({'seed':seed,'mode':mode,'issue':'public_projection_leak'})
                    public.append(json.dumps(view,sort_keys=True))
                if len(set(public))!=4:findings.append({'seed':seed,'mode':mode,'issue':'duplicate_public_query_view'})
                for pair in episode['train']+episode['test']:
                    sizes.add((len(pair['input']),len(pair['input'][0]),len(pair['output']),len(pair['output'][0])))
                    state=adapter.model.analyze(pair['input'])
                    if state['visible_orbit_conflicts'] or state['unrecoverable_hidden_cells']:
                        findings.append({'seed':seed,'mode':mode,'issue':'invalid_recovery_state','state':state})
                    actual=apply(episode['program_solution'],pair['input']);racket_evaluations+=1
                    if actual!=pair['output']:findings.append({'seed':seed,'mode':mode,'issue':'racket_label_mismatch'})
    finally:
        bridge.close()
    if len(orders)<2 or not any(order[0]!=0 for order in orders):findings.append({'issue':'query_order_not_effectively_shuffled'})
    if not any(ih==iw==30 for ih,iw,_,_ in sizes):findings.append({'issue':'missing_30x30_input_stress'})
    hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(HOME.rglob('*')) if p.is_file() and p.suffix in ('.py','.rkt','.json') and '__pycache__' not in p.parts}
    return {'schema':'arcpuzzles-task-bounded-audit-v1','task_id':HOME.name,
            'status':'passed' if not findings else 'failed','seeds':list(range(seeds)),
            'episodes':episodes,'public_views':views,'rivals':list(adapter.model.RIVALS),
            'racket_evaluations':racket_evaluations,'racket':identity,
            'distinct_query_orders':len(orders),'distinct_shapes':len(sizes),
            'findings':findings,'source_sha256':hashes,
            'limits':'Finite seeds and named rivals only; not universal uniqueness, owner acceptance or training admission.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--seeds',type=int,default=24);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    if args.out.exists():raise FileExistsError('choose a fresh output path')
    report=run(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','racket','seeds')},sort_keys=True))
    return int(bool(report['findings']))

if __name__=='__main__':raise SystemExit(main())
