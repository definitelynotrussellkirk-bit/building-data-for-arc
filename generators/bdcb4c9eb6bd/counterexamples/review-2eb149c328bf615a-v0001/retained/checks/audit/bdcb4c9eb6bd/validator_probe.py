import hashlib, importlib.util, json
from pathlib import Path
TASK='bdcb4c9eb6bd'
source=Path('generators')/TASK/'generator.py'
spec=importlib.util.spec_from_file_location(f'audit_{TASK}', source)
assert spec and spec.loader
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
root=Path('../checks/audit')/TASK
grid=json.loads((root/'input.json').read_text())
probe={
 'task_id':TASK,
 'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'validator_errors':g.self_check(grid),
 'input_shape':[len(grid),len(grid[0])],
}
(root/'validator.json').write_text(json.dumps(probe,indent=2,sort_keys=True)+'\n')
print(json.dumps(probe,sort_keys=True))
