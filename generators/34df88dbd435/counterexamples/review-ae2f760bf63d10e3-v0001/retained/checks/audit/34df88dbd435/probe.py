from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
REPO = PACKET / 'repo'
GEN_PATH = REPO / 'generators/34df88dbd435/generator.py'
spec = importlib.util.spec_from_file_location('audit_34df88dbd435', GEN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

grid = module.generate(0, 0, difficulty='medium', texture='all_tall')
errors = module.self_check(grid)
out = Path(__file__).resolve().parent
(out / 'input.json').write_text(json.dumps(grid, indent=2) + '\n')
record = {
    'task_id': '34df88dbd435',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'seed': 0,
    'sample_index': 0,
    'difficulty': 'medium',
    'overrides': {'texture': 'all_tall'},
    'axis_declared_valid': 'all_tall' in str(module.AXES['texture']['valid']).split('|'),
    'self_check_errors': errors,
    'shape': [len(grid), len(grid[0])],
    'colors': sorted({v for row in grid for v in row}),
}
(out / 'probe.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
