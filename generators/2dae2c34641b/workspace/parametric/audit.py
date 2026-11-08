#!/usr/bin/env python3
"""Bounded native routing audit; no owner acceptance or training admission.

The sweep uses Python claims; separate protected Racket execution verifies the
listed labels, finite demo refutations, and edge fixtures. Same-checkout only.
"""
from pathlib import Path
import argparse
from collections import Counter
import hashlib
import importlib.util
import json

HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_routing_audit_adapter',HOME/'adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def raw(value):return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


def run_sweep(seeds=32):
    if type(seeds) is not int or not 1<=seeds<=1024:raise ValueError('seeds must be 1..1024')
    failures=[];seen=set();survivors=Counter();orientations=Counter();counts=Counter()
    episodes=pair_checks=fallbacks=0;boundary_min=900
    for seed in range(seeds):
        inputs={}
        for demos in range(2,7):
            for mode in a.MODES:
                settings={'routing':mode};e=a.generate(seed,settings,demos,4)
                episodes+=1;pair_checks+=len(e['train'])+4
                audit=a.teaching_audit(e);survivors.update(audit['survivors'])
                grids=[raw(p['input']) for p in e['train']+e['test']];seen.update(grids)
                if audit['query_disagreeing_survivors']:failures.append(dict(seed=seed,demos=demos,mode=mode,teaching=audit))
                if len(set(grids))!=len(grids):failures.append(dict(seed=seed,issue='duplicate_input'))
                if demos in inputs and grids!=inputs[demos]:failures.append(dict(seed=seed,issue='setting_affects_inputs'))
                inputs[demos]=grids
                if a.generate(seed,settings,demos,1)['test']!=e['test'][:1]:failures.append(dict(seed=seed,issue='query_prefix'))
                if a.generate(seed,settings,2,4)['train']!=e['train'][:2]:failures.append(dict(seed=seed,issue='demo_prefix'))
                for p in e['train']+e['test']:
                    groups=a.validate_input(p['input']);counts[len(groups)]+=1
                    _,trace=a.route(p['input']);orientations.update(t['orientation'] for t in trace)
                    fallbacks+=sum(t['fallback'] for t in trace)
                g=e['test'][3]['input'];out=e['test'][3]['output']
                cells=sum(bool(v) for row in out for v in row);boundary_min=min(cells,boundary_min)
                if (len(g)!=30 or len(g[0])!=30 or cells<200 or sum(bool(v) for row in g for v in row)!=18
                    or not any(g[0]) or not any(g[-1]) or not any(r[0] for r in g) or not any(r[-1] for r in g)):
                    failures.append(dict(seed=seed,mode=mode,issue='boundary_stress'))
    if fallbacks:failures.append(dict(issue='constructed_grammar_has_blocked_both_candidates',count=fallbacks))
    return dict(seeds=seeds,demo_counts=list(range(2,7)),queries=4,episodes=episodes,
      labeled_pair_checks=pair_checks,distinct_inputs=len(seen),policies=list(a.rivals()),
      survivors=dict(survivors),orientations=dict(orientations),pair_count_checks=dict(counts),
      boundary_min_output_cells=boundary_min,fallbacks=fallbacks,failures=failures,
      scope='Finite Python claims over matched inputs; labeled-pair checks repeat inputs across settings/demo counts.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=32);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError('Choose a new output directory')
    args.out.mkdir(parents=True);public=args.out/'public';public.mkdir()
    report=run_sweep(args.seeds)
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(find_root(HOME)/'shared/runtime')
    calls=0;examples=[];refutations=[];edge_cases=[]
    try:
        for seed in (0,17):
            for mode in a.MODES:
                settings={'routing':mode};e=a.generate(seed,settings,6,4)
                for p in e['train']+e['test']:
                    actual=apply(e['program_solution'],p['input']);calls+=1
                    assert actual==p['output'],(seed,mode,'Racket label mismatch')
                    p['output']=actual
                e['train']=e['train'][:3]
                examples.append(dict(seed=seed,settings=settings,episode=e,teaching=a.teaching_audit(e)))
                for index in range(4):
                    b=a.public_turn_bytes(e,index);digest=hashlib.sha256(b).hexdigest()
                    (public/f'{digest}.json').write_bytes(b)
                if mode=='avoid_shorter':
                    for name,program,fn in (
                        ('no_occupancy',a.routing_program(avoid=False),lambda g:a.route(g,avoid=False)[0]),
                        ('area_priority',a.routing_program(priority='area'),lambda g:a.route(g,priority='area')[0]),
                        ('height_priority',a.routing_program(priority='height'),lambda g:a.route(g,priority='height')[0])):
                        pairs=[]
                        for p in e['train'][:2]:
                            other=apply(program,p['input']);calls+=1
                            assert other==fn(p['input']),name
                            pairs.append(dict(input=p['input'],output=p['output'],rival_output=other))
                        assert any(p['output']!=p['rival_output'] for p in pairs),(seed,name)
                        refutations.append(dict(seed=seed,program=e['program_solution'],rival=name,rival_program=program,train=pairs))
        # Literal no-occupancy causal fixture: the collision is (3,3), not an
        # original endpoint. Tie/fallback fixture is outside the sampled grammar.
        g=[[0]*9 for _ in range(7)];g[1][1]=g[3][4]=4;g[0][3]=g[6][7]=2
        good=apply(a.routing_program(),g);bad=apply(a.routing_program(avoid=False),g);calls+=2
        assert good==a.route(g)[0] and good!=bad and good[3][3]==4 and good[0][4]==2
        edge_cases.append(dict(name='interior_path_contact',input=g,output=good,counterfactual_output=bad,
            program=a.routing_program(),counterfactual_program=a.routing_program(avoid=False)))
        g=[[0]*8 for _ in range(8)];g[0][2]=g[3][3]=7;g[1][0]=g[3][2]=1
        actual=apply(a.routing_program(),g);calls+=1
        assert actual==a.route(g)[0] and actual[3][2]==1
        edge_cases.append(dict(name='equal_distance_reading_tie_and_total_fallback_off_sampling_grammar',input=g,output=actual,program=a.routing_program()))
    finally:bridge.close()
    (args.out/'examples.private.json').write_bytes(raw(examples))
    (args.out/'teaching-refutations.json').write_bytes(raw({'racket':identity,'cases':refutations}))
    (args.out/'edge-cases.json').write_bytes(raw({'racket':identity,'cases':edge_cases}))
    report.update(racket=identity,protected_evaluations=calls,public_files=len(list(public.glob('*.json'))),
      source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HOME/'adapter.py',HOME/'canonical.rkt',HOME/'promotion.json',Path(__file__))},
      status='passed' if not report['failures'] else 'failed',owner_accepted=False,training_admitted=False)
    (args.out/'audit.json').write_bytes(raw(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('racket','source_sha256')},indent=2))
    return bool(report['failures'])

if __name__=='__main__':raise SystemExit(main())
