from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
REPO = ROOT / 'WORK' / 'repo'
TASK = '1d2e86233750'
GEN_PATH = REPO / 'generators' / TASK / 'generator.py'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))
spec = importlib.util.spec_from_file_location('audit_1d2_current', GEN_PATH)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)

def sha_bytes(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rotate_cw(g):
    return [list(row) for row in zip(*g[::-1])]

def rotate_180(g):
    return [row[::-1] for row in g[::-1]]

def flip_lr(g):
    return [row[::-1] for row in g]

def flip_ud(g):
    return [row[:] for row in g[::-1]]
XFORMS = {1: rotate_cw, 2: rotate_180, 3: flip_lr, 4: flip_ud}

def inners(grid):
    boxes = gen._frame_boxes_for_self_check(grid)
    out = []
    for r1,c1,r2,c2,_ in boxes[:3]:
        out.append([row[c1+1:c2] for row in grid[r1+1:r2]])
    return out

seed=1
indices=[12,13,14,15]
inputs=[]
records=[]
for i in indices:
    grid=gen.generate(seed, i, difficulty='medium')
    A,B,C=inners(grid)
    matches=[code for code,fn in XFORMS.items() if fn(A)==B]
    assert len(matches)==1, matches
    inputs.append(grid)
    records.append({
        'sample_index': i,
        'self_check': gen.self_check(grid, difficulty='medium'),
        'transform_code': matches[0],
        'c': C,
        'always_cw_output': rotate_cw(C),
    })

outdir=HERE.parent
(outdir/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
(outdir/'probe-preapply.json').write_text(json.dumps({
    'schema':'audit-1d2-constant-transform-v1',
    'task_id':TASK,
    'generator_sha256':sha_bytes(GEN_PATH),
    'seed':seed,
    'difficulty':'medium',
    'sample_indices':indices,
    'lesson_interpretation':'first 3 pairs are demonstrations; fourth is query',
    'rival':'always rotate panel C clockwise',
    'records':records,
    'domain_limit':'One reachable consecutive production-shaped 3-demo/1-query window; no frequency estimate.',
},indent=2,sort_keys=True)+'\n')
print(json.dumps({'generator_sha256':sha_bytes(GEN_PATH),'transform_codes':[r['transform_code'] for r in records],'self_checks':[r['self_check'] for r in records]},indent=2))
