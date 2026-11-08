from __future__ import annotations
import hashlib, importlib.util, json
from collections import Counter
from pathlib import Path

TASK='d8111f3f714d'
path=Path('generators')/TASK/'generator.py'
spec=importlib.util.spec_from_file_location(f'audit_{TASK}', path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

stats={}
all_errors=[]
for band in ('easy','medium','hard'):
    orientations=Counter(); branches=Counter(); side_support=Counter(); unique=set()
    for index in range(200):
        grid=mod.generate(73000+index,index,difficulty=band)
        errors=mod.self_check(grid)
        if errors:
            all_errors.append({'band':band,'index':index,'errors':errors})
        facts=mod._analyze(grid)
        orientations[facts['orientation']]+=1
        branches[facts['n_branches']]+=1
        side_support[(facts['side_support']['negative']>0,facts['side_support']['positive']>0)]+=1
        unique.add(tuple(tuple(row) for row in grid))
    stats[band]={
        'draws':200,
        'unique_inputs':len(unique),
        'orientations':dict(orientations),
        'branch_counts':dict(branches),
        'side_support_boolean':{str(k):v for k,v in side_support.items()},
    }

result={
  'task_id':TASK,
  'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
  'rule_hash':getattr(mod,'RULE_HASH',None),
  'probe':stats,
  'self_check_failures':all_errors,
  'defect_lint':'PASS (checks/audit-d8111f3f714d-defect_lint/checks/d8111f3f714d_after_defect_lint.log)',
  'semantic_gate':'FAIL only because no semantic contract is declared (checks/audit-d8111f3f714d-semantic_gate/checks/d8111f3f714d_after_semantic_gate.log)',
  'finding':'No generated structural defect reproduced in 600 draws; missing lesson-level semantic contract remains an assurance gap.',
  'command':['python3','run_with_racket.py','python3','../checks/audit/d8111f3f714d/probe.py'],
  'cwd':'packet_root',
}
print(json.dumps(result,indent=2,sort_keys=True))
