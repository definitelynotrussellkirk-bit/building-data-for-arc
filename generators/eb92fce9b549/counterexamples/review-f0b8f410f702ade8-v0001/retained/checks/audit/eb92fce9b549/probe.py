from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

TASK = "eb92fce9b549"
REPO = Path.cwd()
EVIDENCE = REPO.parent / "checks" / "audit" / TASK
SOURCE = REPO / "generators" / TASK / "generator.py"

spec = importlib.util.spec_from_file_location("audit_eb92", SOURCE)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

CARDINAL = ((-1,0),(1,0),(0,-1),(0,1))

def comps(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r,c) in seen: continue
            color=grid[r][c]; stack=[(r,c)]; seen.add((r,c)); cells=[]
            while stack:
                x=stack.pop(); cells.append(x)
                for dr,dc in CARDINAL:
                    y=(x[0]+dr,x[1]+dc)
                    if 0<=y[0]<h and 0<=y[1]<w and y not in seen and grid[y[0]][y[1]]==color:
                        seen.add(y); stack.append(y)
            out.append(tuple(sorted(cells)))
    return out

def box(cells):
    rs=[r for r,_ in cells]; cs=[c for _,c in cells]
    return min(rs),min(cs),max(rs),max(cs)

def metrics(cells):
    r0,c0,r1,c1=box(cells); h=r1-r0+1; w=c1-c0+1
    return h*w, 2*(h+w)-4

def rank(grid, mode):
    objects=comps(grid)
    if mode=="area":
        key=lambda cells: (-metrics(cells)[0], box(cells), cells)
    elif mode=="perimeter_then_area":
        key=lambda cells: (-metrics(cells)[1], -metrics(cells)[0], box(cells), cells)
    else: raise ValueError(mode)
    out=[[0]*len(grid[0]) for _ in grid]
    for label,cells in enumerate(sorted(objects,key=key),start=2):
        for r,c in cells: out[r][c]=label
    return out

root=find_root(REPO)
canon=canonical_pairs(TASK,root=root)
canonical_fit=sum(rank(p["input"],"perimeter_then_area")==p["output"] for p in canon)
by_band={}; total=0; fit=0
for band in ("easy","medium","hard"):
    band_fit=0
    for i in range(100):
        grid=mod.generate(17000+i,i,difficulty=band)
        total+=1
        same=rank(grid,"area")==rank(grid,"perimeter_then_area")
        fit+=int(same); band_fit+=int(same)
    by_band[band]={"draws":100,"rival_matches_area_rank":band_fit}

witness=json.loads((EVIDENCE/"input.json").read_text())
racket=json.loads((EVIDENCE/"racket.json").read_text())
actual=racket["results"][0]["output"]
rival=rank(witness,"perimeter_then_area")
(EVIDENCE/"rival.json").write_text(json.dumps(rival,indent=2)+"\n")
report={
  "schema":"audit-probe-v1","task_id":TASK,
  "generator_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
  "rule_hash":racket["executed_rule_hash"],
  "hypothesis":"rank components by bbox perimeter descending, breaking ties by bbox area, instead of bbox area",
  "canonical":{"pairs":len(canon),"rival_matches":canonical_fit},
  "ordinary_generated":{"draws":total,"rival_matches":fit,"per_band":by_band,"seed_formula":"seed=17000+i, sample_index=i, i=0..99"},
  "witness":{"self_check":mod.self_check(witness),"area_metrics":[metrics(c) for c in comps(witness)],"actual_equals_rival":actual==rival,"input":"input.json","racket":"racket.json","rival":"rival.json"},
  "command":{"cwd":"repo","argv":["python3","../checks/audit/eb92fce9b549/probe.py"]}
}
(EVIDENCE/"probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
