from __future__ import annotations

import json
from pathlib import Path

from reviewer_support import canonical_pairs, load_selected_generator

TASK_ID = "fa103c7aa88b"
ROOT = Path.cwd()
OUT = ROOT.parent / "checks" / "audit" / TASK_ID


def components(grid):
    key = grid[0][0]
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, key) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = rr+dr, cc+dc
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr,nc)); stack.append((nr,nc))
            found.append(cells)
    found.sort(key=lambda cells: (-len(cells), max(r for r,_ in cells)-min(r for r,_ in cells)+1, max(c for _,c in cells)-min(c for _,c in cells)+1))
    return found


def norm(cells):
    r0 = min(r for r,_ in cells); c0 = min(c for _,c in cells)
    return {(r-r0,c-c0) for r,c in cells}


def template_family(grid):
    comps = components(grid)
    if len(comps) < 2:
        return False
    a, b = norm(comps[0]), norm(comps[1])
    h = max(max(r for r,_ in a), max(r for r,_ in b)) + 1
    w = max(max(c for _,c in a), max(c for _,c in b)) + 1
    expected = [
        {(r,c) for r in range(h) for c in range(w-1)},
        {(r,c) for r in range(h-1) for c in range(w)},
    ]
    return {frozenset(a), frozenset(b)} == {frozenset(x) for x in expected}


def shortcut(grid):
    key = grid[0][0]
    comps = components(grid)
    a, b = norm(comps[0]), norm(comps[1])
    h = max(max(r for r,_ in a), max(r for r,_ in b)) + 1
    w = max(max(c for _,c in a), max(c for _,c in b)) + 1
    if key == 1:
        occ = {(r,c) for r in range(h) for c in range(w)} - {(h-1,w-1)}
    elif key == 2:
        occ = {(r,c) for r in range(h-1) for c in range(w-1)}
    else:
        occ = {(h-1,c) for c in range(w-1)} | {(r,w-1) for r in range(h-1)}
    r0=min(r for r,_ in occ); c0=min(c for _,c in occ)
    r1=max(r for r,_ in occ); c1=max(c for _,c in occ)
    return [[8 if (r,c) in occ else 0 for c in range(c0,c1+1)] for r in range(r0,r1+1)]


def main():
    gen, source, sha = load_selected_generator(TASK_ID, root=ROOT)
    records=[]
    grids=[]
    bands=["easy","medium","hard"]
    for i in range(63):
        band=bands[i%3]
        seed=20261012+i*7919
        index=i*17+5
        grid=gen.generate(seed,index,difficulty=band)
        records.append({"kind":"generated","seed":seed,"sample_index":index,"difficulty":band,"self_check":gen.self_check(grid),"template_family":template_family(grid),"shortcut_output":shortcut(grid)})
        grids.append(grid)
    pair=canonical_pairs(TASK_ID,root=ROOT,labeled_only=True)[1]
    grid=pair["input"]
    records.append({"kind":"canonical_train_1","self_check":gen.self_check(grid),"template_family":template_family(grid),"shortcut_output":shortcut(grid),"canonical_expected":pair["output"]})
    grids.append(grid)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"input.json").write_text(json.dumps(grids,indent=2)+"\n")
    meta={"task_id":TASK_ID,"generator_path":str(source.relative_to(ROOT)),"generator_sha256":sha,"rule_hash_expected":"2727d30f719d","records":records}
    (OUT/"probe_meta.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"inputs":len(grids),"generated_template_family":sum(r["template_family"] for r in records[:-1]),"generated_self_check_pass":sum(not r["self_check"] for r in records[:-1]),"canonical_template_family":records[-1]["template_family"],"canonical_self_check":records[-1]["self_check"],"generator_sha256":sha},sort_keys=True))

if __name__ == "__main__":
    main()
