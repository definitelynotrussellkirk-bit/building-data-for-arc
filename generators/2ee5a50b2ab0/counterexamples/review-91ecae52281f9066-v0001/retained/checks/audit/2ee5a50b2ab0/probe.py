from __future__ import annotations
import copy, hashlib, importlib.util, json
from pathlib import Path

TASK_ID='2ee5a50b2ab0'
ROOT=Path.cwd(); SOURCE=ROOT/'generators'/TASK_ID/'generator.py'; OUT=ROOT.parent/'checks'/'audit'/TASK_ID
spec=importlib.util.spec_from_file_location('audit_2ee_generator',SOURCE); assert spec and spec.loader
G=importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

def horizontal_color(grid):
    for color,cells in G._components(grid):
        if len({r for r,_ in cells})==1 and len(cells)>=2:
            return color
    raise AssertionError('no horizontal line')

def vertical_only(grid):
    out=copy.deepcopy(grid)
    for color,cells in G._components(grid):
        rs=sorted({r for r,_ in cells}); cs=sorted({c for _,c in cells})
        if len(cs)==1 and len(cells)>=2:
            out[min(rs)][cs[0]]=8; out[max(rs)][cs[0]]=8
    return out

selected=None
for seed in range(20000):
    grids=[G.generate(seed,i,difficulty='easy') for i in range(4)]
    colors=[horizontal_color(g) for g in grids]
    if colors[:3]==[8,8,8] and colors[3]!=8:
        selected=(seed,grids,colors); break
if selected is None: raise SystemExit('no witness in search range')
seed,grids,colors=selected
report={
 'schema':'audit-2ee5a50b2ab0-horizontal-shortcut-v1','task_id':TASK_ID,
 'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'generator_version':G.VERSION,
 'search':{'seed_start':0,'seed_stop_exclusive':20000,'difficulty':'easy','sample_indices':[0,1,2,3]},
 'selected':{'seed':seed,'horizontal_colors':colors,'demo_indices':[0,1,2],'query_index':3},
 'inputs':grids,
 'self_check_errors':[G.self_check(g,difficulty='easy') for g in grids],
 'rival':'mark endpoints of vertical lines only',
 'rival_outputs':[vertical_only(g) for g in grids],
 'claim':'The rival fits all three demos when their only horizontal line is already color 8, but differs on the query whose horizontal line has another color.',
}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'input.json').write_text(json.dumps(grids,indent=2)+'\n')
(OUT/'probe-pre-racket.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'seed':seed,'horizontal_colors':colors,'self_checks':report['self_check_errors']}))
