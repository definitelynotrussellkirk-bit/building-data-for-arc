"""Bounded adversarial connectivity audit; writes only its own evidence directory."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root

HERE = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
SOURCE = ROOT / 'generators/c05faa9b2b85/generator.py'
spec = importlib.util.spec_from_file_location('audited_generator', SOURCE)
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

def rival8(grid):
    out = [row[:] for row in grid]
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 1}
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack, region = [start], []
        while stack:
            r, c = stack.pop()
            region.append((r, c))
            for dr, dc in itertools.product((-1, 0, 1), repeat=2):
                q = (r + dr, c + dc)
                if (dr or dc) and q in unseen:
                    unseen.remove(q)
                    stack.append(q)
        colors = {grid[r][c] for r, c in region if grid[r][c] > 1}
        if len(colors) == 1:
            color = next(iter(colors))
            for r, c in region:
                if grid[r][c] == 0:
                    out[r][c] = color
    return out

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()

pairs = canonical_pairs(g.TASK_ID, root=ROOT)
ledger = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get('task_id') == g.TASK_ID]
rule_sha = hashlib.sha256(ledger[0]['program_solution'].encode()).hexdigest()
canonical = {
    name: {'fits': sum(fn(pair['input']) == pair['output'] for pair in pairs), 'denominator': len(pairs)}
    for name, fn in {**g.CANONICAL_SHORTCUTS, 'eight_connected_regions': rival8}.items()
}
samples = []
for seed in range(20):
    for scene, canvas, rooms in itertools.product(g.SCENE_PROFILES, g.CANVAS_PROFILES, range(2, 5)):
        samples.append((seed, seed, 'hard', {'scene_profile': scene, 'canvas_profile': canvas, 'n_rooms': rooms}))
for band in ('easy', 'medium', 'hard'):
    samples.extend((1000 + i, i, band, {}) for i in range(60))
counts = {'valid': 0, 'nonidentity': 0, 'eight_connected_agrees': 0}
declared_fit = {name: 0 for name in g.LESSON_COMPETITORS}
unique = set()
for seed, index, band, overrides in samples:
    grid = g.generate(seed, index, difficulty=band, **overrides)
    truth = g.rule_mirror(grid)
    counts['valid'] += not g.self_check(grid, meta={'overrides': overrides})
    counts['nonidentity'] += truth != grid
    counts['eight_connected_agrees'] += rival8(grid) == truth
    unique.add(digest(grid))
    for name, fn in g.LESSON_COMPETITORS.items():
        declared_fit[name] += fn(grid) == truth

lessons, lesson_unique = [], set()
for band in ('easy', 'medium', 'hard'):
    for start in range(3):
        grids = [g.generate(2000, start + j, difficulty=band) for j in range(4)]
        lesson_unique.update(map(digest, grids))
        labeled = [{'input': x, 'output': g.rule_mirror(x)} for x in grids]
        rotations = []
        for query_index in range(4):
            demos = [p for j, p in enumerate(labeled) if j != query_index]
            rotations.append({'query_index': query_index,
                'declared_contract_errors': g.lesson_identifiable(demos, labeled[query_index]),
                'eight_connected_fits_all_demos': all(rival8(p['input']) == p['output'] for p in demos)})
        lessons.append({'seed': 2000, 'start': start, 'difficulty': band, 'overrides': {}, 'rotations': rotations})

generated = g.generate(20261008, 1, difficulty='medium', n_rooms=2)
counterfactual = [[0] * 8 for _ in range(7)]
for r in range(1, 6):
    for c in range(1, 7):
        counterfactual[r][c] = 1
counterfactual[2][2], counterfactual[2][3] = 2, 0
counterfactual[3][4], counterfactual[4][4] = 3, 0
witnesses = []
for name, grid, origin in [
    ('emitted_scene', generated, {'seed': 20261008, 'sample_index': 1, 'difficulty': 'medium', 'overrides': {'n_rooms': 2}, 'emitted_support': True}),
    ('diagonal_contact_counterfactual', counterfactual, {'seed': None, 'sample_index': None, 'overrides': None, 'construction': 'Two enclosed 4-connected strips touch only diagonally, at (2,3) and (3,4).', 'emitted_support': False})]:
    witnesses.append({'name': name, **origin, 'self_check': g.self_check(grid), 'strict_canonical_like': g.strict_canonical_like(grid),
        'input': grid, 'intended_output_python_mirror': g.rule_mirror(grid),
        'rival_output': rival8(grid), 'rival_disagrees_python_mirror': rival8(grid) != g.rule_mirror(grid)})
report = {'task_id': g.TASK_ID, 'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'rule_hash': g.RULE_HASH, 'rule_source_sha256': rule_sha, 'canonical': canonical,
    'sample_scan': {'count': len(samples), 'distinct_inputs': len(unique), 'counts': counts, 'declared_rival_fit_counts': declared_fit,
        'sampling': [{'seed_range_inclusive': [0, 19], 'sample_index': 'equals seed', 'difficulty': 'hard', 'overrides': 'Cartesian product of actual SCENE_PROFILES, CANVAS_PROFILES, n_rooms=2..4', 'count': 540},
            {'seed': '1000+i', 'sample_index': 'i=0..59', 'difficulty': ['easy', 'medium', 'hard'], 'overrides': {}, 'count': 180}]},
    'lesson_scan': {'demonstrations': 3, 'production_query_index': 3, 'lesson_count': len(lessons), 'rotation_count': len(lessons) * 4,
        'materialized_input_slots': len(lessons) * 4, 'distinct_inputs': len(lesson_unique), 'rows': lessons}, 'witnesses': witnesses}
(HERE / 'probe.json').write_text(json.dumps(report, indent=2) + '\n')
(HERE / 'input.json').write_text(json.dumps([w['input'] for w in witnesses]) + '\n')
print(json.dumps({k: report[k] for k in ('generator_sha256', 'rule_source_sha256', 'canonical', 'sample_scan')}, indent=2))
