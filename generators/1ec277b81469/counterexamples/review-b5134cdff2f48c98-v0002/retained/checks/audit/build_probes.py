from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'repo'


def load(task):
    p=REPO/'generators'/task/'generator.py'
    spec=importlib.util.spec_from_file_location(f'audit_{task}',p)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod,p

# Audit 1: an advertised override is inert, and a named degenerate contradicts self_check.
task='1ec277b81469'
mod,p=load(task)
seed=20261005
sample_index=0
g=mod.generate(seed,sample_index,difficulty='medium',n_distinct_colors=1)
colors=sorted({v for row in g for v in row if v!=0})
deg=mod.generate(seed,sample_index,difficulty='medium',texture='no_active_rows')
record={
  'schema':'arcpuzzles-audit-generator-contract-v1',
  'task_id':task,
  'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
  'seed':seed,'sample_index':sample_index,'difficulty':'medium',
  'probe_1':{
    'override':{'n_distinct_colors':1},
    'observed_nonzero_colors':colors,
    'observed_count':len(colors),
    'grid':g,
    'finding':'advertised n_distinct_colors=1 is not honored' if len(colors)!=1 else 'not reproduced',
  },
  'probe_2':{
    'override':{'texture':'no_active_rows'},
    'grid':deg,
    'self_check':mod.self_check(deg,difficulty='medium',meta=None),
    'finding':'named degenerate emitted by generate fails self_check',
  },
}
out=ROOT/'checks'/'audit'/task/'contract-probes.json'
out.write_text(json.dumps(record,indent=2)+'\n')
print(out)

# Audit 2: count of separated gray markers (3) differs from their horizontal span (5).
task='12b35b7402b6'
mod,p=load(task)
grid=[[0]*12 for _ in range(9)]
for c in (0,2,4): grid[0][c]=5
# Unique size-3 L component.
for r,c in ((2,1),(3,1),(3,2)): grid[r][c]=1
# Unique size-5 cross component, separated from the first.
for r,c in ((4,8),(5,7),(5,8),(5,9),(6,8)): grid[r][c]=1
errs=mod.self_check(grid,difficulty='medium',meta=None)
assert not errs, errs
adir=ROOT/'checks'/'audit'/task
(adir/'input.json').write_text(json.dumps(grid,indent=2)+'\n')
# Rival: interpret marker horizontal span 0..4 as 5 and recolor the size-5 component.
rival=[row[:] for row in grid]
for r,c in ((4,8),(5,7),(5,8),(5,9),(6,8)): rival[r][c]=2
(adir/'rival.json').write_text(json.dumps({'name':'gray_horizontal_span','output':rival},indent=2)+'\n')
meta={
 'schema':'arcpuzzles-audit-counterexample-local-v1','task_id':task,
 'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'input':grid,'self_check':errs,
 'documented_domain_checks':{
   'background_zero':True,'only_gray_cells_are_top_row':True,
   'gray_marker_count':3,'gray_horizontal_span':5,
   'blue_component_sizes':[3,5],
   'exactly_one_blue_object_matches_marker_count':True,
   'objects_separated_and_below_top':True,
 },
 'intended_claim':'count all gray cells; recolor unique blue component of size 3',
 'rival_claim':'use gray horizontal span; recolor unique blue component of size 5',
}
(adir/'counterexample-local.json').write_text(json.dumps(meta,indent=2)+'\n')
print(adir/'input.json')
