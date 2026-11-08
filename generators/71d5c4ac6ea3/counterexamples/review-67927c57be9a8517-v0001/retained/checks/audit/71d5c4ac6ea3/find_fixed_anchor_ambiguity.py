from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators/71d5c4ac6ea3/generator.py"
spec = importlib.util.spec_from_file_location("audit_gen_71", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

def points(grid, color):
    return [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color]

def solve(grid, fixed_origin=None):
    origins=points(grid,9)
    if not origins: return [[0 for _ in row] for row in grid]
    origin=fixed_origin if fixed_origin is not None else origins[0]
    offsets=[(r-origin[0],c-origin[1]) for r,c in points(grid,1)]
    out=[[0 for _ in row] for row in grid]
    for sr,sc in points(grid,2):
        for dr,dc in offsets:
            r,c=sr+dr,sc+dc
            if 0<=r<len(out) and 0<=c<len(out[0]): out[r][c]=8
    return out

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

found=None
for band in ("easy","medium","hard"):
    for seed in range(2048):
        for start in range(128):
            try:
                grids=[gen.generate(seed,start+i,difficulty=band) for i in range(4)]
            except Exception:
                continue
            if any(gen.self_check(g,difficulty=band) for g in grids):
                continue
            anchors=[points(g,9)[0] for g in grids]
            if not (anchors[0]==anchors[1]==anchors[2] and anchors[3]!=anchors[0]):
                continue
            fixed=anchors[0]
            demo_truth=[solve(g) for g in grids[:3]]
            demo_rival=[solve(g,fixed) for g in grids[:3]]
            q_truth=solve(grids[3]); q_rival=solve(grids[3],fixed)
            if demo_truth==demo_rival and q_truth!=q_rival:
                diff=[(r,c,q_truth[r][c],q_rival[r][c]) for r in range(len(q_truth)) for c in range(len(q_truth[0])) if q_truth[r][c]!=q_rival[r][c]]
                found={
                    "schema":"arcpuzzles-audit-fixed-anchor-ambiguity-v1",
                    "task_id":"71d5c4ac6ea3",
                    "generator_sha256":sha(GEN_PATH),
                    "lesson_policy":"3 consecutive demonstrations plus the next generated query",
                    "seed":seed,"start":start,"difficulty":band,
                    "demo_sample_indices":[start,start+1,start+2],"query_sample_index":start+3,
                    "demo_anchors":[list(x) for x in anchors[:3]],"query_anchor":list(anchors[3]),
                    "rival_fixed_origin":list(fixed),
                    "rival_description":f"Ignore the color-9 anchor and always treat {fixed} as the offset origin.",
                    "all_inputs_pass_self_check":True,
                    "demos":[{"input":g,"actual_output":t,"rival_output":r,"anchor":list(a)} for g,t,r,a in zip(grids[:3],demo_truth,demo_rival,anchors[:3])],
                    "query":{"input":grids[3],"actual_output":q_truth,"rival_output":q_rival,"anchor":list(anchors[3]),"different_cells":diff},
                    "command":"PYTHONPATH=shared/runtime:src python3 ../checks/audit/71d5c4ac6ea3/find_fixed_anchor_ambiguity.py",
                    "working_directory":str(ROOT),
                }
                break
        if found: break
    if found: break
if found is None: raise SystemExit('no witness found')
out=Path(__file__).with_name('fixed_anchor_ambiguity_candidate.json')
out.write_text(json.dumps(found,indent=2)+'\n')
inputs=[x['input'] for x in found['demos']]+[found['query']['input']]
Path(__file__).with_name('input.json').write_text(json.dumps(inputs,indent=2)+'\n')
print(json.dumps({k:found[k] for k in ('seed','start','difficulty','demo_anchors','query_anchor','rival_fixed_origin')},indent=2))
print(out)
