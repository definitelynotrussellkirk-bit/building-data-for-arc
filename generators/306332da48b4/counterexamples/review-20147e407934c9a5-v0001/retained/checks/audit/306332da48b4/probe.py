from __future__ import annotations
from collections import deque
from pathlib import Path
import hashlib, importlib.util, json, sys

ROOT = Path(__file__).resolve().parents[3] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))
GEN = ROOT / "generators/306332da48b4/generator.py"
spec = importlib.util.spec_from_file_location("audit_306", GEN)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def components(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            if grid[r][c]==0 or (r,c) in seen: continue
            color=grid[r][c]; q=deque([(r,c)]); seen.add((r,c)); cells=[]
            while q:
                rr,cc=q.popleft(); cells.append([rr,cc])
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
                        seen.add((nr,nc)); q.append((nr,nc))
            out.append({"color":color,"cells":sorted(cells)})
    return out

records=[]
for requested in (2,3):
    grid=mod.generate(17,0,difficulty="medium",n_blobs=requested)
    records.append({"requested_n_blobs":requested,"self_check":mod.self_check(grid),"actual_components":components(grid),"input":grid})
identical=records[0]["input"]==records[1]["input"]
outdir=Path(__file__).resolve().parent
(outdir/"input.json").write_text(json.dumps(records[1]["input"],indent=2)+"\n")
result={
 "task_id":mod.TASK_ID,
 "generator_sha256":hashlib.sha256(GEN.read_bytes()).hexdigest(),
 "seed":17,"sample_index":0,"difficulty":"medium",
 "finding":"advertised exact n_blobs override is ignored",
 "records":records,
 "both_overrides_yield_identical_grid":identical,
}
(outdir/"probe.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
