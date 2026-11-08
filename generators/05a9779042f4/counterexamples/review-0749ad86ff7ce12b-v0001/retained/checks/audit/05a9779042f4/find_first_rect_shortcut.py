#!/usr/bin/env python3
from __future__ import annotations
from copy import deepcopy
import hashlib, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]/'repo'
GEN=ROOT/'generators/05a9779042f4/generator.py'
spec=importlib.util.spec_from_file_location('audit_05a',GEN)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def comps(g):
    h=len(g); w=len(g[0]); seen=set(); out=[]
    for sr in range(h):
      for sc in range(w):
        if g[sr][sc]==0 or (sr,sc) in seen: continue
        color=g[sr][sc]; stack=[(sr,sc)]; seen.add((sr,sc)); cells=[]
        while stack:
          r,c=stack.pop(); cells.append((r,c))
          for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr,nc=r+dr,c+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and g[nr][nc]==color:
              seen.add((nr,nc)); stack.append((nr,nc))
        out.append((color,tuple(cells)))
    return out
def eligible(g):
    result=[]
    for color,cells in comps(g):
      rs=[r for r,c in cells]; cs=[c for r,c in cells]
      r0,r1=min(rs),max(rs); c0,c1=min(cs),max(cs)
      if color==6 and len(cells)==(r1-r0+1)*(c1-c0+1) and r1-r0+1>=3 and c1-c0+1>=3:
        result.append((r0,c0,r1,c1))
    return sorted(result)
def apply(g,first_only=False):
    out=deepcopy(g); boxes=eligible(g)
    if first_only: boxes=boxes[:1]
    for r0,c0,r1,c1 in boxes:
      for r in range(r0+1,r1):
       for c in range(c0+1,c1): out[r][c]=0
    return out

found=None
for seed in range(50000):
  grids=[mod.generate(seed,i,difficulty='medium') for i in range(4)]
  truth=[apply(g) for g in grids]; rival=[apply(g,True) for g in grids]
  if all(truth[i]==rival[i] for i in range(3)) and truth[3]!=rival[3]:
    found=(seed,grids,truth,rival); break
if found is None: raise SystemExit('no witness found')
seed,grids,truth,rival=found
receipt={
 'schema':'audit-shortcut-witness-v1','task_id':'05a9779042f4',
 'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
 'seed':seed,'difficulty':'medium','demo_indices':[0,1,2],'query_index':3,
 'rival':'hollow_only_first_eligible_rectangle',
 'eligible_counts':[len(eligible(g)) for g in grids],
 'demos':[{'input':grids[i],'output':truth[i],'rival_output':rival[i]} for i in range(3)],
 'query':{'input':grids[3],'output':truth[3],'rival_output':rival[3]},
 'claim':'The first-eligible-only rival fits all three demonstrations and changes the query.'
}
out=Path(__file__).with_name('first-rect-shortcut-witness.json'); out.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'seed':seed,'eligible_counts':receipt['eligible_counts'],'out':str(out)},indent=2))
