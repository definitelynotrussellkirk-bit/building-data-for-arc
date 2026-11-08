#!/usr/bin/env python3
"""Bounded native analogy audit; no owner acceptance or training admission."""
from __future__ import annotations
from collections import Counter
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes

HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('analogy_audit_adapter',HOME/'adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def run(seeds,out):
    if out.exists():raise FileExistsError('Use a fresh audit output directory')
    out.mkdir(parents=True)
    report={'schema':'arcpuzzles-task-parametric-audit-v1','task_id':a.TASK,
            'seeds':seeds,'demo_counts':[2,3,4,5,6],'directions':list(a.DIRECTIONS),
            'episodes':0,'labeled_pair_claims':0,'failures':[],
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                            (HOME/'adapter.py',HOME/'audit.py',HOME/'canonical.rkt',HOME.parents[1]/'generator.py')}}
    unique=set();sizes=set();transforms=Counter();arities=set();boundary=0
    for seed in range(seeds):
        for direction in a.DIRECTIONS:
            full=a.generate(seed,{'direction':direction},6,4)
            for demos in report['demo_counts']:
                ep=a.generate(seed,{'direction':direction},demos,4)
                report['episodes']+=1;report['labeled_pair_claims']+=demos+4
                failures=a.teaching_failures(ep)
                if failures:report['failures'].append({'seed':seed,'direction':direction,'demos':demos,'failures':failures})
                assert ep['train']==full['train'][:demos] and ep['test']==full['test']
                assert len({digest(p['input']) for p in ep['train']+ep['test']})==demos+4
            for pair in full['train']+full['test']:
                g=pair['input'];unique.add(digest(g));sizes.add((len(g),len(g[0])))
                code,mapping=a.infer(g);transforms[code]+=1;arities.add(len(mapping))
                q=a.split_panels(g)[2]
                unmapped={v for row in q for v in row if v}-set(mapping)
                assert unmapped <= {v for row in pair['output'] for v in row}
            stress=full['test'][3]
            assert (len(stress['input']),len(stress['input'][0]))==(30,30)
            assert (len(stress['output']),len(stress['output'][0]))==(30,9)
            assert sum(v!=0 for row in stress['input'] for v in row)>=300
            assert sum(v!=0 for row in stress['output'] for v in row)>=70
            boundary+=1
    report.update(distinct_inputs=len(unique),sizes=sorted(sizes),boundary_checks=boundary,
                  transforms=dict(sorted(transforms.items())),map_arities=sorted(arities),
                  finite_policy_count=len(a.rival_predictions(a.scene(0,'train',0),'inverse')))
    episodes=[];calls=0
    with RacketBridge(timeout=10,startup_timeout=60) as bridge:
        runtime=bridge.runtime_identity;assert runtime['protected']
        report['racket']={k:v for k,v in runtime.items() if not k.endswith('_path')}
        for seed in (0,17):
            for direction in a.DIRECTIONS:
                ep=a.generate(seed,{'direction':direction},3,4)
                for pair in ep['train']+ep['test']:
                    actual=a.execute(bridge,ep['program_solution'],pair['input']);calls+=1
                    assert actual==pair['output'];pair['output']=actual
                for index in range(4):
                    raw=public_challenge_bytes(a.public_turn(ep,index));(out/'public').mkdir(exist_ok=True)
                    (out/'public'/f'{hashlib.sha256(raw).hexdigest()}.json').write_bytes(raw)
                episodes.append({'seed':seed,**ep})
        # Intentional negative control, not an alleged production defect:
        # two clockwise examples permit a constant counterclockwise-transfer
        # rival; the real second demonstration uses a reflection and rejects it.
        correct=a.program({'direction':'inverse'})
        rival=a.program({'direction':'forward'}).replace(
            '(tq (apply-transform-name name query))',
            "(tq (apply-transform-name 'rot270 query))").replace('(list a b)','(list b a)')
        regression={'kind':'intentional_negative_control','program':correct,'rival_program':rival,
                    'rival':'fixed_counterclockwise_query_transform','weak_train':[],
                    'real_demo_count':2,'universal_identifiability':False}
        for seed in (0,17):
            g=a.scene(seed,'train',0)
            expected=a.execute(bridge,correct,g);wrong=a.execute(bridge,rival,g);calls+=2
            assert expected==wrong
            regression['weak_train'].append({'input':g,'output':expected,'rival_output':wrong})
        g=a.scene(0,'train',1)
        expected=a.execute(bridge,correct,g);wrong=a.execute(bridge,rival,g);calls+=2
        assert expected!=wrong
        regression['separating_query_also_actual_second_demo']={'input':g,'output':expected,'rival_output':wrong}
        report['teaching_control']={'weak_lesson_rival_survives':True,'actual_second_demo_refutes':True,
                                    'label':'intentional negative control, not a discovered production defect'}
        write(out/'teaching-control.json',regression)
        causal=a.generate(17,{'direction':'inverse'},3,4)['train'][0]
        wrong=a.execute(bridge,a.counterfactual_program(),causal['input']);calls+=1
        assert causal['output']!=wrong
        code,mapping=a.infer(causal['input'])
        report['causal_probe']={'inferred_transform':code,'inferred_map':mapping,
                                'changed_cells':sum(x!=y for r,s in zip(causal['output'],wrong) for x,y in zip(r,s))}
    report['protected_racket_evaluations']=calls
    report['status']='passed' if not report['failures'] else 'failed'
    report['limits']='Finite declared-policy and seed evidence only. One terminal separator makes the 30x30 input natural; output is 30x9. No owner acceptance, training admission or universal uniqueness.'
    write(out/'episodes.private.json',episodes);write(out/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('racket','sizes','source_sha256')},indent=2))
    return 0 if not report['failures'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    options=p.parse_args()
    if not 1<=options.seeds<=256:p.error('seeds must be in 1..256')
    raise SystemExit(run(options.seeds,options.out))
