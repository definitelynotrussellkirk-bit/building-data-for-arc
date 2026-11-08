from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
TASK = 'b45771715d10'
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_b457', SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()

requested = {'code1': 1, 'code2': 1}
exact = module.generate(0, 0, **requested)
default = module.generate(0, 0)
unknown = module.generate(0, 0, definitely_unknown=37)
obs = {
    'schema': 'review-audit-observation-v1',
    'task_id': TASK,
    'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'recipe': {'seed': 0, 'sample_index': 0, 'difficulty': None, 'overrides': requested},
    'requested_codes': [1, 1],
    'observed_codes': exact[0][:2],
    'self_check': module.self_check(exact),
    'unknown_override_accepted': True,
    'unknown_override_byte_identical_to_default': unknown == default,
    'input_sha256': grid_hash(exact),
    'finding': 'advertised exact code1/code2 overrides are not consumed; unknown keys are silently ignored',
}
out = Path(__file__).resolve().parent
(out / 'input.json').write_text(json.dumps(exact, indent=2) + '\n')
(out / 'observation.json').write_text(json.dumps(obs, indent=2) + '\n')
print(json.dumps(obs, indent=2))
