#!/usr/bin/env python3
"""Findings-only experiment for this packet's two immutable audit targets.

Stages a clean runtime and records real Racket outputs, input-only independent
predictions, source hashes, and exact reproductions. Does not modify targets.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

TARGETS = ('3fcea70c3acf', '67e9e17efb62')

def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def objects(g):
    seen=set(); result=[]
    for r,row in enumerate(g):
        for c,color in enumerate(row):
            if color == 0 or (r,c) in seen:
                continue
            todo=[(r,c)]; seen.add((r,c)); cells=[]
            while todo:
                rr,cc=todo.pop(); cells.append((rr,cc))
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if (0<=nr<len(g) and 0<=nc<len(g[0]) and (nr,nc) not in seen
                            and g[nr][nc] == color):
                        seen.add((nr,nc)); todo.append((nr,nc))
            r0=min(x[0] for x in cells); r1=max(x[0] for x in cells)
            c0=min(x[1] for x in cells); c1=max(x[1] for x in cells)
            result.append({'color':color,'cells':cells,'size':len(cells),'r0':r0,'c0':c0,
                           'crop':[row[c0:c1+1] for row in g[r0:r1+1]],
                           'bbox_area':(r1-r0+1)*(c1-c0+1)})
    return result

def pack_objects(g, key='size'):
    obs=sorted(objects(g),key=lambda x:(-x[key],x['r0'],x['c0'],x['color']))
    if not obs:
        return []
    w=sum(len(x['crop'][0]) for x in obs)+len(obs)-1
    out=[[0]*w for _ in range(max(len(x['crop']) for x in obs))]
    col=0
    for x in obs:
        for r,row in enumerate(x['crop']):
            out[r][col:col+len(row)]=row
        col+=len(x['crop'][0])+1
    return out

def bar_answer(g):
    color=next(v for v in g[0] if v)
    length=sum(v != 0 for v in g[0]); width=len(g[0])
    runs=list(range(1,length+1))+list(range(length-1,0,-1))
    stream=[]
    for i,n in enumerate(runs):
        if i: stream.append(0)
        stream.extend([color]*n)
    stream += [0]*((-len(stream))%width)
    return [stream[i:i+width] for i in range(0,len(stream),width)]

def worker(args):
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source
    from scripts.generator_semantic_gate import _RuleOracle
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    command=[sys.executable,*sys.argv]
    # Small independent-model checks, not claims about the target generators.
    assert pack_objects([[1,0,2,2]]) == [[2,2,0,1]]
    assert bar_answer([[3,3,3,0,0],[0]*5,[0]*5]) == [[3,0,3,3,0],[3,3,3,0,3],[3,0,3,0,0]]
    summaries=[]
    for task in TARGETS:
        gen=importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
        rule=canonical_rule_source(task)
        identity={'task_id':task,'generator_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                  'rule_source_sha256':hashlib.sha256(rule.encode()).hexdigest(),
                  'rule_hash_normalized':hashlib.sha256(' '.join(rule.split()).encode()).hexdigest()[:12],
                  'command':command,'runtime_cwd':str(Path.cwd())}
        oracle=_RuleOracle(task)
        if not oracle.ready: raise RuntimeError(oracle.error)
        count=0; failures=[]; witnesses=[]
        def evaluate(grid):
            nonlocal count
            actual,error=oracle.apply(grid); count+=1
            if error: failures.append({'input':grid,'error':error})
            return actual
        def witness(label,grid,seed=None,index=None,overrides=None,rival=None,**extra):
            path=f'{task}_{label}.json'
            data={**identity,'seed':seed,'sample_index':index,'overrides':overrides or {},
                  'input':grid,'validator_errors':gen.self_check(grid),
                  'actual_racket_output':evaluate(grid),'rival_output':rival,**extra}
            save(out/path,data); witnesses.append(path); return data
        report={**identity,'failures':failures}
        try:
            canon=canonical_pairs(task)
            unique={digest(p):p for p in canon}
            model=pack_objects if task==TARGETS[0] else bar_answer
            report['canonical']={'raw_pairs':len(canon),'unique_pairs':len(unique),
                'model_matches':sum(model(p['input'])==p['output'] for p in unique.values()),
                'validator_accepts':sum(not gen.self_check(p['input']) for p in unique.values())}
            report['canonical']['racket_matches']=sum(evaluate(p['input'])==p['output'] for p in unique.values())
            if task==TARGETS[0]:
                seed,index=2718,1
                baseline=gen.generate(seed,index,n_objs=2)
                overrides={'n_objs':2,'palette_size':4,'n_distinct_colors':4}
                grid=gen.generate(seed,index,**overrides)
                observed=len({v for row in grid for v in row}-{0})
                w=witness('ignored_palette_override',grid,seed,index,overrides,
                    same_as_n_objs_only=(baseline==grid),observed_nonzero_colors=observed,
                    requested_nonzero_colors=4,classification='reproduced override-contract mismatch',
                    domain='ordinary generator output, validator accepted')
                report['ignored_palette_override']={'same_as_baseline':baseline==grid,'observed_colors':observed,
                    'requested_colors':4,'validator_errors':w['validator_errors']}
                report['shape_bank_size']=sum(len(v) for v in gen._SHAPES_BY_SIZE.values())
                matches=0; bbox_matches=0; object_counts=Counter(); no_witness=True
                for i in range(120):
                    g=gen.generate(1000+i,i)
                    actual=evaluate(g); expected=model(g); bbox=pack_objects(g,'bbox_area')
                    matches+=actual==expected; bbox_matches+=bbox==actual
                    object_counts[len(objects(g))]+=1
                    if actual != expected: failures.append({'stage':'size-model','seed':1000+i,'sample_index':i,'input':g,'actual':actual,'expected':expected})
                    if no_witness and bbox != actual:
                        no_witness=False
                        witness('bbox_area_rival',g,1000+i,i,rival=bbox,
                            domain='ordinary generator output',classification='candidate rival already discriminated by generator')
                report['sample']={'seed_base':1000,'samples':120,'seed_formula':'1000+i; sample_index=i; default difficulty',
                    'model_racket_matches':matches,'bbox_area_rival_matches':bbox_matches,'object_counts':dict(object_counts)}
                report['bbox_rival_canonical_matches']=sum(pack_objects(p['input'],'bbox_area')==p['output'] for p in canon)
                eq=gen.generate(0,0,texture='equal_sizes')
                witness('equal_sizes_tie',eq,0,0,{'texture':'equal_sizes'},
                    domain='explicit degenerate texture, not ordinary distinct-size domain',
                    classification='documentation/validator mismatch, not ambiguous Racket rule',
                    independent_tie_sorted_output=pack_objects(eq),observed_sizes=[x['size'] for x in objects(eq)])
            else:
                overrides={'bar_len':3,'bar_lenght':8}
                try:
                    g=gen.generate(2718,1,**overrides)
                    baseline=gen.generate(2718,1,bar_len=3)
                    w=witness('unknown_override',g,2718,1,overrides,
                        same_as_baseline=baseline==g,observed_axes=gen.observe_overrides(g),
                        domain='ordinary valid generator output; unknown key is a caller typo',
                        classification='unknown override silently accepted')
                    report['unknown_override']={'accepted':True,'same_as_baseline':baseline==g,'validator_errors':w['validator_errors']}
                except ValueError as exc:
                    report['unknown_override']={'accepted':False,'error':str(exc)}
                matches=0; tested=0; output_hashes=set(); all_color_outputs=set()
                for length in range(3,9):
                    for width in range(5,24):
                        if length>=width: continue
                        for position in ('left','right'):
                            g=gen.generate(1,1,grid_h=3,grid_w=width,bar_len=length,color=1,position_bias=position)
                            expected=bar_answer(g); actual=evaluate(g); tested+=1; matches+=actual==expected
                            if actual != expected or gen.self_check(g):
                                failures.append({'stage':'length-width-position-basis','length':length,'width':width,
                                    'position':position,'input':g,'actual':actual,'expected':expected,'validator':gen.self_check(g)})
                            output_hashes.add(digest(expected))
                            for color in range(1,10):
                                all_color_outputs.add(digest([[color if v else 0 for v in row] for row in expected]))
                report['exhaustive_basis']={'lengths':[3,8],'widths':[5,23],'condition':'length < width',
                    'positions':['left','right'],'fixed_height':3,'fixed_color':1,'cases':tested,
                    'racket_model_matches':matches,'unique_structural_outputs':len(output_hashes),
                    'all_nine_color_outputs_enumerated_in_python':len(all_color_outputs)}
                mutated=[('body_noise',lambda g:g[1].__setitem__(0,2)),
                         ('second_color',lambda g:g[0].__setitem__(1,2)),
                         ('bar_gap',lambda g:g[0].__setitem__(1,0))]
                rejects={}
                for name,mutation in mutated:
                    g=gen.generate(1,1,grid_h=3,grid_w=9,bar_len=5,color=1,position_bias='left')
                    mutation(g); rejects[name]=gen.self_check(g)
                report['malformed_input_rejections']=rejects
            report['oracle_calls']=count; report['witness_paths']=witnesses
            save(out/f'{task}.json',report); summaries.append(report)
            print(f'{task}: {count} Racket calls, {len(failures)} oracle/model failures; witnesses {witnesses}',flush=True)
        finally:
            oracle.close()
    return 1 if any(x['failures'] for x in summaries) else 0

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--out',required=True)
    ap.add_argument('--runtime'); ap.add_argument('--worker',action='store_true')
    args=ap.parse_args()
    if args.worker: return worker(args)
    repo=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(repo/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    runtime=Path(args.runtime).resolve() if args.runtime else Path(tempfile.mkdtemp(prefix='arcpuzzles-audits-'))
    receipt=prepare_runtime(Catalog(repo),runtime,task_ids=list(TARGETS))
    shutil.copy2(__file__,runtime/'audit_assigned.py')
    env=dict(os.environ); env.pop('PYTHONPATH',None); env.pop('PYTHONHOME',None); env['PYTHONNOUSERSITE']='1'
    command=[sys.executable,'audit_assigned.py','--worker','--out',str(out)]
    started=time.monotonic()
    result=subprocess.run(command,cwd=runtime,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=240)
    (out/'audit.log').write_text(result.stdout); print(result.stdout,end='')
    save(out/'run.json',{'command':command,'runtime_cwd':str(runtime),'exit_code':result.returncode,
        'elapsed_seconds':time.monotonic()-started,'task_ids':list(TARGETS),
        'source_files':[r for r in receipt['files'] if r['library_path'].startswith(tuple('generators/'+t+'/' for t in TARGETS))]})
    return result.returncode

if __name__=='__main__':
    raise SystemExit(main())
