#!/usr/bin/env python3
"""Find deterministic four-pair episodes that expose plausible shortcut ambiguity.

This is audit-only evidence: it never edits generator sources. It uses the selected
public generator and simple observable rival predicates to locate a 3-demo + 1-query
window where the rival fits every demonstration but disagrees on the query.
"""
from __future__ import annotations
import argparse, copy, hashlib, json
from collections import deque
from pathlib import Path
from reviewer_support import load_selected_generator

ROOT = Path(__file__).resolve().parents[2] / "repo"


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def comps(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
      for c in range(w):
        color=grid[r][c]
        if color==0 or (r,c) in seen: continue
        q=[(r,c)]; seen.add((r,c)); cells=[]
        while q:
          rr,cc=q.pop(); cells.append((rr,cc))
          for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr,nc=rr+dr,cc+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
              seen.add((nr,nc)); q.append((nr,nc))
        out.append((color,cells))
    return out


def row_span(grid):
    out=copy.deepcopy(grid)
    for color,cells in comps(grid):
      by={}
      for r,c in cells: by.setdefault(r,[]).append(c)
      for r,cs in by.items():
        for c in range(min(cs),max(cs)+1): out[r][c]=color
    return out


def bbox_fill(grid):
    out=copy.deepcopy(grid)
    for color,cells in comps(grid):
      rs=[p[0] for p in cells]; cs=[p[1] for p in cells]
      for r in range(min(rs),max(rs)+1):
        for c in range(min(cs),max(cs)+1): out[r][c]=color
    return out


def find_5f(limit):
    tid='5f8201e3482c'; gen,path,source_sha=load_selected_generator(tid,root=ROOT)
    for seed in range(limit):
      pairs=[]
      for i in range(4):
        x=gen.generate(seed,i,difficulty=None); y=row_span(x); rival=bbox_fill(x)
        pairs.append({'sample_index':i,'input':x,'true_output_python':y,'rival_output':rival,
                      'rival_matches':rival==y,'self_check':gen.self_check(x)})
      if all(p['rival_matches'] for p in pairs[:3]) and not pairs[3]['rival_matches']:
        return {'schema':'audit-shortcut-episode-v1','task_id':tid,'generator_path':str(path.relative_to(ROOT)),
                'generator_sha256':source_sha,'seed':seed,'difficulty':None,'demo_count':3,
                'rival':'fill_each_component_bounding_box','true_rule_mirror':'per-component per-row horizontal span closure',
                'pairs':pairs,'input_sha256':[sha(p['input']) for p in pairs]}
    raise SystemExit(f'no 5f episode in {limit} seeds')


def selected_idx(gen, grid):
    return sum(v==2 for row in grid for v in row)-1


def find_74(limit):
    tid='74a2d06b72b1'; gen,path,source_sha=load_selected_generator(tid,root=ROOT)
    for seed in range(limit):
      pairs=[]
      for i in range(4):
        x=gen.generate(seed,i,difficulty=None); idx=selected_idx(gen,x)
        pairs.append({'sample_index':i,'input':x,'selected_index':idx,'rival_matches':idx==0,
                      'self_check':gen.self_check(x)})
      if all(p['rival_matches'] for p in pairs[:3]) and not pairs[3]['rival_matches']:
        return {'schema':'audit-shortcut-episode-v1','task_id':tid,'generator_path':str(path.relative_to(ROOT)),
                'generator_sha256':source_sha,'seed':seed,'difficulty':None,'demo_count':3,
                'rival':'always_select_outermost_frame','true_rule_observable':'selected_index = count(color-2 markers)-1',
                'pairs':pairs,'input_sha256':[sha(p['input']) for p in pairs]}
    raise SystemExit(f'no 74 episode in {limit} seeds')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--task',required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--limit',type=int,default=20000)
    a=ap.parse_args(); result=find_5f(a.limit) if a.task=='5f8201e3482c' else find_74(a.limit)
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'task_id':result['task_id'],'seed':result['seed'],'rival':result['rival'],
                      'demo_matches':[p['rival_matches'] for p in result['pairs'][:3]],
                      'query_matches':result['pairs'][3]['rival_matches'],'out':str(a.out)},indent=2))
if __name__=='__main__': main()
