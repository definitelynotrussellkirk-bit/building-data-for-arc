#!/usr/bin/env python3
"""Focused findings-only probe; run from packet root. No reference runner imports."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib, importlib.util, json
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'repo/shared/runtime'))
SOURCE = ROOT / 'repo/generators/5955ced85d5c/generator.py'
spec=importlib.util.spec_from_file_location('audited_generator',SOURCE)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
def dump(name,value):
 (OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def feature(grid):
 reds=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==2]
 mains=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,2)]
 horizontal=len({r for r,c in reds})==1
 axis=0 if horizontal else 1
 red_coord=reds[0][axis]
 coords=[p[axis] for p in mains]
 return {'shape':[len(grid),len(grid[0])], 'orientation':'horizontal' if horizontal else 'vertical', 'fold_distance':min(abs(red_coord-v) for v in coords), 'main_side':'before' if max(coords)<red_coord else 'after', 'foreground_touches_border':any(r in (0,len(grid)-1) or c in (0,len(grid[0])-1) for r,c in reds+mains)}
canonical=next(json.loads(line) for line in (ROOT/'repo/shared/data/canonical/puzzles.jsonl').open() if json.loads(line).get('task_id')==g.TASK_ID)
records=[]
for band in ['easy','medium','hard']:
 for seed in range(4):
  for index in range(5):
   grid=g.generate(seed,index,difficulty=band)
   records.append({'seed':seed,'sample_index':index,'difficulty':band,'overrides':{},'input':grid,'self_check':g.self_check(grid,difficulty=band),'features':feature(grid),'domain_membership':'actual ordinary generate() output'})
controls=[]
for override in [{},{'grid_h':9,'grid_w':11},{'grid_h':18,'grid_w':18},{'fold_distance':2},{'fold_distance':4},{'anchor_corner':True}]:
 grid=g.generate(0,0,difficulty='easy',**override)
 controls.append({'seed':0,'sample_index':0,'difficulty':'easy','overrides':override,'input':grid,'self_check':g.self_check(grid),'features':feature(grid),'same_as_baseline':grid==records[0]['input'],'domain_membership':'actual generate() output with advertised valid overrides'})
dump('input.json',[r['input'] for r in records]+[p['input'] for p in canonical['train']])
dump('evidence.json',{'task_id':g.TASK_ID,'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'version':g.VERSION,'rule_program_sha256':hashlib.sha256(canonical['program_solution'].encode()).hexdigest(),'records':records,'control_probes':controls,'canonical_train':canonical['train'],'canonical_test':canonical['test'],'canonical_features':[feature(p['input']) for p in canonical['train']+canonical['test']],'declared_CANONICAL_SHORTCUTS':getattr(g,'CANONICAL_SHORTCUTS',None),'declared_LESSON_COMPETITORS':getattr(g,'LESSON_COMPETITORS',None)})
print(json.dumps({'sample_count':len(records),'validator_failures':sum(bool(r['self_check']) for r in records),'main_sides':sorted({r['features']['main_side'] for r in records}),'controls':[{k:v for k,v in r.items() if k!='input'} for r in controls]},indent=2))
