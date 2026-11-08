"""Reusable owner-handoff smoke for the public-evaluation authority namespace.

This does not register or accept the family.  It verifies that the task's
literal ``ee_<parent>`` authority is accepted by the packet's frozen runner,
then replays one complete two-setting episode through protected Racket.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
TASK=HOME.name
PUBLIC_ID=TASK.removeprefix('public_eval_')


def _load(path: Path, stem: str):
    key=f'_runtime_smoke_{stem}_'+hashlib.sha256(str(path).encode()).hexdigest()[:12]
    spec=importlib.util.spec_from_file_location(key,path)
    module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return module


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def run_smoke(out, *, seed=17):
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    from arcpuzzles.review_public_creation import validate_reference_id

    if type(seed) is not int or seed < 0 or seed >= 2**63:
        raise ValueError('seed must be an exact nonnegative 63-bit integer')
    out=Path(out)
    if out.exists():raise FileExistsError('choose a fresh smoke output')
    root=find_root(__file__);runtime=root/'shared/runtime'
    generator=_load(HOME/'generator.py','generator')
    expected=validate_reference_id(HOME/'generator.py',PUBLIC_ID)
    with _local_imports(runtime,runtime):
        from puzzle_generators.runner import _resolve_rule_task_id
        resolved=_resolve_rule_task_id(TASK,generator,kind='per_puzzle')
    if resolved!=expected:raise ValueError('frozen runner resolved the wrong authority')

    adapter=_load(BASE/'adapter.py','adapter')
    canonical=(HOME/'reference.rkt').read_text()
    if adapter.program({'completion':'all'})!=canonical:
        raise ValueError('default program is not byte-identical to reference.rkt')
    apply,identity,bridge=_real_evaluator(runtime)
    evaluations=0;episodes=[]
    try:
        for completion in ('all','anchored_components'):
            settings={'completion':completion}
            episode=adapter.generate(seed,settings,2,4)
            pair_hashes=[]
            for pair in episode['train']+episode['test']:
                actual=apply(episode['program_solution'],pair['input']);evaluations+=1
                if actual!=pair['output']:
                    raise ValueError(f'protected Racket mismatch for {completion}')
                pair_hashes.append(_digest({'input':pair['input'],'output':actual}))
            episodes.append({'settings':settings,'pair_count':6,'pair_sha256':pair_hashes,
                             'program_sha256':hashlib.sha256(episode['program_solution'].encode()).hexdigest()})
    finally:
        bridge.close()
    report={'schema':'arcpuzzles-public-owner-handoff-smoke-v1','status':'passed',
            'generator_task_id':TASK,'rule_task_id':expected,
            'runner_resolved_rule_task_id':resolved,'seed':seed,
            'protected_racket_evaluations':evaluations,'racket':identity,
            'episodes':episodes,'owner_accepted':False,
            'limits':'Literal/runner compatibility and bounded protected execution only; no registration, qualification, acceptance, or training admission.'}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--seed',type=int,default=17)
    args=p.parse_args();r=run_smoke(args.out,seed=args.seed)
    print(json.dumps({k:v for k,v in r.items() if k not in ('episodes','racket')},sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
