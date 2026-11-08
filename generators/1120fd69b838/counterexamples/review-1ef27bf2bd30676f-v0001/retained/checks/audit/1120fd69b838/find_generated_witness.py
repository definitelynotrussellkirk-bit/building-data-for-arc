from __future__ import annotations
from collections import deque
import importlib.util, json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))
source=REPO/'generators/1120fd69b838/generator.py'
spec=importlib.util.spec_from_file_location('audit_target',source)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
DIR=((1,0),(-1,0),(0,1),(0,-1))

def comps(grid):
    h,w=len(grid),len(grid[0]);seen=set();out=[]
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0]==0 or (r0,c0) in seen: continue
            color=grid[r0][c0]; q=[(r0,c0)];seen.add((r0,c0));cells=[]
            while q:
                r,c=q.pop();cells.append((r,c))
                for dr,dc in DIR:
                    p=(r+dr,c+dc)
                    if 0<=p[0]<h and 0<=p[1]<w and p not in seen and grid[p[0]][p[1]]==color:
                        seen.add(p);q.append(p)
            out.append((min(cells),cells))
    return [cells for _,cells in sorted(out)]

def norm(cells):
    cells=tuple(cells)
    mr=min(r for r,c in cells);mc=min(c for r,c in cells)
    return tuple(sorted((r-mr,c-mc) for r,c in cells))
def rot(cells):
    cells=norm(cells);m=max(r for r,c in cells)
    return norm((c,m-r) for r,c in cells)
def flip(cells):
    cells=norm(cells);m=max(c for r,c in cells)
    return norm((r,m-c) for r,c in cells)
def sig(cells):
    cur=norm(cells);xs=[]
    for _ in range(4):
        xs.extend((norm(cur),flip(cur)));cur=rot(cur)
    return min(xs)
def true_out(grid):
    cs=comps(grid);ss=[sig(c) for c in cs]
    return [[8 if ss[r]==ss[c] else 0 for c in range(len(cs))] for r in range(len(cs))]
def area_out(grid):
    cs=comps(grid);sizes=[len(c) for c in cs]
    return [[8 if sizes[r]==sizes[c] else 0 for c in range(len(cs))] for r in range(len(cs))]

for band in ('easy','medium','hard'):
    for seed in range(1000,1200):
        for index in range(20):
            try:g=mod.generate(seed,index,difficulty=band)
            except Exception:continue
            if mod.self_check(g):continue
            if true_out(g)!=area_out(g):
                result={'task_id':mod.TASK_ID,'seed':seed,'sample_index':index,'difficulty':band,
                        'input':g,'actual_by_independent_shape_equivalence':true_out(g),
                        'area_equality_rival':area_out(g),
                        'object_sizes':[len(c) for c in comps(g)],
                        'object_shape_signatures':[list(map(list,sig(c))) for c in comps(g)]}
                Path(__file__).with_name('generated_witness.json').write_text(json.dumps(result,indent=2)+'\n')
                print(json.dumps({k:result[k] for k in ('seed','sample_index','difficulty','object_sizes')},indent=2))
                raise SystemExit(0)
raise SystemExit('no witness found')
