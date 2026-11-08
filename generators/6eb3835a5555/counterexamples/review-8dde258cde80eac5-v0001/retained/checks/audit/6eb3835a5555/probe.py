from __future__ import annotations
import importlib.util, json, hashlib
from pathlib import Path
from collections import deque

ROOT=Path(__file__).resolve().parents[3]
TASK='6eb3835a5555'
GEN=ROOT/'repo/generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_gen_6e',GEN)
mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)

def regions(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            if grid[r][c]==5 or (r,c) in seen: continue
            q=[(r,c)]; seen.add((r,c)); cells=[]
            while q:
                x,y=q.pop(); cells.append((x,y))
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx,ny=x+dx,y+dy
                    if 0<=nx<h and 0<=ny<w and grid[nx][ny]!=5 and (nx,ny) not in seen:
                        seen.add((nx,ny)); q.append((nx,ny))
            out.append(cells)
    return out

def first_seed_fill(grid):
    out=[row[:] for row in grid]
    for room in regions(grid):
        seeds=[grid[r][c] for r,c in room if grid[r][c] not in (0,5)]
        if not seeds: continue
        color=seeds[0]
        for r,c in room:
            if out[r][c]==0: out[r][c]=color
    return out

# A default sample that falsifies advertised exact axes/invariants.
default=None
for seed in range(1000):
    g=mod.generate(seed,0,difficulty='medium')
    room_list=regions(g)
    seed_colors=[next((g[r][c] for r,c in room if g[r][c] not in (0,5)),None) for room in room_list]
    if (len(g),len(g[0]),len(room_list)) != (7,9,4) or len(set(seed_colors)) < len(seed_colors):
        default=(seed,g,seed_colors,len(room_list)); break
assert default
seed,g,seed_colors,n_rooms=default

# Declared degenerate accepted by self_check; intended rule and first-seed rival disagree.
ambiguous=mod.generate(0,0,difficulty='medium',texture='multiple_colors_per_chamber')
assert mod.self_check(ambiguous)==[]
rival=first_seed_fill(ambiguous)
base={
 'schema':'arc-generator-audit-probe-v1',
 'task_id':TASK,
 'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
 'default_counterexample':{
   'seed':seed,'sample_index':0,'difficulty':'medium','input_grid':g,
   'observed':{'grid_h':len(g),'grid_w':len(g[0]),'n_chambers':n_rooms,'seed_colors':seed_colors,'n_distinct_colors':len(set(seed_colors))},
   'advertised':{'grid_h':'7..7','grid_w':'9..9','n_chambers':'4..4','n_distinct_colors':'4..4'},
   'self_check':mod.self_check(g),
 },
 'ambiguous_room_counterexample':{
   'seed':0,'sample_index':0,'difficulty':'medium','overrides':{'texture':'multiple_colors_per_chamber'},
   'input_grid':ambiguous,'self_check':mod.self_check(ambiguous),
   'rival':'fill every non-wall region using its first nonzero seed, even when multiple distinct colors occur',
   'rival_output':rival,
 },
 'command':['python3','checks/audit/6eb3835a5555/probe.py'],
 'cwd':'packet_root',
}
Path(__file__).with_name('probe.json').write_text(json.dumps(base,indent=2)+'\n')
Path(__file__).with_name('input.json').write_text(json.dumps(ambiguous)+'\n')
Path(__file__).with_name('rival_output.json').write_text(json.dumps(rival)+'\n')
print(json.dumps({'default_seed':seed,'observed':base['default_counterexample']['observed'],'ambiguous_self_check':base['ambiguous_room_counterexample']['self_check'],'generator_sha256':base['generator_sha256']},indent=2))
