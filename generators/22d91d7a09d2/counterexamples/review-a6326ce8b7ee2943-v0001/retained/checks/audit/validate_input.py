from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('task_id')
p.add_argument('--input', required=True, type=Path)
p.add_argument('--out', required=True, type=Path)
a=p.parse_args()
gen_path=Path('generators')/a.task_id/'generator.py'
spec=importlib.util.spec_from_file_location(f'audit_{a.task_id}', gen_path)
assert spec and spec.loader
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
payload=json.loads(a.input.read_text())
grid=payload.get('input', payload)
errors=m.self_check(grid)
report={
  'task_id':a.task_id,
  'generator_path':str(gen_path),
  'generator_sha256':hashlib.sha256(gen_path.read_bytes()).hexdigest(),
  'input_path':str(a.input),
  'self_check_errors':errors,
  'validator_accepted':not errors,
}
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
