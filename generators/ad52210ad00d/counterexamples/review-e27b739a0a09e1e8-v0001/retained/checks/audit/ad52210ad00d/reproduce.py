from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
TASK = 'ad52210ad00d'
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_ad522', SOURCE)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def count_seeds(grid):
    return sum(v == 2 for row in grid for v in row)

def capture(fn):
    try:
        return {'accepted': True, 'value': fn()}
    except Exception as exc:
        return {'accepted': False, 'exception': f'{type(exc).__name__}: {exc}'}

anchor_equal = []
anchor_validator_failures = []
for band in (None, 'easy', 'medium', 'hard'):
    for seed in range(25):
        left = mod.generate(seed, seed, difficulty=band, anchor_corner=False)
        right = mod.generate(seed, seed, difficulty=band, anchor_corner=True)
        anchor_equal.append(left == right)
        if hasattr(mod, 'self_check'):
            anchor_validator_failures.extend(mod.self_check(left))
            anchor_validator_failures.extend(mod.self_check(right))

unknown = capture(lambda: mod.generate(0, 0, typo_axis='silently accepted'))
unknown_summary = {
    'accepted': unknown['accepted'],
    'dimensions': [len(unknown['value']), len(unknown['value'][0])] if unknown['accepted'] else None,
}

representative_overrides = {
    'grid_h': 5, 'grid_w': 5, 'n_seeds': 2,
    'seed_layout': 'scattered', 'edge_avoidance': True,
}
representative_grid = mod.generate(12, 0, **representative_overrides)

n_seed_results = {
    str(value): capture(lambda value=value: count_seeds(mod.generate(
        10 + value, 0, grid_h=5, grid_w=5, n_seeds=value,
        seed_layout='scattered', edge_avoidance=True,
    )))
    for value in (1, 2, 4, 6)
}

width_18 = capture(lambda: [len(row) for row in mod.generate(9, 0, grid_w=18)])
hard_height_4 = capture(lambda: len(mod.generate(9, 0, difficulty='hard', grid_h=4)))

canonical_profiles = set()
import json as _json
for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
    row = _json.loads(line)
    if row.get('task_id') == TASK:
        pairs = list(row.get('train') or [])
        test = row.get('test')
        if isinstance(test, dict): pairs.append(test)
        elif isinstance(test, list): pairs.extend(test)
        for pair in pairs:
            g = pair['input']
            canonical_profiles.add((len(g), len(g[0]), count_seeds(g)))
        break
sample_profiles = []
default_validator_failures = []
for band in ('easy', 'medium', 'hard'):
    for seed in range(100):
        g = mod.generate(1000 + seed, seed, difficulty=band)
        sample_profiles.append((len(g), len(g[0]), count_seeds(g)))
        if hasattr(mod, 'self_check'):
            default_validator_failures.extend(mod.self_check(g))

report = {
    'task_id': TASK,
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'declared_axes': mod.AXES,
    'anchor_corner_identical_cases': sum(anchor_equal),
    'anchor_corner_cases': len(anchor_equal),
    'anchor_corner_validator_failures': anchor_validator_failures,
    'unknown_override': unknown_summary,
    'n_seeds_exact_requests': n_seed_results,
    'representative_exact_control_failure': {
        'seed': 12,
        'sample_index': 0,
        'difficulty': None,
        'overrides': representative_overrides,
        'requested_n_seeds': 2,
        'observed_n_seeds': count_seeds(representative_grid),
        'input': representative_grid,
        'self_check': mod.self_check(representative_grid) if hasattr(mod, 'self_check') else None,
        'in_generator_domain': True,
    },
    'grid_w_18_request': width_18,
    'hard_grid_h_4_request': hard_height_4,
    'canonical_profiles_h_w_seed_count': sorted(canonical_profiles),
    'sampled_default_profile_hits': sum(profile in canonical_profiles for profile in sample_profiles),
    'sampled_default_cases': len(sample_profiles),
    'sampled_default_validator_failures': default_validator_failures,
    'sampled_height_range': [min(p[0] for p in sample_profiles), max(p[0] for p in sample_profiles)],
    'sampled_width_range': [min(p[1] for p in sample_profiles), max(p[1] for p in sample_profiles)],
    'sampled_seed_count_range': [min(p[2] for p in sample_profiles), max(p[2] for p in sample_profiles)],
}
assert report['anchor_corner_identical_cases'] == report['anchor_corner_cases']
assert report['unknown_override']['accepted']
assert not report['n_seeds_exact_requests']['1']['accepted']
assert not report['n_seeds_exact_requests']['6']['accepted']
assert not report['grid_w_18_request']['accepted']
assert not report['hard_grid_h_4_request']['accepted']
assert report['sampled_default_profile_hits'] == 0
assert report['representative_exact_control_failure']['observed_n_seeds'] != 2
assert report['representative_exact_control_failure']['self_check'] == []
assert not report['anchor_corner_validator_failures']
assert not report['sampled_default_validator_failures']
print(json.dumps(report, indent=2, sort_keys=True))
