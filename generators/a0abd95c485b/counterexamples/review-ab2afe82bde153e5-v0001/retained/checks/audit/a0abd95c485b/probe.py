from __future__ import annotations
import importlib.util, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PATH=ROOT/'repo/generators/a0abd95c485b/generator.py'
spec=importlib.util.spec_from_file_location('ga0',PATH)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

grid=[
 [0,0,0,0,0,0,0,0,0,0],
 [0,4,4,0,0,4,4,0,0,0],
 [0,0,0,0,0,0,0,0,0,0],
 [0,0,4,4,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0,0,0,0],
]

def first_pair_per_row(grid):
    out=[row[:] for row in grid]
    h,w=len(grid),len(grid[0])
    for r in range(h):
        for c in range(w-1):
            if grid[r][c]==4 and grid[r][c+1]==4:
                if c-1>=0 and grid[r][c-1]==0: out[r][c-1]=9
                if c+2<w and grid[r][c+2]==0: out[r][c+2]=9
                break
    return out

out={
 'task_id':'a0abd95c485b',
 'generator_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'input':grid,
 'self_check':g.self_check(grid),
 'rival_name':'flank only the first horizontal 44 pair in each row',
 'rival_output':first_pair_per_row(grid),
 'reason':'Canonical and default generated inputs place at most one pair per row, so the rival fits them; this lawful validator input has two pairs in one row.',
}
Path(__file__).with_name('probe.json').write_text(json.dumps(out,indent=2)+'\n')
Path(__file__).with_name('input.json').write_text(json.dumps(grid)+'\n')
Path(__file__).with_name('rival_output.json').write_text(json.dumps(out['rival_output'],indent=2)+'\n')
print(json.dumps(out,indent=2))
