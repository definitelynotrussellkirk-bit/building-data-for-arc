from pathlib import Path
from copy import deepcopy
import hashlib, importlib.util, json
ROOT=Path(__file__).resolve().parents[3]/"repo"
OUT=Path(__file__).resolve().parent
TASK="4a9e2bc51201"
source=ROOT/"generators"/TASK/"generator.py"
spec=importlib.util.spec_from_file_location("audit_target",source)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
row=next(json.loads(s) for s in (ROOT/"shared/data/canonical/puzzles.jsonl").read_text().splitlines() if json.loads(s)["task_id"]==TASK)
def grid(rows):return [[int(v) for v in r] for r in rows]
def open_count(a):
    d=next(c for c in range(len(a[0])) if all(r[c]==5 for r in a))
    n=0
    for row in a:
        for k in range(1,min(d,len(row)-1-d)+1):
            n+=((row[d-k] not in (0,5)) != (row[d+k] not in (0,5)))
    return n
def rival(a):
    return deepcopy(a) if open_count(a)<4 else g.rule_mirror(a)
pairs=[{"input":grid(p["input"]),"output":grid(p["output"])} for p in row["train"]+[row["test"]]]
report={"task_id":TASK,"generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"rule_hash":g.RULE_HASH,
        "canonical":[{"pair":i,"open_orbits":open_count(p["input"]),"self_check":g.self_check(p["input"]),"rival_matches_canonical":rival(p["input"])==p["output"]} for i,p in enumerate(pairs)],"ordinary":{},"overrides":{}}
for band in (None,"easy","medium","hard"):
    errors=[];counts=[];rival_fits=0;declared_refuted=0
    for i in range(96):
        a=g.generate(21000+i,i,difficulty=band)
        errors+=g.self_check(a)
        counts.append(open_count(a))
        rival_fits+=rival(a)==g.rule_mirror(a)
        declared_refuted+=all(f(deepcopy(a))!=g.rule_mirror(a) for f in g.SEMANTIC_RIVALS.values())
    report["ordinary"][str(band)]={"seed_formula":"21000 + sample_index","indices":[0,95],"samples":96,"self_check_errors":errors,"open_count_range":[min(counts),max(counts)],"count_gated_rival_fits":rival_fits,"all_declared_rivals_refuted":declared_refuted}
checks=0;failures=[]
for h in (6,11):
 for w in (7,8,9,10,11):
  for bias in ("left","center","right"):
   for side in ("left","right","mixed"):
    for occupied in (0,3):
     for colors in (1,4):
      opts=dict(grid_h=h,grid_w=w,divider_bias=bias,open_side=side,n_open_pairs=4,n_occupied_pairs=occupied,n_distinct_colors=colors)
      a=g.generate(31000+checks,29,**opts)
      if g.self_check(a) or g.observe_overrides(a)!=opts:failures.append({"seed":31000+checks,"sample_index":29,"overrides":opts,"self_check":g.self_check(a),"observed":g.observe_overrides(a)})
      checks+=1
report["overrides"]={"samples":checks,"seed_formula":"31000 + iteration index","sample_index":29,"domains":{"grid_h":[6,11],"grid_w":[7,8,9,10,11],"divider_bias":["left","center","right"],"open_side":["left","right","mixed"],"n_occupied_pairs":[0,3],"n_distinct_colors":[1,4],"n_open_pairs":[4]},"failures":failures}
demos=[]
for i in range(3):
 a=g.generate(41000,i,difficulty="medium")
 demos.append({"input":a,"output":g.rule_mirror(a)})
query=pairs[-1]
report["selected_lesson"]={"demonstrations":[{"seed":41000,"sample_index":i,"difficulty":"medium","overrides":{},"input":p["input"],"python_supplementary_output":p["output"],"rival_output":rival(p["input"])} for i,p in enumerate(demos)],"query":{"source":"canonical test","seed":None,"sample_index":None,"overrides":None,"input":query["input"],"canonical_output":query["output"],"rival_output":rival(query["input"]),"open_orbits":open_count(query["input"]),"self_check":g.self_check(query["input"])},"declared_lesson_identifiable":g.lesson_identifiable(demos,query)}
(OUT/"input.json").write_text(json.dumps({"inputs":[p["input"] for p in pairs+demos]},indent=2)+"\n")
(OUT/"probe-results.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="selected_lesson"}))
