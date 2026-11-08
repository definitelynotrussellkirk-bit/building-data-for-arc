#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, itertools, json, os, sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2] / 'repo'
RUNTIME = REPO / 'shared' / 'runtime'
sys.path.insert(0, str(RUNTIME))


def load(task: str):
    path = REPO / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'audit_{task}', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def anchor_copy_full(grid, boundary_mode='minimal_shift'):
    h,w=len(grid),len(grid[0])
    src=next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3)
    dst=next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==4)
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==2]
    dr,dc=dst[0]-src[0],dst[1]-src[1]
    tr=[(r+dr,c+dc) for r,c in cells]
    if boundary_mode=='minimal_shift':
        rr=[r for r,c in tr]; cc=[c for r,c in tr]
        sr=max(0,-min(rr)) + min(0,h-1-max(rr))
        sc=max(0,-min(cc)) + min(0,w-1-max(cc))
        tr=[(r+sr,c+sc) for r,c in tr]
    elif boundary_mode=='wrap':
        tr=[(r%h,c%w) for r,c in tr]
    out=[[0]*w for _ in range(h)]
    for r,c in tr:
        if 0<=r<h and 0<=c<w: out[r][c]=8
    out[dst[0]][dst[1]]=4
    return out


def audit327(max_seed: int):
    task='327c3478236b'; mod=load(task)
    totals=Counter(); first=None
    for difficulty in [None,'easy','hard']:
        for seed in range(max_seed):
            for idx in range(12):
                g=mod.generate(seed,idx,difficulty=difficulty)
                totals['draws']+=1
                errs=mod.self_check(g,difficulty=difficulty)
                if errs:
                    totals['self_check_rejected']+=1
                    continue
                totals['accepted']+=1
                h,w=len(g),len(g[0])
                src=next((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==3)
                dst=next((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==4)
                cells=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==2]
                dr,dc=dst[0]-src[0],dst[1]-src[1]
                tr=[(r+dr,c+dc) for r,c in cells]
                clipped=[p for p in tr if not (0<=p[0]<h and 0<=p[1]<w)]
                if clipped:
                    totals['accepted_with_clipping']+=1
                    if first is None:
                        first={
                          'task_id':task,'seed':seed,'sample_index':idx,'difficulty':difficulty,
                          'input':g,'self_check':errs,'src':src,'dst':dst,'vector':[dr,dc],
                          'template_cells':cells,'translated_cells':tr,'out_of_bounds':clipped,
                          'rival_name':'minimal_shift_full_copy',
                          'rival_output':anchor_copy_full(g,'minimal_shift'),
                        }
    return {'summary':dict(totals),'first':first}


def split_quads(g):
    h,w=len(g),len(g[0])
    sr=next(r for r,row in enumerate(g) if all(v==1 for v in row))
    sc=next(c for c in range(w) if all(g[r][c]==1 for r in range(h)))
    vals=[]
    for r in range(sr):
        row=[]
        for c in range(sc):
            row.append((g[r][c],g[r][sc+1+c],g[sr+1+r][c],g[sr+1+r][sc+1+c]))
        vals.append(row)
    return vals


def priority_output(g, order):
    vals=split_quads(g)
    out=[]
    for row in vals:
        rr=[]
        for cell in row:
            rr.append(next((cell[i] for i in order if cell[i]!=0),0))
        out.append(rr)
    return out


def overlap_constraints(g):
    vals=split_quads(g)
    present=Counter()
    for row in vals:
        for cell in row:
            nz=tuple(i for i,v in enumerate(cell) if v)
            if len(nz)>=2: present[nz]+=1
    return {','.join(map(str,k)):v for k,v in sorted(present.items())}


def audit_a233(max_seed: int):
    task='a23328d45092'; mod=load(task)
    canonical=(0,1,2,3)
    rivals=[p for p in itertools.permutations(range(4)) if p!=canonical]
    totals=Counter(); first=None
    for difficulty in [None,'easy','hard']:
        for seed in range(max_seed):
            # Check several cyclic starts: actual generator lessons conventionally use consecutive indexes.
            draws=[mod.generate(seed,i,difficulty=difficulty) for i in range(20)]
            labels=[priority_output(g,canonical) for g in draws]
            for start in range(16):
                demos=range(start,start+3); q=start+3
                totals['windows']+=1
                for rival in rivals:
                    if all(priority_output(draws[i],rival)==labels[i] for i in demos):
                        totals['rival_demo_survivals']+=1
                        if priority_output(draws[q],rival)!=labels[q]:
                            totals['ambiguous_windows']+=1
                            if first is None:
                                first={
                                  'task_id':task,'seed':seed,'difficulty':difficulty,
                                  'sample_indices':list(range(start,start+4)),
                                  'demo_indices':list(range(start,start+3)),
                                  'query_index':start+3,
                                  'canonical_order':['TL','TR','BL','BR'],
                                  'rival_order':[['TL','TR','BL','BR'][i] for i in rival],
                                  'rival_permutation':list(rival),
                                  'inputs':[draws[i] for i in range(start,start+4)],
                                  'canonical_outputs':[labels[i] for i in range(start,start+4)],
                                  'rival_outputs':[priority_output(draws[i],rival) for i in range(start,start+4)],
                                  'self_checks':[mod.self_check(draws[i],difficulty=difficulty) for i in range(start,start+4)],
                                  'overlap_constraints':[overlap_constraints(draws[i]) for i in range(start,start+4)],
                                }
                                return {'summary':dict(totals),'first':first}
    return {'summary':dict(totals),'first':first}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--max-seed',type=int,default=1000)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    data={'327c3478236b':audit327(args.max_seed),'a23328d45092':audit_a233(args.max_seed)}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v['summary'] for k,v in data.items()},indent=2))
    for k,v in data.items():
        print(k,'found',v['first'] is not None)

if __name__=='__main__': main()
