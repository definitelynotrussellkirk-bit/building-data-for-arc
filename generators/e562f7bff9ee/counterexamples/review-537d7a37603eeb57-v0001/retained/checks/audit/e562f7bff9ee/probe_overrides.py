from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] / 'repo'
sys.path.insert(0, str(ROOT / 'shared' / 'runtime'))
PATH = ROOT / 'generators' / 'e562f7bff9ee' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_e562', PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

report = {
    'task_id': 'e562f7bff9ee',
    'generator_sha256': hashlib.sha256(PATH.read_bytes()).hexdigest(),
    'declared_axes': module.AXES,
    'cases': [],
}

def run(label, **kwargs):
    row = {'label': label, 'kwargs': kwargs}
    try:
        grid = module.generate(0, 0, **kwargs)
    except Exception as exc:
        row.update({'status': 'raised', 'exception': type(exc).__name__, 'message': str(exc)})
    else:
        row.update({
            'status': 'returned',
            'shape': [len(grid), len(grid[0])],
            'satellite_count': sum(v in (8, 9) for line in grid for v in line),
            'self_check': module.self_check(grid),
        })
    report['cases'].append(row)

run('advertised grid_h=24 in hard', difficulty='hard', grid_h=24)
run('advertised n_satellites=1 in easy', difficulty='easy', n_satellites=1)
run('unknown key', difficulty='medium', typo_axis=123)

for seed in range(1000):
    try:
        grid = module.generate(seed, 0, difficulty='hard', n_satellites=7)
    except Exception:
        continue
    count = sum(v in (8, 9) for line in grid for v in line)
    if count != 7:
        report['cases'].append({
            'label': 'accepted n_satellites=7 but realized fewer',
            'kwargs': {'seed': seed, 'sample_index': 0, 'difficulty': 'hard', 'n_satellites': 7},
            'status': 'returned',
            'shape': [len(grid), len(grid[0])],
            'satellite_count': count,
            'self_check': module.self_check(grid),
            'input': grid,
        })
        break
else:
    report['cases'].append({'label': 'scan', 'status': 'no mismatch in seeds 0..999'})

print(json.dumps(report, indent=2, sort_keys=True))
