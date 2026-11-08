"""Findings-only audit. Canonical answers are authoring data, not a solve."""
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root

TASK = 'a16cf9241d71'
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / 'repo' / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

def rival(grid):
    """Use palette/border/height correlations to infer axis without reading 8s."""
    cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,8)]
    cmin = min(c for _,c in cells)
    cmax = max(c for _,c in cells)
    color = grid[cells[0][0]][cells[0][1]]
    gap = 0 if cmin == 0 and (len(grid) != 5 or color == 2) else 1
    axis = cmax + 1 + gap
    out = [row[:] for row in grid]
    for r,c in cells:
        mc = 2*axis-c
        if 0 <= mc < len(grid[0]):
            out[r][mc] = grid[r][c]
    return out

cases=[]
for band in ('easy','medium','hard'):
    for index in range(18):
        grid=gen.generate(7,index,difficulty=band)
        cases.append({'kind':'ordinary','seed':7,'sample_index':index,'difficulty':band,'overrides':{},'input':grid,'validator_errors':gen.self_check(grid),'rival_output':rival(grid)})
canonical=canonical_pairs(TASK,root=find_root(SOURCE))
for p in canonical:
    cases.append({'kind':'canonical','input':p['input'],'canonical_output':p['output'],'validator_errors':gen.self_check(p['input']),'rival_output':rival(p['input'])})
overrides={'grid_h':5,'grid_w':7,'shape_idx':0,'shape_color':4,'axis_gap':0,'vertical_profile':'middle'}
grid=gen.generate(7,0,difficulty='medium',**overrides)
cases.append({'kind':'generated_override_witness','seed':7,'sample_index':0,'difficulty':'medium','overrides':overrides,'input':grid,'validator_errors':gen.self_check(grid),'observed_overrides':gen.observe_overrides(grid),'rival_output':rival(grid)})
report={'task_id':TASK,'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'description':'Undeclared rival infers axis from source color, source touching left edge, and height; never locates the cyan axis.','cases':cases}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'input.json').write_text(json.dumps([c['input'] for c in cases],indent=2)+'\n')
(OUT/'rival.json').write_text(json.dumps([c['rival_output'] for c in cases],indent=2)+'\n')
print(json.dumps({'cases':len(cases),'ordinary':54,'canonical':len(canonical),'validator_failures':sum(bool(c['validator_errors']) for c in cases),'generator_sha256':report['generator_sha256']}))
