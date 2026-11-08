from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / 'repo'
GEN_PATH = ROOT / 'generators' / 'fdb8815ba528' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_fdb', GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

sample_count = 0
component_count = 0
observed_spans = set()
mismatches = []
for band in ('easy', 'medium', 'hard'):
    for seed in range(100):
        for sample_index in range(12):
            grid = gen.generate(seed, sample_index, difficulty=band)
            sample_count += 1
            components = gen._components(grid)
            component_count += len(components)
            for component in components:
                r0, c0, r1, c1 = component['bbox']
                observed_spans.add((r1-r0+1, c1-c0+1))
            if gen._legacy_bbox_span_lookup(grid) != gen.rule_mirror(grid):
                mismatches.append({'band': band, 'seed': seed, 'sample_index': sample_index})

# Lawful input with a 3x5 component, a span the source's legacy lookup does not process.
grid = [[0 for _ in range(10)] for _ in range(7)]
shape1 = {(0,0),(0,1),(1,1),(1,2),(1,3),(2,3),(2,4)}
for r,c in shape1:
    grid[1+r][1+c] = 4
shape2 = {(0,0),(0,1),(1,1)}
for r,c in shape2:
    grid[4+r][7+c] = 7

self_errors = gen.self_check(grid)
true_output = gen.rule_mirror(grid)
rival_output = gen._legacy_bbox_span_lookup(grid)
record = {
    'schema': 'arcpuzzles-audit-counterexample-v1',
    'task_id': 'fdb8815ba528',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'shortcut': 'legacy_bbox_span_lookup',
    'shortcut_definition': 'Outline components only when their bbox span is in the hard-coded legacy set; otherwise preserve the source component.',
    'sample_probe': {
        'bands': ['easy','medium','hard'],
        'seeds_per_band': 100,
        'indices_per_seed': 12,
        'samples': sample_count,
        'components': component_count,
        'observed_bbox_spans': sorted([list(x) for x in observed_spans]),
        'legacy_span_set': sorted([list(x) for x in gen._LEGACY_BBOX_SPANS]),
        'rival_mismatches': mismatches,
    },
    'counterexample': {
        'input': grid,
        'self_check_errors': self_errors,
        'rule_mirror_output': true_output,
        'shortcut_output': rival_output,
        'outputs_differ': true_output != rival_output,
        'novel_component_span': [3,5],
    },
}
(HERE / 'legacy_span_shortcut.json').write_text(json.dumps(record, indent=2) + '\n')
(HERE / 'legacy_span_input.json').write_text(json.dumps({'input': grid}, indent=2) + '\n')
print(json.dumps({
    'samples': sample_count,
    'components': component_count,
    'observed_spans': sorted(observed_spans),
    'mismatches': len(mismatches),
    'self_check_errors': self_errors,
    'counterexample_differs': true_output != rival_output,
}, indent=2))
if mismatches or self_errors or true_output == rival_output:
    raise SystemExit(1)
