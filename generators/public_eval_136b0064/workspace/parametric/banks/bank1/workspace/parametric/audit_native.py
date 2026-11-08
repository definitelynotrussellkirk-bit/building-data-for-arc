"""Reusable bounded audit for this task's single-parameter native adapter.

Use the packet's review.py run wrapper to select its protected Racket runtime.
Outputs are author-private, include exact source hashes, and grant no acceptance.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
HOME=HERE.parents[1]
ROOT=HOME.parents[1]
for path in (ROOT/'src', ROOT/'shared/runtime'):
    if str(path) not in sys.path: sys.path.insert(0,str(path))


def source_binding():
    paths=sorted(p for p in HOME.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                 and (p.suffix in {'.py','.rkt'} or p.name in {'promotion.json','public-parent.json'}))
    return {'task_id':HOME.name,'files':[{'path':p.relative_to(ROOT).as_posix(),
           'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}


def load_adapter():
    path=HERE/'adapter.py'
    name='_audit_adapter_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module)
    return module


def audit(seeds, racket_seeds, public_dir=None):
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    from reviewer_support import public_challenge_bytes
    adapter=load_adapter(); family=adapter.family
    contract=json.loads((HERE/'promotion.json').read_text())
    key, options=next(iter(contract['parameters'].items()))
    before=source_binding()
    failures=[]; episodes=prefixes=views=evaluations=0
    different_first=set(); stress_sizes=set(); named_checks=0
    saved={}; representative=[]
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    def execute(program, grid):
        nonlocal evaluations
        evaluations+=1
        return _grid(apply(program,grid))
    try:
        for seed in range(seeds):
            matched=None
            for option in options:
                settings={key:option}
                lesson=adapter.generate(seed,settings,6,4)
                episodes+=1
                inputs=[p['input'] for split in ('train','test') for p in lesson[split]]
                if len({json.dumps(g) for g in inputs})!=10: failures.append(['duplicate',seed,settings])
                if matched is not None and matched!=inputs: failures.append(['unmatched',seed,settings])
                matched=inputs
                for d in range(2,7):
                    for q in range(1,5):
                        prefix=adapter.generate(seed,settings,d,q); prefixes+=1
                        if prefix['train']!=lesson['train'][:d] or prefix['test']!=lesson['test'][:q]:
                            failures.append(['prefix',seed,settings,d,q])
                teaching=lesson['train'][:2]
                for name in family.rival_names(option):
                    demo_fit=all(family.rival_solve(p['input'],option,name)==p['output'] for p in teaching)
                    named_checks+=1
                    if demo_fit and any(family.rival_solve(p['input'],option,name)!=p['output'] for p in lesson['test']):
                        failures.append(['dangerous_rival',seed,settings,name])
                    if seed<racket_seeds:
                        program=family.racket_program(option,name)
                        for p in teaching+lesson['test']:
                            if execute(program,p['input'])!=family.rival_solve(p['input'],option,name):
                                failures.append(['rival_parity',seed,settings,name])
                if seed<racket_seeds:
                    for p in lesson['train']+lesson['test']:
                        if execute(adapter.program(settings),p['input'])!=p['output']:
                            failures.append(['label',seed,settings])
                for index,p in enumerate(lesson['test']):
                    view=adapter.public_view(lesson,index); raw=public_challenge_bytes(view); views+=1
                    polluted=copy.deepcopy(lesson)
                    polluted.update(settings={'hidden':'different'},seed=2**62,program_solution='secret',source_indices=[99]*4)
                    for j,pair in enumerate(polluted['test']):
                        pair['output']=[[9]]
                        if j!=index: pair['input']=[[8]]
                    if raw!=public_challenge_bytes(adapter.public_view(polluted,index)):
                        failures.append(['private_leak',seed,settings,index])
                    if len(view['test'])!=1: failures.append(['multi_query',seed,settings,index])
                    if len(p['input'])==len(p['input'][0])==30:
                        stress_sizes.add(sum(v!=0 for row in p['input'] for v in row))
                        different_first.add(index)
                    if seed<2:
                        public_id=hashlib.sha256(raw).hexdigest()
                        saved[public_id]=raw
                        representative.append({'seed':seed,'settings':settings,'presentation_index':index,'public_id':public_id})
        if source_binding()!=before: failures.append(['source_drift'])
    finally:
        bridge.close()
    if public_dir is not None:
        public_dir.mkdir(parents=True,exist_ok=False)
        # Sort ONLY by public bytes' identity, not seed/settings/private order.
        for public_id in sorted(saved):
            (public_dir/(public_id+'.json')).write_bytes(saved[public_id])
    return {'schema':'arcpuzzles-bounded-native-audit-v1','task_id':HOME.name,
            'status':'failed' if failures else 'passed','source_binding':before,
            'seeds':list(range(seeds)),'episodes_checked':episodes,'prefix_requests_checked':prefixes,
            'public_views_checked':views,'named_rival_checks':named_checks,
            'racket_seed_count':racket_seeds,'racket_evaluations':evaluations,'racket':identity,
            'stress_foreground_counts':sorted(stress_sizes),'stress_presentation_positions':sorted(different_first),
            'public_files_written':len(saved) if public_dir else 0,'public_file_mapping':representative if public_dir else [],
            'failures':failures,'owner_accepted':False,'training_admitted':False,
            'limits':'Finite named rivals and seeds only; Python claims checked through protected Racket on the stated seed subset. No universal rule uniqueness, owner qualification, or admission.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=64); p.add_argument('--racket-seeds',type=int,default=2)
    p.add_argument('--out',type=Path,required=True); p.add_argument('--public-dir',type=Path)
    args=p.parse_args()
    if not 1<=args.seeds<=1024 or not 1<=args.racket_seeds<=min(args.seeds,16):
        p.error('require 1..1024 seeds and 1..min(seeds,16) Racket seeds')
    if args.out.exists() or (args.public_dir and args.public_dir.exists()): p.error('use fresh output paths')
    report=audit(args.seeds,args.racket_seeds,args.public_dir)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes_checked','racket_evaluations','failures')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__': raise SystemExit(main())
