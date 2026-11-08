#!/usr/bin/env python3
from __future__ import annotations
from copy import deepcopy
import hashlib, json
from pathlib import Path
import importlib.util

TASK='bb435f29015f'
BANDS=('easy','medium','hard')
PER_BAND=100

def seed_for(band: str, i: int) -> int:
    return int(hashlib.sha256(f'audit-cyclic:v1:{TASK}:{band}:{i}'.encode()).hexdigest()[:8],16)

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

generator_path=Path('generators')/TASK/'generator.py'
spec=importlib.util.spec_from_file_location(f'audit_target_{TASK}', generator_path)
if spec is None or spec.loader is None: raise ImportError(generator_path)
gen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
competitors=getattr(gen,'LESSON_COMPETITORS',{})
examples=int(getattr(gen,'EXAMPLES_NEEDED',4))
rows=[]; errors=[]; total=ambiguous=0; unique=set()
for band in BANDS:
  for li in range(PER_BAND):
    seed=seed_for(band,li)
    pairs=[]; sample_indices=[]; profiles=[]; hashes=[]
    try:
      for off in range(examples+1):
        si=li+off
        grid=gen.generate(seed,si,difficulty=band)
        findings=gen.self_check(grid)
        if findings: raise ValueError(f'self_check sample={si}: {findings}')
        output=gen.rule_mirror(deepcopy(grid))
        pairs.append({'input':grid,'output':output})
        sample_indices.append(si)
        profiles.append(gen.schedule_profile(seed,si,difficulty=band))
        h=digest(grid); hashes.append(h); unique.add(h)
    except Exception as exc:
      errors.append({'band':band,'lesson_index':li,'seed':seed,'error':f'{type(exc).__name__}: {exc}'})
      continue
    row={'band':band,'lesson_index':li,'seed':seed,'sample_indices':sample_indices,'profiles':profiles,'input_sha256':hashes,'ambiguous_rotations':[]}
    for qi,query in enumerate(pairs):
      total+=1
      demos=[p for j,p in enumerate(pairs) if j!=qi]
      survivors=[]; rotation_errors=[]
      for name,fn in sorted(competitors.items()):
        try:
          fits=all(fn(deepcopy(d['input']))==d['output'] for d in demos)
          if fits:
            survivors.append({'name':name,'agrees_with_query':fn(deepcopy(query['input']))==query['output']})
        except Exception as exc:
          rotation_errors.append(f'{name}: {type(exc).__name__}: {exc}')
      hook=[]
      try:
        hook=list(gen.lesson_identifiable(deepcopy(demos),deepcopy(query)))
      except Exception as exc:
        rotation_errors.append(f'lesson_identifiable: {type(exc).__name__}: {exc}')
      if survivors or hook or rotation_errors:
        ambiguous += 1
        row['ambiguous_rotations'].append({'query_index':qi,'query_sample_index':sample_indices[qi],'survivors':survivors,'hook_reasons':hook,'errors':rotation_errors})
    if row['ambiguous_rotations']:
      rows.append(row)
status='error' if errors else ('ambiguous' if ambiguous else 'pass')
report={
 'schema':'arcpuzzles-audit-cyclic-probe-v1','status':status,'task_id':TASK,
 'generator_sha256':hashlib.sha256(Path('generators/'+TASK+'/generator.py').read_bytes()).hexdigest(),
 'rule_hash':getattr(gen,'RULE_HASH',None),'seed_recipe':"sha256('audit-cyclic:v1:TASK:BAND:INDEX')[:8]",
 'sampler':{'bands':list(BANDS),'per_band':PER_BAND,'pairs_per_lesson':examples+1,'query_rotations_per_lesson':examples+1,'sample_index_recipe':'lesson_index + offset','oracle':'generator.rule_mirror (Racket parity covered by audit battery)'},
 'competitors':sorted(competitors),'counts':{'lessons':len(BANDS)*PER_BAND,'rotations':total,'ambiguous_rotations':ambiguous,'errors':len(errors),'unique_inputs':len(unique)},
 'errors':errors,'ambiguous_lessons':rows,
 'limits':['Finite check over declared rivals, not proof against undeclared shortcuts.']}
out=Path('../checks/audit/'+TASK+'/cyclic_probe.json')
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(f'status={status} rotations={total} ambiguous={ambiguous} errors={len(errors)}')
raise SystemExit(2 if errors else 1 if ambiguous else 0)
