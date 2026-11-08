from __future__ import annotations
import importlib.util, hashlib, json
from pathlib import Path

results = {}

# 5cff: advertised controls that are not consumed by generate().
def load(task_id):
    path = Path('/mnt/data/arcpuzzles_review_035633/repo/generators') / task_id / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + task_id, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

g = load('5cff0d794bdf')
cases = {}
for label, kwargs in {
    'baseline': {},
    'palette_kind_warm': {'palette_kind': 'warm'},
    'palette_kind_cool': {'palette_kind': 'cool'},
    'palette_size_1': {'palette_size': 1},
    'n_distinct_colors_1': {'n_distinct_colors': 1},
    'density_sparse': {'density': 'sparse'},
    'position_bias_column_pairs': {'position_bias': 'column_pairs'},
}.items():
    grid = g.generate(12345, 7, difficulty='medium', **kwargs)
    cases[label] = {
        'kwargs': kwargs,
        'grid': grid,
        'height': len(grid),
        'width': len(grid[0]),
        'colors': sorted({v for row in grid for v in row if v}),
        'sha256': hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest(),
        'self_check': g.self_check(grid, difficulty='medium'),
    }
results['5cff0d794bdf'] = {
    'version': g.VERSION,
    'cases': cases,
    'all_advertised_noop_hashes_equal_baseline': all(
        data['sha256'] == cases['baseline']['sha256']
        for name, data in cases.items() if name != 'baseline'
    ),
}

# 059: measure default four-demo lessons against plausible role shortcuts.
g = load('0591985abf42')

def reflect_all_non_guide(grid):
    # Same geometric operation as the canonical mirror, but reflects both object colors.
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    background = g._mode_reading_order(original)
    guide = g._priority_guide(original, background)
    if guide is None:
        return output
    kind, param, line_color = guide
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if value in (background, line_color):
                continue
            rr, cc = g._mirror_destination(kind, param, r, c)
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                output[rr][cc] = value
    return output

def reflect_first_reading_object_color(grid):
    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    background = g._mode_reading_order(original)
    guide = g._priority_guide(original, background)
    if guide is None:
        return output
    kind, param, line_color = guide
    selected = next((v for row in original for v in row if v not in (background, line_color)), None)
    if selected is None:
        return output
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if value != selected:
                continue
            rr, cc = g._mirror_destination(kind, param, r, c)
            if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                output[rr][cc] = value
    return output

rivals = {
    'reflect_all_object_colors': reflect_all_non_guide,
    'reflect_first_reading_object_color': reflect_first_reading_object_color,
}
ambiguous = {name: [] for name in rivals}
profile_counts = {}
for seed in range(250):
    pairs = []
    for index in range(5):
        grid = g.generate(seed, index, difficulty='medium')
        pairs.append({'input': grid, 'output': g.rule_mirror(grid)})
    for p in pairs[:4]:
        profile = g.observe_overrides(p['input']).get('scene_profile')
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
    for name, rival in rivals.items():
        if all(rival(p['input']) == p['output'] for p in pairs[:4]) and rival(pairs[4]['input']) != pairs[4]['output']:
            ambiguous[name].append(seed)
results['0591985abf42'] = {
    'version': g.VERSION,
    'medium_seed_count': 250,
    'lesson_policy': 'generate(seed, sample_index=0..4); first four demos, fifth query',
    'demo_profile_counts': profile_counts,
    'ambiguous_seed_counts': {name: len(seeds) for name, seeds in ambiguous.items()},
    'first_ambiguous_seeds': {name: seeds[:10] for name, seeds in ambiguous.items()},
}

print(json.dumps(results, indent=2))
