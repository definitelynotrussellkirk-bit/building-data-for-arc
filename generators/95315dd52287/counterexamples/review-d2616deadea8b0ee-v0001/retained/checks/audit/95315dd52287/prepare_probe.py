from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / 'repo'
TASK = '95315dd52287'
SOURCE = REPO / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_953', SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

recipes = []
inputs = []
shape_signatures = set()
origins = set()
color_counts = set()
for band_i, band in enumerate(('easy', 'medium', 'hard')):
    for i in range(20):
        seed = 95315000 + band_i * 1000 + i
        grid = module.generate(seed, i, difficulty=band)
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8)]
        r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
        shape_signatures.add(tuple(sorted((r-r0, c-c0) for r, c in cells)))
        origins.add((r0, c0))
        color_counts.add(len({grid[r][c] for r, c in cells}))
        recipes.append({'seed': seed, 'sample_index': i, 'difficulty': band})
        inputs.append(grid)

canonical = None
with (REPO / 'shared/data/canonical/puzzles.jsonl').open() as fh:
    for line in fh:
        row = json.loads(line)
        if row.get('task_id') == TASK:
            canonical = row
            break
assert canonical
pairs = []
for split, entries in [('train', canonical['train']), ('test', [canonical['test']] if isinstance(canonical['test'], dict) else canonical['test'])]:
    for idx, pair in enumerate(entries):
        pairs.append({
            'split': split,
            'index': idx,
            'self_check': module.self_check(pair['input']),
            'input': pair['input'],
            'output': pair['output'],
        })

out = Path(__file__).resolve().parent
(out / 'inputs.json').write_text(json.dumps(inputs, indent=2) + '\n')
pre = {
    'schema': 'review-audit-probe-pre-v1',
    'task_id': TASK,
    'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'sample_count': len(inputs),
    'recipes': recipes,
    'normalized_blob_signatures': [[list(cell) for cell in sig] for sig in sorted(shape_signatures)],
    'blob_origins': [list(x) for x in sorted(origins)],
    'distinct_blob_color_counts': sorted(color_counts),
    'canonical_self_check': [{k:v for k,v in pair.items() if k not in ('input','output')} for pair in pairs],
    'advertised_grid_h_5_result': None,
    'unknown_override_byte_identical': module.generate(0, 0) == module.generate(0, 0, definitely_unknown=9),
}
try:
    module.generate(0, 0, grid_h=5)
    pre['advertised_grid_h_5_result'] = 'accepted'
except Exception as exc:
    pre['advertised_grid_h_5_result'] = {'error_type': type(exc).__name__, 'message': str(exc)}
(out / 'pre_observation.json').write_text(json.dumps(pre, indent=2) + '\n')
(out / 'canonical_pairs.json').write_text(json.dumps(pairs, indent=2) + '\n')
print(json.dumps(pre, indent=2))
