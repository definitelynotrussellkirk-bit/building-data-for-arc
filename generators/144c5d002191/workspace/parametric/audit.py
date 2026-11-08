#!/usr/bin/env python3
"""Bounded native sweep, protected labels, and a before/after teaching regression."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import public_challenge_bytes

HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stamp_audit_adapter',HOME/'adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def historical_lesson(seed):
    """Exact initial two-demo construction, retained only as a regression."""
    result=[]
    for i in (0,1):
        rng=a._rng(seed,'train',i)
        h,w=rng.randint(9,15),rng.randint(12,22)
        g=[[0]*w for _ in range(h)]
        colors=sorted(rng.sample(range(1,10),4))
        if i==0:
            a._paint(g,[(0,1),(0,2),(1,0),(1,1)],h-4,1,colors[0])
            high,low=colors[3],colors[1]
            anchors=[(0,w-4,high),(0,w-3,low),(0,w-2,high),(1,w-5,high)]
        else:
            a._paint(g,[(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1)],h-5,1,colors[3])
            anchors=[(0,0,colors[2]),(h-2,w-1,colors[1])]
            anchors += [(h-1,w-1-k,colors[0]) for k in (0,2,4)]
        for r,c,v in anchors:g[r][c]=v
        result.append(g)
    return result

def run(seeds,out):
    if out.exists():raise FileExistsError('Use a fresh audit output directory')
    out.mkdir(parents=True)
    report={'schema':'arcpuzzles-task-parametric-audit-v1','task_id':a.TASK,
            'seeds':seeds,'demo_counts':[2,3,4,5,6], 'policies':list(a.POLICIES),
            'episodes':0,'labeled_pair_claims':0,'failures':[],
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (HOME/'adapter.py',HOME/'audit.py',HOME/'stamp_orientation.py',HOME/'canonical.rkt')}}
    unique=set();shapes=set();colors=set();boundary=0
    for seed in range(seeds):
        for policy in a.POLICIES:
            full=a.generate(seed,{'policy':policy},6,4)
            for demos in report['demo_counts']:
                ep=a.generate(seed,{'policy':policy},demos,4)
                report['episodes']+=1;report['labeled_pair_claims']+=demos+4
                errors=a.teaching_failures(ep)
                if errors:report['failures'].append({'seed':seed,'policy':policy,'demos':demos,'errors':errors})
                assert ep['train']==full['train'][:demos] and ep['test']==full['test']
                assert len({digest(p['input']) for p in ep['train']+ep['test']})==demos+4
            for p in full['train']+full['test']:
                unique.add(digest(p['input']));shapes.add((len(p['input']),len(p['input'][0])))
            stress=full['test'][3]
            assert sum(v!=0 for row in stress['input'] for v in row)>=60
            assert sum(v!=0 for row in stress['output'] for v in row)>=60
            boundary+=1
            colors.add(a.winning_color(a._stamp(full['train'][1]['input'])))
    report.update(distinct_inputs=len(unique),sizes=sorted(shapes),boundary_checks=boundary,
                  relay_selected_colors=sorted(colors))
    labels=[];calls=0
    with RacketBridge(timeout=10,startup_timeout=60) as bridge:
        runtime=bridge.runtime_identity
        assert runtime['protected']
        # Remove local runtime filenames only; retain hashes and protection canaries.
        report['racket']={k:v for k,v in runtime.items() if not k.endswith('_path')}
        for seed in (0,17):
            for policy in a.POLICIES:
                ep=a.generate(seed,{'policy':policy},3,4)
                for pair in ep['train']+ep['test']:
                    actual=a.prior.execute_program(bridge,ep['program_solution'],pair['input']);calls+=1
                    assert actual==pair['output']
                    pair['output']=actual
                for i in range(4):
                    public=a.public_turn(ep,i);raw=public_challenge_bytes(public)
                    (out/'public').mkdir(exist_ok=True)
                    (out/'public'/f'{hashlib.sha256(raw).hexdigest()}.json').write_bytes(raw)
                labels.append({'seed':seed,**ep})
        correct=a.program({'policy':'horizontal_mirror'})
        anchor='(marker (in-list markers))'
        assert correct.count(anchor)==1
        rival=correct.replace(anchor,'''(marker (in-list (sort markers (lambda (a b)
          (or (< (obj-c1 a) (obj-c1 b))
              (and (= (obj-c1 a) (obj-c1 b)) (< (obj-r1 a) (obj-r1 b))))))))''')
        regression={'rule':'horizontal_mirror','rival':'column_major_marker_order',
                    'program':correct,'rival_program':rival,'before':[], 'after':[]}
        for stage,grids in [('before',historical_lesson(0)),
                            ('after',[p['input'] for p in a.generate(0,{'policy':'horizontal_mirror'},2,4)['train']])]:
            for g in grids:
                expected=a.prior.execute_program(bridge,correct,g)
                wrong=a.prior.execute_program(bridge,rival,g);calls+=2
                regression[stage].append({'input':g,'output':expected,'rival_output':wrong})
        query=a.generate(0,{'policy':'horizontal_mirror'},2,4)['test'][0]['input']
        regression['query']={'input':query,'output':a.prior.execute_program(bridge,correct,query),
                             'rival_output':a.prior.execute_program(bridge,rival,query)};calls+=2
        assert all(p['output']==p['rival_output'] for p in regression['before'])
        assert any(p['output']!=p['rival_output'] for p in regression['after'])
        assert regression['query']['output']!=regression['query']['rival_output']
        report['teaching_regression']={'before_rival_survives':True,'after_rival_refuted':True,
                                       'query_differs':True,'demo_cost_before':2,'demo_cost_after':2}
        write(out/'teaching-regression.json',regression)
        # Counterfactual uses exact matched qualification demo; qualification supplies final binding.
        causal=a.generate(17,{'policy':'visible_majority'},3,4)['train'][1]
        wrong=a.prior.execute_program(bridge,a.counterfactual_program(),causal['input']);calls+=1
        assert wrong!=causal['output']
        report['causal_probe']={'selected_color':a.winning_color(a._stamp(causal['input'])),
                                'changed_cells':sum(x!=y for r,s in zip(causal['output'],wrong) for x,y in zip(r,s))}
    report['protected_racket_evaluations']=calls
    report['status']='passed' if not report['failures'] else 'failed'
    report['limits']='Finite named-rival and bounded-seed evidence; not universal uniqueness, owner acceptance, or training admission.'
    write(out/'episodes.private.json',labels)
    write(out/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in {'racket','sizes','source_sha256'}},indent=2))
    return 0 if not report['failures'] else 1

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    opts=p.parse_args()
    if not 1<=opts.seeds<=256:p.error('seeds must be in 1..256')
    raise SystemExit(run(opts.seeds,opts.out))
