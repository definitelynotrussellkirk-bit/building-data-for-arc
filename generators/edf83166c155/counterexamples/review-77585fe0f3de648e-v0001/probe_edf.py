from __future__ import annotations
import collections
import importlib.util
import json
from pathlib import Path

PATH=Path('generators/edf83166c155/generator.py')
spec=importlib.util.spec_from_file_location('audit_edf',PATH)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def region_of(component,height,width):
    regions=g._quadrants(height,width)
    hits=[]
    for name,(r0,r1,c0,c1) in regions.items():
        if all(r0<=r<r1 and c0<=c<c1 for r,c in component['cells']):
            hits.append(name)
    if len(hits)!=1:
        raise ValueError((component['cells'],regions,hits))
    return hits[0]

def scaffold_rival_component(grid):
    a=g._analysis(grid)
    if a['errors']: raise ValueError(a['errors'])
    by_region={region_of(c,a['height'],a['width']):c for c in a['components']}
    tl=by_region['tl']
    if tl['bbox_w'] >= 4:
        return by_region['br']
    if 'tr' in by_region:
        return by_region['tr']
    return by_region['bl']

def rival_output(grid):
    return g._crop_component(grid,scaffold_rival_component(grid))

counts=collections.Counter(); first_mismatch=None; quadrants=collections.Counter()
for band in [None,'easy','medium','hard']:
  for seed in range(100):
    for idx in range(20):
      try: grid=g.generate(seed,idx,difficulty=band)
      except Exception as exc:
        counts['generation_error']+=1
        if first_mismatch is None: first_mismatch={'kind':'generation_error','band':band,'seed':seed,'sample_index':idx,'error':repr(exc)}
        continue
      counts['samples']+=1
      a=g._analysis(grid)
      tq=region_of(a['target'],a['height'],a['width']); quadrants[tq]+=1
      actual=g.rule_mirror(grid); rival=rival_output(grid)
      if rival==actual: counts['rival_matches']+=1
      else:
        counts['rival_mismatches']+=1
        if first_mismatch is None:
          first_mismatch={'kind':'rival_mismatch','band':band,'seed':seed,'sample_index':idx,'input':grid,'target_region':tq,'rival_region':region_of(scaffold_rival_component(grid),a['height'],a['width'])}

# Lawful counterexample outside the scheduled scene scaffolds: put the true U target in TL.
grid=[[0]*12 for _ in range(10)]
for dr,dc in g._U_TARGET: grid[1+dr][1+dc]=2
for dr,dc in g._L4_TALL: grid[1+dr][8+dc]=5
for dr,dc in g._J4_WIDE: grid[7+dr][8+dc]=7
counter={
 'input':grid,
 'self_check':g.self_check(grid),
 'true_output':g.rule_mirror(grid),
 'rival_output':rival_output(grid),
 'target_region':region_of(g._analysis(grid)['target'],10,12),
 'rival_region':region_of(scaffold_rival_component(grid),10,12),
}
result={'task_id':'edf83166c155','domain':{'bands':['default','easy','medium','hard'],'seeds':'0..99','sample_indices':'0..19'},'rival':'If TL object bbox width >=4 choose BR; otherwise choose TR when present, else BL. Never tests LR symmetry.','counts':dict(counts),'target_quadrants':dict(quadrants),'first_mismatch':first_mismatch,'lawful_counterexample':counter}
print(json.dumps(result,indent=2))
