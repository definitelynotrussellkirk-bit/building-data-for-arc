#!/usr/bin/env python3
from __future__ import annotations
from collections import Counter
import hashlib, importlib.util, json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))
from reviewer_support import canonical_pairs


def load(task):
    p=REPO/'generators'/task/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+task,p)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m,p

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+'\n')

def d544_transform(grid, allowed=None):
    out=[row[:] for row in grid]
    h,w=len(grid),len(grid[0])
    for c in range(w):
        r=0
        while r<h:
            if grid[r][c]!=5:
                r+=1; continue
            start=r
            while r<h and grid[r][c]==5: r+=1
            n=r-start
            if n>=3 and n%2==1 and (allowed is None or n in allowed):
                out[start+n//2][c]=2
    return out

def audit_d544():
    task='d5447d3527e6'; gen,p=load(task)
    pairs=canonical_pairs(task,root=REPO)
    canon_fit=all(d544_transform(x['input'],{3,5})==x['output'] for x in pairs)
    lengths=Counter(); samples=0; unique=set(); ordinary_disagree=[]
    for band in ('easy','medium','hard'):
        for seed in range(100):
            g=gen.generate(seed,0,difficulty=band)
            samples+=1; unique.add(json.dumps(g,separators=(',',':')))
            h,w=len(g),len(g[0])
            for c in range(w):
                r=0
                while r<h:
                    if g[r][c]!=5: r+=1; continue
                    s=r
                    while r<h and g[r][c]==5: r+=1
                    n=r-s
                    if n>=3 and n%2: lengths[n]+=1
            if d544_transform(g)!=d544_transform(g,{3,5}): ordinary_disagree.append([band,seed])
    g=[[0]*7 for _ in range(9)]
    for r in range(7): g[r][2]=5
    for r in range(2,6): g[r][5]=5
    intended=d544_transform(g); rival=d544_transform(g,{3,5})
    record={
      'task_id':task,'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'canonical_shortcut':'only odd run lengths 3 or 5',
      'canonical_pairs':len(pairs),'shortcut_fits_all_canonical_pairs':canon_fit,
      'ordinary_sampling':{'bands':['easy','medium','hard'],'seeds_per_band':100,'sample_index':0,
        'draws':samples,'unique_inputs':len(unique),'odd_target_length_counts':dict(sorted(lengths.items())),
        'true_vs_rival_disagreements':ordinary_disagree},
      'counterexample':{'validator_errors':gen.self_check(g),'input':g,'intended_output':intended,
        'rival_output':rival,'outputs_disagree':intended!=rival}
    }
    d=ROOT/'checks/audit'/task
    dump(d/'input.json',g); dump(d/'counterexample.json',record)
    return record

def count_slope_rival(gen,grid):
    info,errors=gen._analyse(grid)
    if errors: raise ValueError(errors)
    n=info['n_cells']; ordered=info['ordered_red']; last=ordered[-1]
    if n==1:
        step_r=-1 if last[0] > info['grid_size']/2 else 1
        step_c=step_r  # count 1 -> force main slope
    else:
        step_r=-1
        step_c=-1 if n%2==1 else 1
    bottom=(last[0]+n*step_r,last[1]+n*step_c)
    out=[[7]*info['grid_size'] for _ in range(info['grid_size'])]
    for i in range(n+1):
        r=bottom[0]+i*step_r; c=bottom[1]+i*step_c
        if 0<=r<info['grid_size'] and 0<=c<info['grid_size']: out[r][c]=2
    return out

def audit_6e():
    task='6e18fab2c2e5'; gen,p=load(task); seed=1234; band='medium'
    lesson=[]
    for i in range(6):
        g=gen.generate(seed,i,difficulty=band); intended=gen.rule_mirror(g); rival=count_slope_rival(gen,g)
        lesson.append({'sample_index':i,'observed':gen.observe_overrides(g),'validator_errors':gen.self_check(g),
                       'input':g,'intended_output':intended,'rival_output':rival,'rival_matches':rival==intended})
    demos=[{'input':x['input'],'output':x['intended_output']} for x in lesson[:5]]
    query={'input':lesson[5]['input'],'output':lesson[5]['intended_output']}
    record={
      'task_id':task,'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rule_hash':gen.RULE_HASH,
      'rival':'derive output diagonal slope from n_cells parity (odd=main, even=anti), ignoring the input slope',
      'seed':seed,'difficulty':band,'demos_sample_indices':[0,1,2,3,4],'query_sample_index':5,
      'demos_all_fit_rival':all(x['rival_matches'] for x in lesson[:5]),
      'query_disagrees':not lesson[5]['rival_matches'],
      'lesson_identifiable_result':gen.lesson_identifiable(demos,query),
      'lesson':lesson,
    }
    d=ROOT/'checks/audit'/task
    dump(d/'input.json',lesson[5]['input']); dump(d/'counterexample.json',record)
    return record

if __name__=='__main__':
    result={'d5447d3527e6':audit_d544(),'6e18fab2c2e5':audit_6e()}
    dump(ROOT/'checks/audit/summary.json',result)
    print(json.dumps({
      'd544': {k:result['d5447d3527e6'][k] for k in ('generator_sha256','shortcut_fits_all_canonical_pairs')},
      'd544_sampling': result['d5447d3527e6']['ordinary_sampling'],
      '6e': {k:result['6e18fab2c2e5'][k] for k in ('generator_sha256','demos_all_fit_rival','query_disagrees','lesson_identifiable_result')}
    },indent=2))
