from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

TASK="37fbfdde70b9"
REPO=Path.cwd(); EVIDENCE=REPO.parent/"checks"/"audit"/TASK
SOURCE=REPO/"generators"/TASK/"generator.py"
spec=importlib.util.spec_from_file_location("audit_37",SOURCE); assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def all_seed_rule(grid):
    out=[row[:] for row in grid]; h=len(grid); w=len(grid[0])
    seeds=[(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    for r,c,v in seeds:
        i=1
        while r+i<h and c-i>=0:
            out[r+i][c-i]=v; i+=1
    for r,c,v in seeds:
        out[r][c]=v
    return out

def topmost_per_color(grid):
    out=[row[:] for row in grid]; h=len(grid); w=len(grid[0]); chosen={}
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v and (v not in chosen or (r,c)<chosen[v]): chosen[v]=(r,c)
    for v,(r,c) in chosen.items():
        i=1
        while r+i<h and c-i>=0:
            out[r+i][c-i]=v; i+=1
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            if value:
                out[r][c]=value
    return out

root=find_root(REPO); canon=canonical_pairs(TASK,root=root)
canonical_fit=sum(topmost_per_color(p["input"])==p["output"] for p in canon)
by_band={}; total=unique_color_draws=rival_fit=0
for band in ("easy","medium","hard"):
    unique=matches=0
    for i in range(100):
        grid=mod.generate(23000+i,i,difficulty=band)
        colors=[v for row in grid for v in row if v]
        unique+=int(len(colors)==len(set(colors)))
        matches+=int(topmost_per_color(grid)==all_seed_rule(grid))
    by_band[band]={"draws":100,"one_seed_per_color":unique,"rival_matches_all_seed_rule":matches}
    total+=100; unique_color_draws+=unique; rival_fit+=matches

override_grid=mod.generate(123,0,difficulty="hard",seed_count=4,n_distinct_colors=1,palette_size=1,palette_kind="warm")
override_colors=sorted({v for row in override_grid for v in row if v})
try:
    mod.generate(123,0,grid_h=4)
    grid_h4={"raised":False}
except Exception as exc:
    grid_h4={"raised":True,"exception":type(exc).__name__,"message":str(exc)}

witness=json.loads((EVIDENCE/"input.json").read_text()); racket=json.loads((EVIDENCE/"racket.json").read_text())
actual=racket["results"][0]["output"]; rival=topmost_per_color(witness)
(EVIDENCE/"rival.json").write_text(json.dumps(rival,indent=2)+"\n")
report={
 "schema":"audit-probe-v1","task_id":TASK,
 "generator_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),"rule_hash":racket["executed_rule_hash"],
 "hypothesis":"extend only the topmost seed of each color; ordinary data never has two seeds sharing a color",
 "canonical":{"pairs":len(canon),"rival_matches":canonical_fit},
 "ordinary_generated":{"draws":total,"one_seed_per_color":unique_color_draws,"rival_matches":rival_fit,"per_band":by_band,"seed_formula":"seed=23000+i, sample_index=i, i=0..99"},
 "override_contract":{
   "requested":{"difficulty":"hard","seed_count":4,"n_distinct_colors":1,"palette_size":1,"palette_kind":"warm"},
   "observed_nonzero_colors":override_colors,"observed_distinct_color_count":len(override_colors),
   "advertised_grid_h_4":grid_h4
 },
 "witness":{"self_check":mod.self_check(witness),"actual_equals_rival":actual==rival,"input":"input.json","racket":"racket.json","rival":"rival.json"},
 "command":{"cwd":"repo","argv":["python3","../checks/audit/37fbfdde70b9/probe.py"]}
}
(EVIDENCE/"probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
