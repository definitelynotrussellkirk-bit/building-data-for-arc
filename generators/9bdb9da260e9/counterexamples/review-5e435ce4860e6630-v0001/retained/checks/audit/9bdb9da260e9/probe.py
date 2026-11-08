from __future__ import annotations
import hashlib, importlib.util, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))
path = REPO / 'generators' / '9bdb9da260e9' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_9bdb9da260e9', path)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
grid = mod.generate(0, 0, texture='missing_match')
input_path = pathlib.Path(__file__).with_name('missing_match_input.json')
input_path.write_text(json.dumps({'input': grid}, separators=(',', ':')) + '\n')
report = {
    'task_id': '9bdb9da260e9',
    'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'override': {'texture': 'missing_match'},
    'self_check': mod.self_check(grid),
    'shape': [len(grid), len(grid[0])],
    'colors': sorted({v for row in grid for v in row}),
    'input_path': str(input_path.relative_to(ROOT)),
}
pathlib.Path(__file__).with_name('probe.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
