from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK='b19deac47327'
path=Path('generators')/TASK/'generator.py'
spec=importlib.util.spec_from_file_location(f'audit_{TASK}', path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
grid=mod.generate(0,0,difficulty='easy',grid_h=18)
result={
  'task_id': TASK,
  'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
  'declared_rule_hash': getattr(mod,'RULE_HASH',None),
  'current_rule_hash_from_defect_lint': '2b2e46dd36cc',
  'seed':0,
  'sample_index':0,
  'difficulty':'easy',
  'overrides':{'grid_h':18},
  'observed_grid_h':len(grid),
  'observed_grid_w':len(grid[0]),
  'self_check':mod.self_check(grid),
  'input':grid,
  'finding':'advertised exact grid_h override is accepted but ignored',
  'command': ['python3','run_with_racket.py','python3','../checks/audit/b19deac47327/probe.py'],
  'cwd':'packet_root',
}
print(json.dumps(result, indent=2))
