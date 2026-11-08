from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators/76e1a5257af0/generator.py"
spec = importlib.util.spec_from_file_location("audit_gen_76", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

CARD = [(-1,0),(1,0),(0,-1),(0,1)]

def markers(grid):
    h,w=len(grid),len(grid[0]); out=[]
    for r in range(h):
        for c in range(w):
            v=grid[r][c]
            if v not in (1,2,3,4):
                continue
            if not any(0 <= r+dr < h and 0 <= c+dc < w and grid[r+dr][c+dc] == v for dr,dc in CARD):
                out.append((r,c,v))
    return out

def crop(grid):
    pts=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    if not pts: return []
    r0=min(r for r,_ in pts); r1=max(r for r,_ in pts)
    c0=min(c for _,c in pts); c1=max(c for _,c in pts)
    return [row[c0:c1+1] for row in grid[r0:r1+1]]

def rot(g, code):
    if code==1: return [row[:] for row in g]
    if code==2: return [list(row) for row in zip(*g[::-1])]
    if code==3: return [row[::-1] for row in g[::-1]]
    if code==4: return [list(row) for row in zip(*g)][::-1]
    raise ValueError(code)

def solve(grid, remap=None):
    remap=remap or {}
    ms=markers(grid)
    cleaned=[row[:] for row in grid]
    for r,c,_ in ms: cleaned[r][c]=0
    tpl=crop(cleaned)
    out=[[0 for _ in row] for row in grid]
    for mr,mc,code in ms:
        stamp=rot(tpl, remap.get(code,code))
        for r,row in enumerate(stamp):
            for c,v in enumerate(row):
                if v:
                    rr,cc=mr+r,mc+c
                    if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                        out[rr][cc]=v
    return out

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

found=None
for band in ("easy","medium","hard"):
    for seed in range(256):
        for start in range(64):
            grids=[]
            try:
                grids=[gen.generate(seed,start+i,difficulty=band) for i in range(4)]
            except Exception:
                continue
            if any(gen.self_check(g,difficulty=band) for g in grids):
                continue
            demo_codes=sorted({v for g in grids[:3] for _,_,v in markers(g)})
            query_codes=sorted({v for _,_,v in markers(grids[3])})
            for missing in sorted(set(query_codes)-set(demo_codes)):
                wrong=1 if missing != 1 else 2
                remap={missing:wrong}
                demo_truth=[solve(g) for g in grids[:3]]
                demo_rival=[solve(g,remap) for g in grids[:3]]
                q_truth=solve(grids[3]); q_rival=solve(grids[3],remap)
                if demo_truth == demo_rival and q_truth != q_rival:
                    diff=[(r,c,q_truth[r][c],q_rival[r][c]) for r in range(len(q_truth)) for c in range(len(q_truth[0])) if q_truth[r][c] != q_rival[r][c]]
                    found={
                        "schema":"arcpuzzles-audit-rotation-ambiguity-v1",
                        "task_id":"76e1a5257af0",
                        "generator_sha256":sha(GEN_PATH),
                        "lesson_policy":"3 consecutive demonstrations plus the next generated query",
                        "seed":seed,"start":start,"difficulty":band,
                        "demo_sample_indices":[start,start+1,start+2],"query_sample_index":start+3,
                        "demo_codes":demo_codes,"query_codes":query_codes,
                        "unseen_query_code":missing,"rival_remap":{str(missing):wrong},
                        "rival_description":f"Use the authority mapping for observed codes, but map unseen code {missing} to rotation code {wrong}.",
                        "all_inputs_pass_self_check":True,
                        "demos":[{"input":g,"actual_output":t,"rival_output":r,"marker_codes":sorted({v for _,_,v in markers(g)})} for g,t,r in zip(grids[:3],demo_truth,demo_rival)],
                        "query":{"input":grids[3],"actual_output":q_truth,"rival_output":q_rival,"marker_codes":query_codes,"different_cells":diff},
                        "command":"PYTHONPATH=shared/runtime:src python3 ../checks/audit/76e1a5257af0/find_rotation_ambiguity.py",
                        "working_directory":str(ROOT),
                    }
                    break
            if found: break
        if found: break
    if found: break

if found is None:
    raise SystemExit("no witness found")
out=Path(__file__).with_name("rotation_ambiguity_candidate.json")
out.write_text(json.dumps(found,indent=2)+"\n")
inputs=[x["input"] for x in found["demos"]]+[found["query"]["input"]]
Path(__file__).with_name("input.json").write_text(json.dumps(inputs,indent=2)+"\n")
print(json.dumps({k:found[k] for k in ("seed","start","difficulty","demo_codes","query_codes","unseen_query_code","rival_remap")},indent=2))
print(out)
