#!/usr/bin/env python3
"""Bounded, rerunnable teaching/source/export audit. No acceptance is granted.

Run from the packet root via review.py run python3 generators/TASK/.../audit.py.
Python sweep results are claims; only the listed protected evaluations bind
labels to Racket. The optional frozen-before evidence retains actual findings.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
from collections import Counter

HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_exact2_audit_adapter',HOME/'adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
TASK='2ab8c1aaa3e2'


def raw(value):
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


def run_sweep(seeds=32):
    if type(seeds) is not int or not 1 <= seeds <= 1024:
        raise ValueError('seeds must be 1..1024')
    failures=[];seen=set();survivors=Counter();episodes=0;pair_checks=0
    for seed in range(seeds):
        inputs={}
        for demos in range(2,7):
            for mode in a.MODES:
                e=a.generate(seed,{'composition':mode},demos,4)
                episodes+=1;pair_checks+=len(e['train'])+4
                audit=a.teaching_audit(e);survivors.update(audit['survivors'])
                grids=[raw(p['input']) for p in e['train']+e['test']]
                seen.update(grids)
                if audit['query_disagreeing_survivors']:
                    failures.append(dict(seed=seed,mode=mode,demos=demos,teaching=audit))
                if len(set(grids))!=len(grids): failures.append(dict(seed=seed,issue='duplicate_input'))
                if demos in inputs and grids!=inputs[demos]: failures.append(dict(seed=seed,issue='setting_leaks_into_inputs'))
                inputs[demos]=grids
                if a.generate(seed,{'composition':mode},demos,1)['test']!=e['test'][:1]: failures.append(dict(seed=seed,issue='query_prefix'))
                if a.generate(seed,{'composition':mode},2,4)['train']!=e['train'][:2]: failures.append(dict(seed=seed,issue='demo_prefix'))
                g=e['test'][3]['input'];out=e['test'][3]['output']
                if (len(g)!=30 or len(g[0])!=30 or sum(bool(v) for row in g for v in row)<55
                        or sum(bool(v) for row in out for v in row)<350): failures.append(dict(seed=seed,issue='boundary_stress'))
    return dict(seeds=seeds,demonstration_counts=list(range(2,7)),queries=4,episodes=episodes,
        labeled_pair_checks=pair_checks,distinct_inputs=len(seen),policies=list(a.rivals()),
        survivors=dict(survivors),failures=failures,scope='Finite Python claims; not all grids or hypotheses.')


def regressions(apply, directory):
    records=[];calls=0
    for filename,order in (('teaching-before.json','hv'),('iteration-before.json','vhvh'),('threshold-before.json','threshold')):
        path=directory/filename
        old=json.loads(path.read_bytes());e=old['episode']
        if order=='threshold':
            vp=a._pass_rkt('vertical','vp')
            hp=a._pass_rkt('horizontal','hp').replace('(= (length hits) 2)','(>= (length hits) 2)')
            rival='(rule! (let ('+vp+'\n'+hp+') (hp (vp g))))'
        else: rival=a.composition_program(order)
        intended=e['program_solution']
        observed=[]
        for pair in e['train']:
            gold=apply(intended,pair['input']);wrong=apply(rival,pair['input']);calls+=2
            assert gold==pair['output'] and gold==wrong,(filename,'not a demo-fitting rival')
            observed.append({'input':pair['input'],'output':gold})
        # Pick the first harmful old query using the frozen Python oracle; then
        # prove that exact pair via protected Racket instead of trusting claims.
        rival_fn=a.rivals()[{'hv':'horizontal_then_vertical','vhvh':'repeat_vh_twice','threshold':'horizontal_at_least_two'}[order]]
        query=next(p for p in e['test'] if rival_fn(p['input'])!=p['output'])
        gold=apply(intended,query['input']);wrong=apply(rival,query['input']);calls+=2
        assert gold==query['output'] and gold!=wrong
        fresh=a.generate(old['seed'],old['settings'],2,4)
        after=[]
        for p in fresh['train']:
            x=apply(intended,p['input']);y=apply(rival,p['input']);calls+=2
            assert x==p['output'];after.append({'input':p['input'],'output':x,'rival_output':y})
        assert any(p['output']!=p['rival_output'] for p in after)
        records.append(dict(frozen_fixture=filename,fixture_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
          seed=old['seed'],settings=old['settings'],program=intended,rival_program=rival,
          old_train=observed,old_query={'input':query['input'],'output':gold,'rival_output':wrong},
          repaired_train=after,demonstrations_before=2,demonstrations_after=2))
    return records,calls


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=32)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--regressions',type=Path)
    args=parser.parse_args()
    if args.out.exists(): raise FileExistsError('Choose a new output directory')
    args.out.mkdir(parents=True)
    report=run_sweep(args.seeds)
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    root=find_root(HOME)
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    calls=0;examples=[];public=args.out/'public';public.mkdir()
    try:
        for seed in (0,17):
            for mode in a.MODES:
                settings={'composition':mode};e=a.generate(seed,settings,6,4)
                for p in e['train']+e['test']:
                    out=apply(e['program_solution'],p['input']);calls+=1
                    assert out==p['output'],(seed,mode,'Python/Racket disagreement')
                    p['output']=out
                e['train']=e['train'][:3]
                examples.append(dict(seed=seed,settings=settings,episode=e,teaching=a.teaching_audit(e)))
                for index in range(4):
                    b=a.public_turn_bytes(e,index);digest=hashlib.sha256(b).hexdigest()
                    (public/f'{digest}.json').write_bytes(b)
        if args.regressions:
            cases,n=regressions(apply,args.regressions);calls+=n
            (args.out/'teaching-regressions.json').write_bytes(raw({'racket':identity,'cases':cases,'evaluations':n}))
    finally: bridge.close()
    (args.out/'examples.private.json').write_bytes(raw(examples))
    report.update(racket=identity,protected_evaluations=calls,public_files=len(list(public.glob('*.json'))),
       source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HOME/'adapter.py',HOME/'canonical.rkt',HOME/'promotion.json',Path(__file__))},
       status='passed' if not report['failures'] else 'failed',training_admitted=False,owner_accepted=False)
    (args.out/'audit.json').write_bytes(raw(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('racket','source_sha256')},indent=2))
    return bool(report['failures'])

if __name__=='__main__': raise SystemExit(main())
