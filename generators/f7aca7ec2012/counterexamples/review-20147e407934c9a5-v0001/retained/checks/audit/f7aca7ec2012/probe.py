from __future__ import annotations
from collections import deque
from pathlib import Path
import hashlib, importlib.util, json, sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
GEN = ROOT / "generators/f7aca7ec2012/generator.py"
spec = importlib.util.spec_from_file_location("audit_f7", GEN)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

COUNTEREXAMPLE = [
[5,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,2,2,0,0,0,0],
[0,0,0,0,0,0,0,0,0,2,2,0,0,0,0],
[0,5,0,0,0,0,0,0,0,2,0,0,0,0,0],
[0,5,5,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,5,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

def comps(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            color=grid[r][c]
            if color==0 or (r,c) in seen: continue
            q=deque([(r,c)]); seen.add((r,c)); cells=[]
            while q:
                rr,cc=q.popleft(); cells.append((rr,cc))
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
                        seen.add((nr,nc)); q.append((nr,nc))
            out.append((color,cells))
    return out

def crop_flip(color_cells):
    color,cells=color_cells
    rs=[r for r,c in cells]; cs=[c for r,c in cells]
    r0,r1=min(rs),max(rs); c0,c1=min(cs),max(cs)
    out=[[0]*(c1-c0+1) for _ in range(r1-r0+1)]
    for r,c in cells: out[r-r0][c1-c]=color
    return out

def global_rival(grid):
    g=[row[:] for row in grid]; g[0][0]=0
    objects=comps(g)
    target=max(objects,key=lambda x:len(x[1]))
    return crop_flip(target)

def relation(grid):
    legend=grid[0][0]; g=[row[:] for row in grid]; g[0][0]=0
    objects=comps(g)
    legend_objects=[o for o in objects if o[0]==legend]
    if not legend_objects: return "no_legend_target"
    lt=max(legend_objects,key=lambda x:len(x[1])); largest=max(len(c) for _,c in objects)
    nlargest=sum(len(c)==largest for _,c in objects)
    if len(lt[1])==largest and nlargest==1: return "strict_global_target"
    if len(lt[1])==largest: return "tie"
    return "other_larger"

counts={k:0 for k in ("strict_global_target","tie","other_larger","no_legend_target")}
for band in ("easy","medium","hard"):
    for seed in range(500):
        counts[relation(mod.generate(seed,seed*17+3,difficulty=band))]+=1

outdir=Path(__file__).resolve().parent
(outdir/"input.json").write_text(json.dumps(COUNTEREXAMPLE,indent=2)+"\n")
result={
 "task_id":mod.TASK_ID,
 "generator_sha256":hashlib.sha256(GEN.read_bytes()).hexdigest(),
 "self_check":mod.self_check(COUNTEREXAMPLE),
 "rival_name":"ignore_legend_take_globally_largest_then_flip",
 "rival_output":global_rival(COUNTEREXAMPLE),
 "production_probe":{"bands":["easy","medium","hard"],"seeds_per_band":500,"sample_index_formula":"seed*17+3","total":1500,"counts":counts},
}
(outdir/"probe.json").write_text(json.dumps(result,indent=2)+"\n")
(outdir/"rival.json").write_text(json.dumps({"output":result["rival_output"]},indent=2)+"\n")
print(json.dumps(result,indent=2))
