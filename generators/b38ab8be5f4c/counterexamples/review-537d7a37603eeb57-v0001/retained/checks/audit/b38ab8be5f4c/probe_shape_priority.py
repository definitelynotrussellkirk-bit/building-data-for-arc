from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3] / 'repo'
sys.path.insert(0, str(ROOT / 'shared' / 'runtime'))
GEN_PATH = ROOT / 'generators' / 'b38ab8be5f4c' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_b38', GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gen)

DIR4 = ((-1,0),(1,0),(0,-1),(0,1))
SHAPES = {
    'tee4': ((0,0),(0,1),(0,2),(1,1)),
    'c5': ((0,0),(0,1),(0,2),(1,0),(1,2)),
    'p5': ((0,0),(0,1),(1,0),(1,1),(2,0)),
    'stair5': ((0,0),(1,0),(1,1),(2,1),(2,2)),
    'ring8': ((0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)),
}
# This order alone identifies every generated/canonical target.
PRIORITY = ('ring8','stair5','p5','c5','tee4')


def normalize(cells):
    r0=min(r for r,c in cells); c0=min(c for r,c in cells)
    return tuple(sorted((r-r0,c-c0) for r,c in cells))


def objects(grid):
    colors=sorted({v for row in grid[1:] for v in row if v})
    out=[]
    for color in colors:
        cells={(r,c) for r in range(1,len(grid)) for c,v in enumerate(grid[r]) if v==color}
        # The documented grammar has exactly one component per body color.
        start=next(iter(cells)); seen={start}; stack=[start]
        while stack:
            r,c=stack.pop()
            for dr,dc in DIR4:
                p=(r+dr,c+dc)
                if p in cells and p not in seen:
                    seen.add(p); stack.append(p)
        shape=next((name for name,pat in SHAPES.items() if normalize(seen)==pat),None)
        out.append((color, seen, shape))
    return out


def raw_crop(grid,cells):
    r1=min(r for r,c in cells); r2=max(r for r,c in cells)
    c1=min(c for r,c in cells); c2=max(c for r,c in cells)
    return [row[c1:c2+1] for row in grid[r1:r2+1]]


def rival(grid):
    ranked=[]
    for color,cells,shape in objects(grid):
        if shape in PRIORITY:
            ranked.append((PRIORITY.index(shape), color, cells, shape))
    if not ranked:
        raise ValueError('no priority morphology')
    _,_,cells,_=min(ranked)
    return raw_crop(grid,cells)


def canonical_pairs():
    for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
        task=json.loads(line)
        if task['task_id']=='b38ab8be5f4c':
            return [*task['train'],task['test']]
    raise RuntimeError('canonical task not found')

canon=canonical_pairs()
canon_fit=[rival(p['input'])==p['output'] for p in canon]
default_checked=0
default_fit=0
for band in ('easy','medium','hard'):
    for seed in range(20):
        for index in range(12):
            grid=gen.generate(seed,index,difficulty=band)
            default_checked+=1
            default_fit += rival(grid)==gen.rule_mirror(grid)

# Build a lawful scene containing both stair5 and c5, then switch only the
# top-row marker to the c5 color. The intended rule follows the marker; the
# shape-priority rival still selects stair5.
base=gen.generate(17,0,difficulty='medium',target_shape='stair5',bbox_intruder=False)
scene=[row[:] for row in base]
body=objects(scene)
c5_color=next(color for color,cells,shape in body if shape=='c5')
marker_col=next(c for c,v in enumerate(scene[0]) if v)
scene[0][marker_col]=c5_color
intended=gen.rule_mirror(scene)
rival_out=rival(scene)

report={
    'task_id':'b38ab8be5f4c',
    'generator_sha256':hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'rule_hash':gen.RULE_HASH,
    'rival':'ignore the marker; crop the highest-priority body morphology ring8 > stair5 > p5 > c5 > tee4',
    'canonical_fit':canon_fit,
    'canonical_fit_count':sum(canon_fit),
    'canonical_total':len(canon_fit),
    'default_fit_count':default_fit,
    'default_total':default_checked,
    'counterexample':{
        'construction':{'seed':17,'sample_index':0,'difficulty':'medium','overrides':{'target_shape':'stair5','bbox_intruder':False},'mutation':'replace the sole top-row marker color with the c5 distractor color'},
        'self_check':gen.self_check(scene),
        'input':scene,
        'python_mirror_output':intended,
        'shape_priority_output':rival_out,
        'disagrees':intended!=rival_out,
    },
}
(HERE.parent/'input.json').write_text(json.dumps(scene,indent=2)+'\n')
(HERE.parent/'rival-output.json').write_text(json.dumps(rival_out,indent=2)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
