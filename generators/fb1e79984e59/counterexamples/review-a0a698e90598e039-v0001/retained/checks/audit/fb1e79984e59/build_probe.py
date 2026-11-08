from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
GEN_PATH = PACKET / 'repo/generators/fb1e79984e59/generator.py'
CANONICAL = PACKET / 'repo/shared/data/canonical/puzzles.jsonl'

spec = importlib.util.spec_from_file_location('audit_fb_generator', GEN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def ring_colors(grid: list[list[int]]) -> list[int]:
    h, w = len(grid), len(grid[0])
    return [grid[d][d] for d in range((min(h, w) + 1) // 2)]


def repaint_by_mapping(grid: list[list[int]], mapping: dict[int, int]) -> list[list[int]]:
    return [[mapping.get(value, value) for value in row] for row in grid]


def unique_predecessor(grid: list[list[int]]) -> list[list[int]]:
    unique = list(dict.fromkeys(ring_colors(grid)))
    mapping = {value: unique[(i - 1) % len(unique)] for i, value in enumerate(unique)}
    return repaint_by_mapping(grid, mapping)


def unique_successor(grid: list[list[int]]) -> list[list[int]]:
    unique = list(dict.fromkeys(ring_colors(grid)))
    mapping = {value: unique[(i + 1) % len(unique)] for i, value in enumerate(unique)}
    return repaint_by_mapping(grid, mapping)


def positional_shift(grid: list[list[int]], delta: int) -> list[list[int]]:
    colors = ring_colors(grid)
    h, w = len(grid), len(grid[0])
    return [
        [colors[(min(r, c, h - 1 - r, w - 1 - c) + delta) % len(colors)] for c in range(w)]
        for r in range(h)
    ]


def positional_predecessor(grid: list[list[int]]) -> list[list[int]]:
    return positional_shift(grid, -1)


def positional_successor(grid: list[list[int]]) -> list[list[int]]:
    return positional_shift(grid, 1)


def preserve_zero_predecessor(grid: list[list[int]]) -> list[list[int]]:
    unique = [value for value in dict.fromkeys(ring_colors(grid)) if value != 0]
    if len(unique) < 2:
        return [row[:] for row in grid]
    mapping = {value: unique[(i - 1) % len(unique)] for i, value in enumerate(unique)}
    mapping[0] = 0
    return repaint_by_mapping(grid, mapping)


def sorted_predecessor(grid: list[list[int]]) -> list[list[int]]:
    unique = sorted(set(ring_colors(grid)))
    mapping = {value: unique[(i - 1) % len(unique)] for i, value in enumerate(unique)}
    return repaint_by_mapping(grid, mapping)

RIVALS = {
    'unique_successor': unique_successor,
    'positional_predecessor': positional_predecessor,
    'positional_successor': positional_successor,
    'preserve_zero_predecessor': preserve_zero_predecessor,
    'sorted_predecessor': sorted_predecessor,
}

canonical_pairs = []
for line in CANONICAL.read_text(encoding='utf-8').splitlines():
    row = json.loads(line)
    if row.get('task_id') == 'fb1e79984e59':
        canonical_pairs.extend(row.get('train', []))
        canonical_pairs.extend(row.get('test', []))

canonical = {
    'pair_count': len(canonical_pairs),
    'all_pass_self_check': all(not module.self_check(pair['input']) for pair in canonical_pairs),
    'python_authority_matches': all(unique_predecessor(pair['input']) == pair['output'] for pair in canonical_pairs),
    'rival_fit_counts': {
        name: sum(fn(pair['input']) == pair['output'] for pair in canonical_pairs)
        for name, fn in RIVALS.items()
    },
}

census_records = []
census_hashes = set()
racket_inputs = []
for difficulty in ('easy', 'medium', 'hard'):
    for sample_index in range(100):
        grid = module.generate(20261004, sample_index, difficulty=difficulty)
        observed = module.observe_overrides(grid)
        errs = module.self_check(grid, difficulty=difficulty)
        census_records.append({
            'difficulty': difficulty,
            'seed': 20261004,
            'sample_index': sample_index,
            'self_check': errs,
            'observed': observed,
        })
        census_hashes.add(hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest())
        if sample_index < 20:
            racket_inputs.append(grid)

lesson_cases = []
ambiguous = []
for difficulty in ('easy', 'medium', 'hard'):
    for seed in range(40):
        for start in range(6):
            grids = [module.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
            authority = [unique_predecessor(grid) for grid in grids]
            patterns = [module.observe_overrides(grid)['ring_pattern'] for grid in grids[:3]]
            survivors = []
            bad_survivors = []
            for name, fn in RIVALS.items():
                if all(fn(grids[i]) == authority[i] for i in range(3)):
                    survivors.append(name)
                    if fn(grids[3]) != authority[3]:
                        bad_survivors.append(name)
            case = {
                'difficulty': difficulty,
                'seed': seed,
                'start': start,
                'demo_patterns': patterns,
                'has_all_distinct': 'all_distinct' in patterns,
                'has_repeated_witness': any(p in {'outer_repeat', 'inner_repeat'} for p in patterns),
                'surviving_rivals': survivors,
                'survives_demos_but_differs_query': bad_survivors,
            }
            lesson_cases.append(case)
            if bad_survivors:
                ambiguous.append(case)

# Exact override boundary checks from the retained task contract.
override_cases = [
    {'grid_h': 5, 'grid_w': 18, 'ring_pattern': 'all_distinct', 'include_zero': False},
    {'grid_h': 18, 'grid_w': 5, 'ring_pattern': 'outer_repeat', 'include_zero': True},
    {'grid_h': 5, 'grid_w': 5, 'ring_pattern': 'inner_repeat', 'include_zero': False},
    {'grid_h': 7, 'grid_w': 18, 'ring_pattern': 'alternating', 'include_zero': True},
    {'grid_h': 18, 'grid_w': 7, 'ring_pattern': 'alternating', 'include_zero': False},
]
override_results = []
for difficulty in ('easy', 'medium', 'hard'):
    for index, overrides in enumerate(override_cases):
        grid = module.generate(1500 + index, 7000 + index, difficulty=difficulty, **overrides)
        override_results.append({
            'difficulty': difficulty,
            'overrides': overrides,
            'observed': module.observe_overrides(grid),
            'self_check': module.self_check(grid, difficulty=difficulty),
        })

small_alt_rejected = False
try:
    module.generate(88, 99, difficulty='easy', grid_h=5, grid_w=5, ring_pattern='alternating')
except ValueError:
    small_alt_rejected = True
unknown_axis_rejected = False
try:
    module.generate(88, 99, palette_seed=3)
except ValueError:
    unknown_axis_rejected = True

pre = {
    'schema': 'arcpuzzles-audit-probe-v1',
    'task_id': 'fb1e79984e59',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'canonical': canonical,
    'census': {
        'seed': 20261004,
        'per_band': 100,
        'total': len(census_records),
        'unique_inputs': len(census_hashes),
        'all_pass_self_check': all(not item['self_check'] for item in census_records),
        'pattern_counts': {
            p: sum(item['observed']['ring_pattern'] == p for item in census_records)
            for p in module.RING_PATTERNS
        },
        'include_zero_counts': {
            str(v).lower(): sum(item['observed']['include_zero'] is v for item in census_records)
            for v in (False, True)
        },
    },
    'lesson_probe': {
        'seeds': '0..39',
        'difficulties': ['easy', 'medium', 'hard'],
        'cyclic_schedule_starts': '0..5',
        'demo_count': 3,
        'query_offset': 3,
        'case_count': len(lesson_cases),
        'all_have_all_distinct': all(item['has_all_distinct'] for item in lesson_cases),
        'all_have_repeated_witness': all(item['has_repeated_witness'] for item in lesson_cases),
        'ambiguous_case_count': len(ambiguous),
        'rivals': list(RIVALS),
        'ambiguous_cases': ambiguous,
    },
    'overrides': {
        'case_count': len(override_results),
        'all_exact': all(item['observed'] == item['overrides'] for item in override_results),
        'all_pass_self_check': all(not item['self_check'] for item in override_results),
        'small_alternating_rejected': small_alt_rejected,
        'unknown_axis_rejected': unknown_axis_rejected,
        'results': override_results,
    },
}
(OUT_DIR / 'probe_pre_apply.json').write_text(json.dumps(pre, indent=2) + '\n')
(OUT_DIR / 'generated_inputs.json').write_text(json.dumps(racket_inputs, indent=2) + '\n')
print(json.dumps({
    'generator_sha256': pre['generator_sha256'],
    'canonical': canonical,
    'census': pre['census'],
    'lesson_probe': {k: v for k, v in pre['lesson_probe'].items() if k != 'ambiguous_cases'},
    'overrides': {k: v for k, v in pre['overrides'].items() if k != 'results'},
}, indent=2))
