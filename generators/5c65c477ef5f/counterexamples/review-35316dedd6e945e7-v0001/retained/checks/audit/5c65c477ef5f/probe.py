"""Bounded audit preparation; does not execute an authoritative reference."""
from pathlib import Path
import hashlib, importlib.util, json
from reviewer_support import canonical_pairs, canonical_path, find_root
TASK="5c65c477ef5f"
ROOT=find_root(Path.cwd())
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/"generators"/TASK/"generator.py"
spec=importlib.util.spec_from_file_location("audit_5c65",SOURCE)
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
def components(grid):
    unseen={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=0};result=[]
    while unseen:
        start=min(unseen);unseen.remove(start);todo=[start];cells={start};color=grid[start[0]][start[1]]
        while todo:
            r,c=todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen and grid[p[0]][p[1]]==color:
                    unseen.remove(p);todo.append(p);cells.add(p)
        result.append(cells)
    return result

def description(cells):
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    norm={(r-r0,c-c0) for r,c in cells};h=max(r for r,c in norm)+1;w=max(c for r,c in norm)+1
    lr=norm=={(r,w-1-c) for r,c in norm};ud=norm=={(h-1-r,c) for r,c in norm}
    perimeter=sum(p not in cells for r,c in cells for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)))
    return {"cells":[list(p) for p in sorted(cells)],"size":len(cells),"r0":r0,"c0":c0,"h":h,"w":w,"lr":lr,"ud":ud,"perimeter":perimeter}

def predict(grid,*,rival=False):
    ds=[description(cs) for cs in components(grid)]
    eligible=[d for d in ds if (not(d["lr"] and d["ud"]) if rival else not d["lr"] and not d["ud"])]
    d=min(eligible,key=lambda a:(a["size"],a["perimeter"],a["r0"],a["c0"]))
    out=[[0]*d["w"] for _ in range(d["h"])]
    for r,c in d["cells"]:out[r-d["r0"]][c-d["c0"]]=8
    return out

pairs=canonical_pairs(TASK,root=ROOT,labeled_only=True)
record=next(json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip() and json.loads(line).get("task_id")==TASK)
grid=[[0]*12 for _ in range(10)]
shapes=[(2,1,1,[(0,0),(0,1),(1,1),(2,1),(2,2)]),(3,5,1,[(0,0),(1,0),(2,0),(3,0),(3,1),(3,2),(3,3)]),(4,1,8,[(0,0),(0,1),(0,2),(1,1)])]
for color,r0,c0,cells in shapes:
    for r,c in cells:grid[r+r0][c+c0]=color
checks=[]
for band in ("easy","medium","hard"):
    for seed in (0,17,91):
        for index in range(6):
            inp=gen.generate(seed,index,difficulty=band)
            checks.append({"difficulty":band,"seed":seed,"sample_index":index,"overrides":{},"self_check":gen.self_check(inp,difficulty=band),"mirror_rival_equal":predict(inp)==predict(inp,rival=True),"symmetry_counts":sorted(int(d["lr"])+int(d["ud"]) for d in map(description,components(inp)))})
report={"schema":"audit-5c65c477ef5f-v1","task_id":TASK,"generator_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),"rule_text_sha256":hashlib.sha256(record["program_solution"].encode()).hexdigest(),"rival":"Select smallest object not symmetric on BOTH axes, using selected rule's area/perimeter/top-left ranking, then crop/recolor8.","canonical_fit":[{"variant":p["variant"],"split":p["split"],"pair_index":p["pair_index"],"rival_equals_label":predict(p["input"],rival=True)==p["output"]} for p in pairs],"input":grid,"input_origin":"hand-authored boundary witness; no generation seed/index/overrides","target_self_check":gen.self_check(grid),"components":[description(cs) for cs in components(grid)],"diagnostic_rule_output":predict(grid),"rival_output":predict(grid,rival=True),"generated_probe":checks,"reference_execution":{"status":"pending","wrapper_argv":["WORK/.venv/bin/python","review.py","run","/dev/shm/arc-review-604d32c6dec0/WORK/.venv/bin/python","-m","arcpuzzles","apply",TASK,"--input","../checks/audit/5c65c477ef5f/input.json","--out","../checks/audit/5c65c477ef5f/racket.json"],"wrapper_cwd":"/dev/shm/arc-review-604d32c6dec0","effective_cwd":str(ROOT),"environment":{"TMPDIR":"/dev/shm/arc-review-604d32c6dec0-tmp"},"input_batch_order":["canonical-train-0","canonical-train-1","canonical-test-0","hand-authored-single-axis-decoy"]}}
(OUT/"input.json").write_text(json.dumps([p["input"] for p in pairs]+[grid],indent=2)+"\n")
(OUT/"probe-output.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"source":report["generator_sha256"],"rule":report["rule_text_sha256"],"canonical_fit":report["canonical_fit"],"self_check":report["target_self_check"],"diagnostic_rule":report["diagnostic_rule_output"],"rival":report["rival_output"],"bounded_draws":len(checks),"rival_equal_draws":sum(c["mirror_rival_equal"] for c in checks),"invalid_draws":sum(bool(c["self_check"]) for c in checks)},indent=2))
