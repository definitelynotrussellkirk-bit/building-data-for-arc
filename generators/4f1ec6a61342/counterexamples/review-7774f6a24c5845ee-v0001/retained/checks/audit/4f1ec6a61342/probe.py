from pathlib import Path
from collections import deque
import hashlib, json
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator
TASK = "4f1ec6a61342"
OUT = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd() / "generators" / TASK / "generator.py")
gen, source, source_hash = load_selected_generator(TASK, root=ROOT)

def rooms(grid):
    seen = {(0, 0)}
    regions = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if (r,c) in seen or grid[r][c] == 5:
                continue
            seen.add((r,c)); q = deque([(r,c)]); cells = []
            while q:
                x,y = q.popleft(); cells.append((x,y))
                for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                    if 0 <= nx < h and 0 <= ny < w and (nx,ny) not in seen and grid[nx][ny] != 5:
                        seen.add((nx,ny)); q.append((nx,ny))
            regions.append(cells)
    return regions

def predict(grid, shortcut=False):
    rr = rooms(grid)
    counts = [sum(grid[r][c] == 2 for r,c in cells) for cells in rr]
    target = grid[0][0]
    if shortcut and target >= 4:
        target = min((x for x in counts if x >= 3), default=-1)
    out = [[5 if x == 5 else 0 for x in row] for row in grid]
    for cells,count in zip(rr,counts):
        if count == target:
            for r,c in cells: out[r][c] = 8
    return out

canonical = canonical_pairs(TASK, root=ROOT)
assert all(predict(p["input"],True) == p["output"] for p in canonical)
counts = {"draws":0,"invalid":0,"rival_matches":0,"rival_mismatches":0,"even_mismatches":0,"odd_mismatches":0}
first = None
for band in ("easy", "medium", "hard"):
    grids = [gen.generate(17,i,difficulty=band) for i in range(200)]
    matches = []
    for i,g in enumerate(grids):
        errors=gen.self_check(g,difficulty=band)
        assert errors == [], (band,i,errors)
        match=predict(g,True) == predict(g)
        matches.append(match); counts["draws"]+=1
        counts["rival_matches" if match else "rival_mismatches"]+=1
        if not match: counts["even_mismatches" if i%2==0 else "odd_mismatches"]+=1
    if first is None:
        for start in range(197):
            window=matches[start:start+4]
            if window[:3] == [True]*3 and not window[3]:
                first={"seed":17,"difficulty":band,"start":start,"sample_indices":list(range(start,start+4)),"query_position":3,"overrides":{},"grids":grids[start:start+4]}
                break
assert first is not None, counts
inputs=[p["input"] for p in canonical] + first.pop("grids")
for name,rival in gen.CANONICAL_SHORTCUTS.items():
    assert all(rival(p["input"])==p["output"] for p in canonical),name
report={"task_id":TASK,"generator_path":str(source.relative_to(ROOT)),"generator_sha256":source_hash,"canonical_ledger_sha256":hashlib.sha256(canonical_path(ROOT).read_bytes()).hexdigest(),"rule_hash":gen.RULE_HASH,"scope":{"seed":17,"sample_indices":[0,199],"bands":["easy","medium","hard"],"overrides":{},"unique_inputs":len({json.dumps(gen.generate(17,i,difficulty=b)) for b in ("easy","medium","hard") for i in range(200)})},"counts":counts,"canonical_pairs":len(canonical),"canonical_fit":True,"declared_rival_names":list(gen.CANONICAL_SHORTCUTS),"lesson":first,"cases":[]}
for i,g in enumerate(inputs):
    case={"apply_batch_index":i,"input":g,"self_check":gen.self_check(g),"rival_output":predict(g,True),"mirror_output":predict(g),"room_seed_counts":[sum(g[r][c]==2 for r,c in cells) for cells in rooms(g)]}
    if i < len(canonical): case.update({"origin":"canonical", "variant":canonical[i]["variant"],"split":canonical[i]["split"],"pair_index":canonical[i]["pair_index"],"recorded_output":canonical[i]["output"]})
    else: case.update({"origin":"generated", "seed":17,"sample_index":first["sample_indices"][i-len(canonical)],"difficulty":first["difficulty"],"overrides":{}})
    report["cases"].append(case)
OUT.joinpath("inputs.json").write_text(json.dumps(inputs)+"\n")
OUT.joinpath("probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"counts":counts,"lesson":first,"source_sha256":source_hash}))
