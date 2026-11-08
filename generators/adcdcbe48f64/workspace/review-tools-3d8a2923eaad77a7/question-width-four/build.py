from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'repo'
TASK='adcdcbe48f64'
SOURCE=REPO/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('question_generator',SOURCE)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def rival(grid):
    return [row[:4]+row[:4][::-1]+row[:4]+row[:4][::-1]+row[:4] for row in grid]

# Exact noncanonical width emitted through the advertised override contract.
grid=mod.generate(2026,7,difficulty='medium',grid_h=4,grid_w=5,palette_size=2)
assert mod.self_check(grid)==[]
assert len(grid)==4 and len(grid[0])==5
outdir=Path(__file__).resolve().parent
(outdir/'input.json').write_text(json.dumps(grid,indent=2)+'\n')
(outdir/'rival.json').write_text(json.dumps(rival(grid),indent=2)+'\n')

canonical=[]
for line in (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
    obj=json.loads(line)
    if obj.get('task_id')==TASK:
        canonical.extend(obj.get('train',[])); canonical.extend(obj.get('test',[]))

def pair_input(pair): return pair['input'] if isinstance(pair,dict) else pair[0]
def pair_output(pair): return pair['output'] if isinstance(pair,dict) else pair[1]
assert all(rival(pair_input(p))==pair_output(p) for p in canonical)
(outdir/'probe.json').write_text(json.dumps({
    'task_id':TASK,
    'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'canonical_pair_occurrences':len(canonical),
    'canonical_matches':sum(rival(pair_input(p))==pair_output(p) for p in canonical),
    'recipe':{'seed':2026,'sample_index':7,'difficulty':'medium','overrides':{'grid_h':4,'grid_w':5,'palette_size':2}},
    'self_check':mod.self_check(grid),
    'observed_overrides':mod.observe_overrides(grid),
    'input':grid,
    'rival_output':rival(grid),
},indent=2,sort_keys=True)+'\n')
