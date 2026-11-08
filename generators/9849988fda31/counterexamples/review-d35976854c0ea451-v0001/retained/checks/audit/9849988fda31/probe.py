from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
TASK = '9849988fda31'
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_984', SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

cases = [
  ('seed', True, lambda v: module.generate(v,0)),
  ('seed', 1.5, lambda v: module.generate(v,0)),
  ('sample_index', -1, lambda v: module.generate(991,v)),
  ('sample_index', '1', lambda v: module.generate(991,v)),
  ('difficulty', '__invalid_difficulty__', lambda v: module.generate(991,0,difficulty=v)),
]
results=[]
for axis,value,call in cases:
  try:
    grid=call(value)
  except (TypeError,ValueError) as exc:
    results.append({'axis':axis,'value':value,'status':'rejected','error':f'{type(exc).__name__}: {exc}'})
  except Exception as exc:
    results.append({'axis':axis,'value':value,'status':'unexpected_exception','error':f'{type(exc).__name__}: {exc}'})
  else:
    results.append({'axis':axis,'value':value,'status':'accepted_invalid_scalar','output_shape':[len(grid),len(grid[0])]})
record={
  'schema':'arcpuzzles-audit-strict-scalar-v1',
  'task_id':TASK,
  'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
  'finding':'generate accepts invalid request scalars',
  'results':results,
  'accepted_invalid_count':sum(r['status']=='accepted_invalid_scalar' for r in results),
}
Path(__file__).with_name('probe.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
raise SystemExit(0 if record['accepted_invalid_count'] else 1)
